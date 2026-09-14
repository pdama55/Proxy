"""Local annotation tool. Serves one batch to one annotator; never serves key.json or other annotators' labels."""

import datetime as dt
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from proxy.annotation.agreement import LEAK_LABELS
from proxy.scoring.judge import DISCLOSURE_CATEGORIES

STATIC = Path(__file__).parent / "static"
_write_lock = threading.Lock()


def valid_label(item_type: str, label) -> bool:
    if item_type == "disclosure":
        return label in DISCLOSURE_CATEGORIES
    if item_type == "characterization":
        return isinstance(label, int) and not isinstance(label, bool) and 1 <= label <= 7
    if item_type == "leak":
        return label in LEAK_LABELS
    return False


def make_handler(batch_dir: Path, annotator: str):
    items = [json.loads(l) for l in (batch_dir / "items.jsonl").read_text().splitlines() if l.strip()]
    types = {i["item_id"]: i["type"] for i in items}
    labels_path = batch_dir / f"labels_{annotator}.jsonl"

    def own_labels() -> dict:
        out = {}
        if labels_path.exists():
            for line in labels_path.read_text().splitlines():
                if line.strip():
                    rec = json.loads(line)
                    out[rec["item_id"]] = {"label": rec["label"], "note": rec.get("note", "")}
        return out

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _send(self, code, body: bytes, ctype="application/json"):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                return self._send(200, (STATIC / "annotate.html").read_bytes(), "text/html; charset=utf-8")
            if self.path == "/api/items":
                return self._send(200, json.dumps({"annotator": annotator, "items": items}).encode())
            if self.path == "/api/labels":
                return self._send(200, json.dumps(own_labels()).encode())
            self._send(404, b'{"error": "not found"}')

        def do_POST(self):
            if self.path != "/api/label":
                return self._send(404, b'{"error": "not found"}')
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            iid, label = body.get("item_id"), body.get("label")
            if iid not in types or not valid_label(types[iid], label):
                return self._send(400, b'{"error": "invalid item or label"}')
            rec = {"item_id": iid, "label": label, "note": str(body.get("note") or ""), "annotator": annotator,
                   "at": dt.datetime.now(dt.timezone.utc).isoformat()}
            with _write_lock, labels_path.open("a") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            self._send(200, b'{"ok": true}')

    return Handler


def serve(batch_dir: Path, annotator: str, port: int = 8766):
    assert annotator.replace("-", "").replace("_", "").isalnum(), "annotator name must be alphanumeric"
    httpd = ThreadingHTTPServer(("127.0.0.1", port), make_handler(Path(batch_dir), annotator))
    print(f"Annotation tool for {annotator} on http://127.0.0.1:{port}  (Ctrl+C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
