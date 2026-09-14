"""Calibrates scripted counterparty parameters against the rule-based reference agent. No model calls.

Prints, per outcome target, the distribution of termination reasons and agent_gain_fraction, so the
parameter sets in an experiment config can be checked to land their intended bands before any spend.
"""

import asyncio
import statistics as st
from collections import Counter

from proxy.config import ExperimentConfig
from proxy.counterparty.reference import ReferenceAgent
from proxy.runner.episode import run_episode


def _q(vals: list[float], p: float) -> float:
    s = sorted(vals)
    return s[min(len(s) - 1, int(p * len(s)))]


async def calibrate(
    cfg: ExperimentConfig,
    reference_exponents: tuple[float, ...] = (0.5, 1.0, 2.0),
    extra_seeds: int = 20,
) -> dict:
    """Two reference agents per target: one that always respects its floor constraints and one that
    ignores them. The gap between them shows how much of each band depends on violating."""
    specs = [s for s in cfg.episode_specs() if s.model == cfg.models[0] and not s.audit_framing and s.replicate == 0]
    specs = [s for s in specs if s.briefing_variant == cfg.briefing_variants[0] and s.phrasing == cfg.phrasings[0] and s.report_variant == cfg.report_variants[0]]
    # Calibrate on more scenarios than the config itself uses, so bands are not tuned to a handful of seeds.
    base_seed = max(cfg.scenario_seeds) + 10_000
    specs += [
        s.model_copy(update={"scenario_seed": base_seed + i})
        for i in range(extra_seeds)
        for s in specs
        if s.scenario_seed == cfg.scenario_seeds[0]
    ]
    results: dict = {}
    for target in cfg.outcome_targets:
        for respect in (True, False):
            rows = []
            for e in reference_exponents:
                for s in (s for s in specs if s.outcome_target == target):
                    agent = ReferenceAgent(concession_exponent=e, respect_constraints=respect)
                    rows.append(await run_episode(s, {}, None, agent_override=agent, debug_isolation=True))
            results[(target, "compliant" if respect else "unconstrained")] = _summarize(cfg, target, rows)
    return results


def _summarize(cfg: ExperimentConfig, target: str, rows: list[dict]) -> dict:
    reasons = Counter(r["termination"]["reason"] for r in rows)
    gains = [r["outcomes"]["agent_gain_fraction"] for r in rows if r["outcomes"]["deal"]]
    deals = [r for r in rows if r["outcomes"]["deal"]]
    violating = [
        r for r in deals
        if any(c["type"] == "floor" and r["termination"]["final_package"][c["issue"]] not in c["allowed"] for c in r["briefing"]["constraints"])
    ]
    return {
        "params": cfg.counterparty.scripted[target],
        "episodes": len(rows),
        "reasons": dict(reasons),
        "deal_rate": len(deals) / len(rows),
        "violation_rate_among_deals": len(violating) / len(deals) if deals else None,
        "gain_mean": st.mean(gains) if gains else None,
        "gain_p10": _q(gains, 0.1) if gains else None,
        "gain_p90": _q(gains, 0.9) if gains else None,
    }


def run_calibration(cfg: ExperimentConfig) -> dict:
    return asyncio.run(calibrate(cfg))
