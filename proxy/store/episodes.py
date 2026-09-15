"""One JSON file per episode, plus a SQLite index over the flat fields used for filtering."""

import json
import os
import sqlite3
from collections.abc import Iterator
from pathlib import Path

from proxy import DATA_DIR

INDEX_COLUMNS = {
    "episode_id": "TEXT PRIMARY KEY",
    "run": "TEXT",
    "path": "TEXT",
    "created_at": "TEXT",
    "model": "TEXT",
    "model_versions": "TEXT",
    "outcome_target": "TEXT",
    "audit_framing": "INTEGER",
    "briefing_variant": "TEXT",
    "phrasing": "TEXT",
    "report_variant": "TEXT",
    "agent_role": "TEXT",
    "constraint_set": "TEXT",
    "scenario_seed": "INTEGER",
    "replicate": "INTEGER",
    "counterparty_kind": "TEXT",
    "first_mover": "TEXT",
    "termination_reason": "TEXT",
    "turns_used": "INTEGER",
    "deal": "INTEGER",
    "agent_utility": "REAL",
    "agent_gain_fraction": "REAL",
    "beat_batna": "INTEGER",
    "parse_failures": "INTEGER",
    "cost_usd": "REAL",
    "report_chars": "INTEGER",
    "scoring_version": "TEXT",
    "constraint_violated": "INTEGER",
    "leaked": "INTEGER",
    "leaked_near": "INTEGER",
    "reservation_breached": "INTEGER",
    "should_have_walked": "INTEGER",
    "violation_unmentioned": "INTEGER",
    "leak_unmentioned": "INTEGER",
    "flagged": "INTEGER",
}


def _flat(rec: dict, path: Path) -> dict:
    spec, cond = rec["spec"], rec["condition"]
    out, det = rec.get("outcomes") or {}, rec.get("detectors") or {}
    disc = (rec.get("scores") or {}).get("disclosure_stage1") or {}
    b = lambda v: None if v is None else int(bool(v))
    return {
        "episode_id": rec["episode_id"],
        "run": rec.get("run"),
        "path": str(path),
        "created_at": rec.get("created_at"),
        "model": spec["model"],
        "model_versions": ",".join(rec["agent"].get("model_versions") or []),
        "outcome_target": spec["outcome_target"],
        "audit_framing": int(spec["audit_framing"]),
        "briefing_variant": spec["briefing_variant"],
        "phrasing": spec["phrasing"],
        "report_variant": spec["report_variant"],
        "agent_role": spec["agent_role"],
        "constraint_set": "+".join(spec["constraint_set"]),
        "scenario_seed": spec["scenario_seed"],
        "replicate": spec["replicate"],
        "counterparty_kind": spec["counterparty_kind"],
        "first_mover": cond.get("first_mover"),
        "termination_reason": rec["termination"]["reason"],
        "turns_used": rec["termination"]["turns_used"],
        "deal": b(out.get("deal")),
        "agent_utility": out.get("agent_utility"),
        "agent_gain_fraction": out.get("agent_gain_fraction"),
        "beat_batna": b(out.get("beat_batna")),
        "parse_failures": rec["stats"]["agent_parse_failures"],
        "cost_usd": rec["stats"]["cost_usd"],
        "report_chars": len((rec.get("report") or {}).get("text") or ""),
        "scoring_version": (rec.get("scores") or {}).get("scoring_version"),
        "constraint_violated": b(det.get("constraint_violated")),
        "leaked": b(det.get("leaked")),
        "leaked_near": b(det.get("leaked_near")),
        "reservation_breached": b(det.get("reservation_breached")),
        "should_have_walked": b(det.get("should_have_walked")),
        "violation_unmentioned": b(disc.get("any_violation_unmentioned")),
        "leak_unmentioned": b(disc.get("any_leak_unmentioned")),
        "flagged": b(det.get("flagged")),
    }


class EpisodeStore:
    def __init__(self, root: Path | str = DATA_DIR):
        self.root = Path(root)
        self.runs_dir = self.root / "runs"
        self.index_path = self.root / "index.sqlite"

    def path(self, run: str, episode_id: str) -> Path:
        return self.runs_dir / run / "episodes" / f"{episode_id}.json"

    def exists(self, run: str, episode_id: str) -> bool:
        return self.path(run, episode_id).exists()

    def write(self, rec: dict) -> Path:
        path = self.path(rec["run"], rec["episode_id"])
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(rec, indent=1, ensure_ascii=False))
        os.replace(tmp, path)
        self.upsert_index(rec, path)
        return path

    @staticmethod
    def load(path: Path | str) -> dict:
        return json.loads(Path(path).read_text())

    def iter_paths(self, run: str | None = None) -> Iterator[Path]:
        base = self.runs_dir / run if run else self.runs_dir
        # Runs whose directory starts with "_" (e.g. _superseded) are set aside and never indexed.
        yield from sorted(p for p in base.glob("**/episodes/*.json") if not any(part.startswith("_") for part in p.relative_to(self.runs_dir).parts))

    def iter(self, run: str | None = None) -> Iterator[tuple[Path, dict]]:
        for p in self.iter_paths(run):
            yield p, self.load(p)

    def find(self, episode_id: str) -> Path | None:
        hits = list(self.runs_dir.glob(f"*/episodes/{episode_id}.json"))
        return hits[0] if hits else None

    # ---- index --------------------------------------------------------------
    def connect(self) -> sqlite3.Connection:
        self.root.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(self.index_path)
        cols = ", ".join(f"{k} {v}" for k, v in INDEX_COLUMNS.items())
        con.execute(f"CREATE TABLE IF NOT EXISTS episodes ({cols})")
        return con

    def upsert_index(self, rec: dict, path: Path) -> None:
        row = _flat(rec, path)
        with self.connect() as con:
            keys = list(row)
            con.execute(
                f"INSERT OR REPLACE INTO episodes ({', '.join(keys)}) VALUES ({', '.join('?' for _ in keys)})",
                [row[k] for k in keys],
            )

    def rebuild_index(self) -> int:
        if self.index_path.exists():
            self.index_path.unlink()
        n = 0
        for p, rec in self.iter():
            self.upsert_index(rec, p)
            n += 1
        return n
