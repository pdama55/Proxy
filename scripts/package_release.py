"""Packages the episode corpus and annotation labels for archival deposit (Zenodo, OSF, or a GitHub release).

    python scripts/package_release.py [--out DIR] [--version v1]

Writes DIR/proxy-episodes-<version>.tar.gz containing data/runs/** (every episode JSON, pilots and superseded
runs included, so the compute figures in the paper can be recomputed), data/annotations/** (items, keys,
per-annotator labels and agreement reports), a MANIFEST.json with a SHA-256 per file, and the datasheet and
licence scope. Nothing is modified in place. The SQLite index is not shipped; `proxy index` rebuilds it.
"""

import argparse
import hashlib
import io
import json
import subprocess
import sys
import tarfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = [ROOT / "docs" / "DATASHEET.md", ROOT / "LICENSE-SCOPE.md", ROOT / "LICENSE", ROOT / "docs" / "annotation_guidelines.md"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "release"))
    ap.add_argument("--version", default="v1")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    files: list[tuple[Path, str]] = []  # (source, archive name)
    for p in sorted((DATA / "runs").rglob("*")):
        if p.is_file() and p.suffix == ".json" and p.parent.name == "episodes":
            files.append((p, str(p.resolve().relative_to(DATA.resolve()))))
    for p in sorted((DATA / "runs").rglob("pilot_review.md")):
        files.append((p, str(p.resolve().relative_to(DATA.resolve()))))
    for p in sorted((DATA / "annotations").rglob("*")):
        if p.is_file():
            files.append((p, str(p.resolve().relative_to(DATA.resolve()))))
    for p in DOCS:
        if p.exists():
            files.append((p, p.name))

    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    runs: dict[str, int] = {}
    for _, name in files:
        if name.startswith("runs/") and name.endswith(".json"):
            runs[name.split("/")[1]] = runs.get(name.split("/")[1], 0) + 1
    manifest = {
        "name": f"proxy-episodes-{args.version}",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "harness_commit": commit,
        "episodes_by_run": runs,
        "episodes_total": sum(runs.values()),
        "files": {name: sha256(src) for src, name in files},
        "note": "Episode JSONs are self-contained; `python -m proxy index` rebuilds the SQLite index and "
                "`python -m proxy analyze all configs/analysis.yaml` regenerates every result. Model-generated "
                "text is subject to the generating provider's terms; see DATASHEET.md and LICENSE-SCOPE.md.",
    }
    tar_path = out / f"{manifest['name']}.tar.gz"
    with tarfile.open(tar_path, "w:gz", compresslevel=6) as tar:
        for src, name in files:
            tar.add(src, arcname=f"{manifest['name']}/{name}")
        blob = json.dumps(manifest, indent=1).encode()
        info = tarfile.TarInfo(f"{manifest['name']}/MANIFEST.json")
        info.size, info.mtime = len(blob), int(time.time())
        tar.addfile(info, io.BytesIO(blob))
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=1))
    (out / f"{manifest['name']}.tar.gz.sha256").write_text(f"{sha256(tar_path)}  {tar_path.name}\n")
    print(f"{tar_path}  {tar_path.stat().st_size / 1e6:.1f} MB  {manifest['episodes_total']} episodes in {len(runs)} runs")
    print(json.dumps(runs, indent=1))


if __name__ == "__main__":
    sys.exit(main())
