"""Scoring pass: reads persisted episodes, writes detectors and scores back. Idempotent and rerunnable."""

from proxy.scoring.detectors import DETECTORS_VERSION, disclosure_stage1, run_detectors
from proxy.store import EpisodeStore

SCORING_VERSION = f"scoring-v2+{DETECTORS_VERSION}"


def score_episode(ep: dict) -> dict:
    if ep["termination"]["reason"] == "error":
        ep["detectors"] = {"skipped": "error episode"}
        ep["scores"] = {"scoring_version": SCORING_VERSION, "excluded": True}
        return ep
    det = run_detectors(ep)
    ep["detectors"] = det
    # Keep judge and principal-simulation outputs; they are versioned by their own prompt hashes.
    ep["scores"] = {
        **(ep.get("scores") or {}),
        "scoring_version": SCORING_VERSION,
        "excluded": False,
        "disclosure_stage1": disclosure_stage1(ep, det),
    }
    return ep


def score_store(store: EpisodeStore, run: str | None = None, force: bool = False) -> tuple[int, int]:
    scored = skipped = 0
    for path, ep in store.iter(run):
        if not force and (ep.get("scores") or {}).get("scoring_version") == SCORING_VERSION:
            skipped += 1
            continue
        store.write(score_episode(ep))
        scored += 1
    return scored, skipped
