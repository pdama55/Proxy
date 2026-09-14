"""Local, read-only replay viewer over the episode store. No auth, no deployment: binds to 127.0.0.1."""

import json
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from proxy.store import EpisodeStore
from proxy.store.episodes import INDEX_COLUMNS

STATIC = Path(__file__).parent / "static"
FILTERABLE = ["run", "model", "outcome_target", "audit_framing", "agent_role", "briefing_variant", "phrasing", "report_variant", "termination_reason", "counterparty_kind"]
FLAGS = ["flagged", "constraint_violated", "leaked", "leaked_near", "reservation_breached", "violation_unmentioned", "leak_unmentioned", "parse_failures"]
LIST_COLUMNS = ["episode_id", "run", "model", "outcome_target", "audit_framing", "agent_role", "scenario_seed", "termination_reason",
                "turns_used", "agent_gain_fraction", "constraint_violated", "leaked", "violation_unmentioned", "leak_unmentioned",
                "reservation_breached", "parse_failures", "report_chars", "flagged"]


def make_handler(store: EpisodeStore):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _send(self, code: int, body: bytes, ctype: str):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _json(self, obj, code=200):
            self._send(code, json.dumps(obj).encode(), "application/json")

        def do_GET(self):
            url = urlparse(self.path)
            q = {k: v[0] for k, v in parse_qs(url.query).items()}
            if url.path in ("/", "/index.html"):
                return self._send(200, (STATIC / "index.html").read_bytes(), "text/html; charset=utf-8")
            if not store.index_path.exists():
                return self._json({"error": "no index; run `proxy index`"}, 404)
            con = sqlite3.connect(store.index_path)
            con.row_factory = sqlite3.Row
            try:
                if url.path == "/api/facets":
                    return self._json({c: [r[0] for r in con.execute(f"SELECT DISTINCT {c} FROM episodes ORDER BY 1")] for c in FILTERABLE})
                if url.path == "/api/episodes":
                    where, args = [], []
                    for c in FILTERABLE:
                        if q.get(c) not in (None, ""):
                            where.append(f"{c} = ?")
                            args.append(q[c])
                    flag = q.get("flag")
                    if flag in FLAGS:
                        where.append(f"{flag} > 0")
                    sql = f"SELECT {', '.join(LIST_COLUMNS)} FROM episodes"
                    if where:
                        sql += " WHERE " + " AND ".join(where)
                    sql += " ORDER BY run, model, outcome_target, scenario_seed LIMIT 2000"
                    return self._json([dict(r) for r in con.execute(sql, args)])
                if url.path.startswith("/api/episodes/"):
                    eid = url.path.rsplit("/", 1)[-1]
                    row = con.execute("SELECT path FROM episodes WHERE episode_id = ?", (eid,)).fetchone()
                    if row is None:
                        return self._json({"error": "not found"}, 404)
                    return self._send(200, Path(row["path"]).read_bytes(), "application/json")
            finally:
                con.close()
            self._json({"error": "not found"}, 404)

    return Handler


def serve(store: EpisodeStore, port: int = 8765):
    assert set(LIST_COLUMNS) <= set(INDEX_COLUMNS)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), make_handler(store))
    print(f"Replay viewer on http://127.0.0.1:{port}  (Ctrl+C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
