"""Correcting a judged rate for judge error, using the human validation labels.

A judged rate is not the quantity of interest: it is the quantity of interest seen through an imperfect
instrument. With sensitivity q1 = P(judge says non-disclosure | human says non-disclosure) and specificity
q0 = P(judge says disclosure | human says disclosure), the observed rate p relates to the true rate t by
p = t*q1 + (1-t)*(1-q0), which inverts to the Rogan-Gladen estimator

    t = (p + q0 - 1) / (q0 + q1 - 1).

Two things make a naive application of this misleading here, and both are handled below.

1. The validation items were drawn stratified on whether the report mentions any other offer, which is far
   from the population mix. Sensitivity and specificity are therefore estimated within stratum and the
   corrected rate is recombined at the population stratum shares.
2. Disclosure is rare, so the validation set contains very few items a human called "disclosed". Specificity
   is the weakly identified parameter, and a point estimate of 1.0 from a handful of negatives would claim a
   precision the data do not support. `sensitivity_curve` therefore reports the corrected rate across the
   whole credible range of q0 rather than at its point estimate alone.
"""

import json
import math
from pathlib import Path

from proxy.annotation.agreement import load_labels
from proxy.store import EpisodeStore

# Jeffreys interval: a Beta(1/2, 1/2) prior, which stays sensible when a cell is empty or saturated.
JEFFREYS = 0.5


def _jeffreys_interval(successes: int, n: int, level: float = 0.95) -> tuple[float, float]:
    """Equal-tailed Beta posterior interval. Returns (nan, nan) when there is nothing to estimate from."""
    if n <= 0:
        return (math.nan, math.nan)
    try:
        from scipy.stats import beta
    except ImportError:
        p = successes / n
        se = math.sqrt(max(p * (1 - p), 1e-9) / n)
        return (max(0.0, p - 1.96 * se), min(1.0, p + 1.96 * se))
    a, b = successes + JEFFREYS, n - successes + JEFFREYS
    lo = 0.0 if successes == 0 else float(beta.ppf((1 - level) / 2, a, b))
    hi = 1.0 if successes == n else float(beta.ppf(1 - (1 - level) / 2, a, b))
    return (lo, hi)


def rogan_gladen(p: float, q1: float, q0: float) -> float:
    """Corrected rate, clipped to [0, 1]. Undefined when the judge is no better than chance (q0 + q1 <= 1)."""
    denom = q0 + q1 - 1
    if denom <= 0:
        return math.nan
    return min(1.0, max(0.0, (p + q0 - 1) / denom))


def confusion(batch_dirs: list[Path], store: EpisodeStore, judge: str, constraint_kind: str = "alt") -> dict:
    """Judge vs human on items both annotators placed on the same side of the binary decision.

    Positive = the report did NOT convey the blocked better deal. Returns per-stratum cells; the stratum is
    whether the report mentions any other offer at all, the axis the validation set was stratified on and the
    one on which the judge's job differs most.
    """
    cells: dict[str, dict[str, int]] = {}
    for batch_dir in batch_dirs:
        batch_dir = Path(batch_dir)
        if not (batch_dir / "key.json").exists():
            continue
        key = json.loads((batch_dir / "key.json").read_text())
        labels = load_labels(batch_dir)
        annotators = sorted(labels)
        if not annotators:
            continue
        for item, meta in key.items():
            if meta["type"] != "disclosure" or meta["stratum"][1] != constraint_kind:
                continue
            vals = [labels[a][item] for a in annotators if item in labels[a]]
            if len(vals) != len(annotators):
                continue
            human = {v != "acknowledged" for v in vals}
            if len(human) != 1:  # annotators disagree on the binary decision; excluded, and counted below
                cells.setdefault(meta["stratum"][2], {}).setdefault("human_split", 0)
                cells[meta["stratum"][2]]["human_split"] += 1
                continue
            path = store.find(meta["episode_id"])
            if path is None:
                continue
            scores = store.load(path).get("scores") or {}
            cat = ((scores.get("disclosure_stage2") or {}).get("by_judge") or {}).get(judge, {}).get(
                meta["constraint_id"], {}
            ).get("category")
            if cat is None:
                s1 = ((scores.get("disclosure_stage1") or {}).get("per_constraint") or {}).get(meta["constraint_id"], {})
                if s1.get("applicable") and not s1.get("mentioned"):
                    cat = "absent"
            if cat is None:
                continue
            c = cells.setdefault(meta["stratum"][2], {})
            h, j = human.pop(), cat != "acknowledged"
            c[("tp" if j else "fn") if h else ("fp" if j else "tn")] = c.get(("tp" if j else "fn") if h else ("fp" if j else "tn"), 0) + 1
    for c in cells.values():
        for k in ("tp", "fn", "fp", "tn", "human_split"):
            c.setdefault(k, 0)
    return cells


def _rates(cell: dict) -> dict:
    pos, neg = cell["tp"] + cell["fn"], cell["tn"] + cell["fp"]
    return {
        "n": pos + neg,
        "positives": pos,
        "negatives": neg,
        "sensitivity": cell["tp"] / pos if pos else math.nan,
        "sensitivity_ci": _jeffreys_interval(cell["tp"], pos),
        "specificity": cell["tn"] / neg if neg else math.nan,
        "specificity_ci": _jeffreys_interval(cell["tn"], neg),
        **{k: cell[k] for k in ("tp", "fn", "fp", "tn")},
    }


def debias(cells: dict, observed_by_stratum: dict[str, float], stratum_share: dict[str, float]) -> dict:
    """Stratified Rogan-Gladen. `observed_by_stratum` and `stratum_share` come from the full analysis sample."""
    per: dict[str, dict] = {}
    total = 0.0
    weight_used = 0.0
    for stratum, share in stratum_share.items():
        cell = cells.get(stratum)
        p = observed_by_stratum.get(stratum)
        if cell is None or p is None:
            continue
        r = _rates(cell)
        q1 = r["sensitivity"] if r["positives"] else 1.0
        q0 = r["specificity"] if r["negatives"] else 1.0
        corrected = rogan_gladen(p, q1, q0)
        per[stratum] = {**r, "observed": p, "share": share, "corrected": corrected,
                        "assumed_q1_when_unestimated": not r["positives"],
                        "assumed_q0_when_unestimated": not r["negatives"]}
        if not math.isnan(corrected):
            total += share * corrected
            weight_used += share
    return {"per_stratum": per, "corrected_overall": total / weight_used if weight_used else math.nan,
            "weight_covered": weight_used}


def sensitivity_curve(cells: dict, observed_by_stratum: dict[str, float], stratum_share: dict[str, float],
                      grid: tuple[float, ...] = (1.0, 0.95, 0.9, 0.8, 0.7, 0.6, 0.5)) -> list[dict]:
    """Corrected overall rate as a function of an assumed specificity, held common across strata.

    Specificity is the parameter the validation set identifies weakly, because reports that convey the
    blocked deal are rare. Rather than quote one corrected number, this shows what the correction would give
    across the range of specificities the validation data leave open.
    """
    out = []
    for q0 in grid:
        total = weight = 0.0
        for stratum, share in stratum_share.items():
            cell, p = cells.get(stratum), observed_by_stratum.get(stratum)
            if cell is None or p is None:
                continue
            r = _rates(cell)
            q1 = r["sensitivity"] if r["positives"] else 1.0
            c = rogan_gladen(p, q1, q0)
            if not math.isnan(c):
                total += share * c
                weight += share
        out.append({"assumed_specificity": q0, "corrected": total / weight if weight else math.nan})
    return out


__all__ = ["confusion", "debias", "sensitivity_curve", "rogan_gladen"]
