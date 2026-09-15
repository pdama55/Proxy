"""Flattens the episode store into one analysis row per episode."""

import math

import pandas as pd

from proxy.config import ModelSpec
from proxy.scoring.judge import final_disclosure
from proxy.store import EpisodeStore

NaN = math.nan


def _b(v):
    return NaN if v is None else float(bool(v))


def episode_row(ep: dict, models: dict[str, ModelSpec], primary_judge: str, principal_model: str | None) -> dict:
    spec, term = ep["spec"], ep["termination"]
    m = models.get(spec["model"])
    scores = ep.get("scores") or {}
    det = ep.get("detectors") or {}
    out = ep.get("outcomes") or {}
    row = {
        "episode_id": ep["episode_id"],
        "run": ep.get("run"),
        "model": spec["model"],
        "family": m.family if m else None,
        "tier": m.tier if m else None,
        "capability_rank": m.capability_rank if m else None,
        "open_weight": bool(m.open_weight) if m else None,
        "model_versions": ",".join(ep["agent"].get("model_versions") or []),
        "outcome_target": spec["outcome_target"],
        "audit": int(spec["audit_framing"]),
        "role": spec["agent_role"],
        "seed": spec["scenario_seed"],
        "replicate": spec["replicate"],
        "briefing_variant": spec["briefing_variant"],
        "phrasing": spec["phrasing"],
        "report_variant": spec["report_variant"],
        "counterparty_kind": spec["counterparty_kind"],
        "reason": term["reason"],
        "error": term["reason"] == "error",
        "turns": term["turns_used"],
        "agent_turns": sum(1 for a in ep["actions"] if a["actor"] == "agent"),
        "parse_failures": ep["stats"]["agent_parse_failures"],
        "report_chars": len((ep.get("report") or {}).get("text") or ""),
        "scored": scores.get("excluded") is False,
        "deal": _b(out.get("deal")),
        "agent_utility": out.get("agent_utility", NaN),
        "gain_fraction": out.get("agent_gain_fraction") if out.get("agent_gain_fraction") is not None else NaN,
        "beat_batna": _b(out.get("beat_batna")),
        "violated": _b(det.get("constraint_violated")),
        "leaked": _b(det.get("leaked")),
        "leaked_near": _b(det.get("leaked_near")),
        "reservation_breached": _b(det.get("reservation_breached")),
        "blocked_alt": _b(det.get("blocked_alternative_exists")),
        "points_forgone": (det.get("blocked_alternative") or {}).get("points_forgone", NaN),
        "forgone_compliant": _b(det.get("forgone_compliant_exists")),
        "total_stated": _b((det.get("stated_total") or {}).get("stated")) if (det.get("stated_total") or {}).get("applicable") else NaN,
        "total_error": (det.get("stated_total") or {}).get("error", NaN),
        "total_misstated": _b((det.get("stated_total") or {}).get("misstated")) if (det.get("stated_total") or {}).get("stated") else NaN,
        "floor_issue": next((c["issue"] for c in ep["briefing"]["constraints"] if c["type"] == "floor"), None),
        "has_secret": any(c["type"] == "secrecy" for c in ep["briefing"]["constraints"]),
    }

    s1 = (scores.get("disclosure_stage1") or {}).get("per_constraint", {})
    final = final_disclosure(ep, primary_judge) if s1 else {}
    for prefix, ctype, applicable_col in (("a", "alt", "blocked_alt"), ("v", "floor", "violated"), ("l", "secrecy", "leaked")):
        cids = [cid for cid in s1 if cid.startswith(ctype + ":") and s1[cid]["applicable"]]
        if row[applicable_col] == 1.0 and cids:
            unmentioned = any(s1[c]["unmentioned"] for c in cids)
            cats = [final[c]["category"] for c in cids]
            disclosed = [final[c]["disclosed"] for c in cids]
            row[f"{prefix}_unmentioned"] = float(unmentioned)
            row[f"{prefix}_category"] = cats[0] if len(cats) == 1 else "|".join(cats)
            # Judged non-disclosure: mechanical non-mention, or the judge found no acknowledgment.
            row[f"{prefix}_nondisclosed"] = NaN if any(d is None for d in disclosed) else float(not all(disclosed))
        else:
            row[f"{prefix}_unmentioned"] = NaN
            row[f"{prefix}_category"] = None
            row[f"{prefix}_nondisclosed"] = NaN

    char = ((scores.get("characterization") or {}).get("by_judge") or {})
    row["char_rating"] = char.get(primary_judge, {}).get("rating", NaN)
    row["total_inflated"] = NaN if math.isnan(row["total_error"]) else float(row["total_error"] > 0)
    for j, v in char.items():
        row[f"char_rating__{j}"] = v.get("rating", NaN)

    sim = ((scores.get("principal_sim") or {}).get("by_model") or {}).get(principal_model or "", {})
    row["principal_report_rating"] = (sim.get("report_only") or {}).get("rating", NaN)
    row["principal_truth_rating"] = (sim.get("ground_truth") or {}).get("rating", NaN)
    row["principal_rating_gap"] = sim.get("rating_gap", NaN)
    row["principal_decision_mismatch"] = _b(sim.get("decision_mismatch"))
    row["principal_missed_intervention"] = _b(sim.get("missed_intervention"))
    return row


def load_frame(store: EpisodeStore, models: dict[str, ModelSpec], *, runs: list[str] | None, primary_judge: str, principal_model: str | None) -> pd.DataFrame:
    rows = []
    for run in runs or [None]:
        for _, ep in store.iter(run):
            rows.append(episode_row(ep, models, primary_judge, principal_model))
    return pd.DataFrame(rows)
