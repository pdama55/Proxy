"""Exports a blinded, stratified annotation batch.

Annotators see only items.jsonl: an opaque item id, the report or messages, and (for disclosure) the one
fact needed to judge it. Model, condition, episode id, detector output and judge output are never in an
item. key.json maps item ids back to episodes and records each item's stratum; the annotation tool never
serves it.
"""

import json
import random
from collections import defaultdict
from pathlib import Path

from proxy.scoring.judge import disclosure_fact
from proxy.store import EpisodeStore
from proxy.util import sha256

ITEM_TYPES = ("disclosure", "characterization", "leak", "stated_total")
GUIDELINES = Path(__file__).resolve().parents[2] / "docs" / "annotation_guidelines.md"


def stratified_sample(cands: list[dict], stratum, n: int, rng: random.Random) -> list[dict]:
    """Round-robin across strata (each shuffled), so small strata are fully represented before large
    ones dominate. Each item's stratum is recorded, so population estimates can be reweighted."""
    groups = defaultdict(list)
    for c in cands:
        groups[stratum(c)].append(c)
    keys = sorted(groups, key=str)
    for k in keys:
        rng.shuffle(groups[k])
    out = []
    while len(out) < n and any(groups[k] for k in keys):
        for k in keys:
            if groups[k] and len(out) < n:
                out.append(groups[k].pop())
    return out


def _item_id(batch: str, *parts) -> str:
    return sha256("|".join(map(str, (batch, *parts))))[:12]


def build_batch(
    store: EpisodeStore,
    batch_name: str,
    out_dir: Path,
    *,
    runs: list[str] | None = None,
    n_disclosure: int = 150,
    n_characterization: int = 150,
    n_leak: int = 100,
    n_stated_total: int = 100,
    seed: int = 0,
) -> dict:
    rng = random.Random(seed)
    disclosure, characterization, leak, stated_total = [], [], [], []
    for _, ep in store.iter():
        if runs and ep.get("run") not in runs:
            continue
        scores = ep.get("scores") or {}
        if ep["termination"]["reason"] == "error" or scores.get("excluded") is not False:
            continue
        # Candidates hold only the item payload, not the episode, so large stores fit in memory.
        base = {"episode_id": ep["episode_id"], "run": ep.get("run")}
        report = (ep.get("report") or {}).get("text") or ""
        target = ep["spec"]["outcome_target"]
        for cid, s1 in (scores.get("disclosure_stage1") or {}).get("per_constraint", {}).items():
            if s1["applicable"] and report:
                disclosure.append({**base, "cid": cid, "stratum": (target, cid.split(":")[0], "mentioned" if s1["mentioned"] else "unmentioned"),
                                   "payload": {"fact": disclosure_fact(ep, cid), "report": report}})
        if report:
            characterization.append({**base, "stratum": (target, ep["spec"]["model"]), "payload": {"report": report}})
        st = (ep.get("detectors") or {}).get("stated_total") or {}
        if report and st.get("applicable"):
            # The extractor's value goes in the key, never in the item, so annotators stay blind to it.
            stated_total.append({**base, "stratum": ("stated" if st.get("stated") else "not_stated", ep["spec"]["model"]),
                                 "extracted": st.get("stated_points"), "payload": {"report": report}})
        for cid, d in (ep.get("detectors") or {}).get("constraints", {}).items():
            if d["type"] == "secrecy":
                con = next(x for x in ep["briefing"]["constraints"] if x["constraint_id"] == cid)
                what = "approved budget ceiling" if con["secret_kind"] == "budget_ceiling" else "internal cost floor"
                messages = [a["message"] for a in ep["actions"] if a["actor"] == "agent" and a["message"]]
                det = "exact" if d["leaked"] else "near" if d["leaked_near"] else "none"
                leak.append({**base, "cid": cid, "stratum": (det,),
                             "payload": {"secret": f"${con['secret_value']:,}", "secret_description": f"the client's {what}", "messages": messages}})

    items, key = [], {}
    for item_type, cands, n in (
        ("disclosure", disclosure, n_disclosure),
        ("characterization", characterization, n_characterization),
        ("leak", leak, n_leak),
        ("stated_total", stated_total, n_stated_total),
    ):
        for c in stratified_sample(cands, lambda c: c["stratum"], n, rng):
            cid = c.get("cid")
            iid = _item_id(batch_name, item_type, c["episode_id"], cid or "")
            items.append({"item_id": iid, "type": item_type, **c["payload"]})
            key[iid] = {"type": item_type, "episode_id": c["episode_id"], "run": c["run"], "constraint_id": cid, "stratum": list(c["stratum"])}
            if item_type == "stated_total":
                key[iid]["extracted"] = c["extracted"]

    rng.shuffle(items)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "items.jsonl").write_text("".join(json.dumps(i, ensure_ascii=False) + "\n" for i in items))
    (out_dir / "key.json").write_text(json.dumps(key, indent=1))
    manifest = {
        "batch": batch_name,
        "seed": seed,
        "runs": runs,
        "requested": {"disclosure": n_disclosure, "characterization": n_characterization, "leak": n_leak, "stated_total": n_stated_total},
        "sampled": {t: sum(1 for i in items if i["type"] == t) for t in ITEM_TYPES},
        "available": {"disclosure": len(disclosure), "characterization": len(characterization), "leak": len(leak), "stated_total": len(stated_total)},
        "guidelines_sha256": sha256(GUIDELINES.read_text()) if GUIDELINES.exists() else None,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=1))
    return manifest
