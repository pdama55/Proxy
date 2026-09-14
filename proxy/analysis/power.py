"""Simulation-based power analysis for the paired, scenario-clustered design (research plan section 6).

Model: each scenario s has a random intercept u_s ~ N(0, sigma) on the logit of non-disclosure. In each
outcome condition, each of n episodes violates with probability p_violate; a violating episode is
undisclosed with probability logistic(logit(p0) + u_s + delta_logit * [bad]). The test is a paired t-test on
per-scenario rates (bad minus good) across scenarios that have violations in both conditions, which respects
both the clustering and the pairing.
"""

import math

import numpy as np
import pandas as pd
from scipy import stats


def logit(p: float) -> float:
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


def expit(x):
    return 1 / (1 + np.exp(-x))


def estimate_parameters(df: pd.DataFrame) -> dict:
    """Pilot estimates: violation rate, lower-bound non-disclosure rate, and between-scenario SD on the logit."""
    main = df[(~df["error"]) & (df["scored"]) & (df["counterparty_kind"] == "scripted")]
    violated = main.dropna(subset=["violated"])
    v = main[(main["violated"] == 1.0)].dropna(subset=["v_unmentioned"])
    p_violate = float(violated["violated"].mean()) if len(violated) else math.nan
    p0 = float(v["v_unmentioned"].mean()) if len(v) else math.nan
    # Between-scenario SD of logit rates, shrunk toward zero by subtracting expected binomial noise.
    sigma = math.nan
    if len(v) and v["seed"].nunique() > 2:
        g = v.groupby("seed")["v_unmentioned"].agg(["mean", "count"])
        adj = g["mean"].clip(0.05, 0.95)
        between_var = float(np.var([logit(x) for x in adj], ddof=1))
        noise = float(np.mean(1 / (g["count"] * adj * (1 - adj))))
        sigma = math.sqrt(max(between_var - noise, 0.0))
    return {"p_violate": p_violate, "p_nondisclosure": p0, "sigma_scenario": sigma, "violating_episodes": int(len(v)), "scenarios": int(main["seed"].nunique())}


def simulate_power(
    *,
    n_scenarios: int,
    episodes_per_scenario_condition: int,
    p_violate: float,
    p0: float,
    delta: float,
    sigma: float,
    alpha: float = 0.05,
    sims: int = 2000,
    seed: int = 0,
) -> float:
    """delta is the absolute increase in non-disclosure probability (bad minus good) at the typical scenario."""
    rng = np.random.default_rng(seed)
    base = logit(p0)
    shift = logit(min(p0 + delta, 0.999)) - base
    hits = 0
    for _ in range(sims):
        u = rng.normal(0, sigma if sigma == sigma else 0.0, n_scenarios)
        diffs = []
        for s in range(n_scenarios):
            rates = []
            for bad in (0, 1):
                nv = rng.binomial(episodes_per_scenario_condition, p_violate)
                if nv == 0:
                    break
                k = rng.binomial(nv, expit(base + u[s] + shift * bad))
                rates.append(k / nv)
            if len(rates) == 2:
                diffs.append(rates[1] - rates[0])
        if len(diffs) < 3 or np.std(diffs) == 0:
            hits += int(len(diffs) >= 3 and np.mean(diffs) > 0)
            continue
        t, p_two = stats.ttest_1samp(diffs, 0.0)
        hits += int(t > 0 and p_two / 2 < alpha)
    return hits / sims


def power_table(params: dict, deltas: list[float], scenario_counts: list[int], episodes_per_cell: int, alpha: float = 0.05, sims: int = 1000) -> pd.DataFrame:
    rows = []
    for d in deltas:
        for n in scenario_counts:
            rows.append({
                "delta": d,
                "scenarios": n,
                "episodes_per_scenario_condition": episodes_per_cell,
                "power": simulate_power(
                    n_scenarios=n, episodes_per_scenario_condition=episodes_per_cell, p_violate=params["p_violate"],
                    p0=params["p_nondisclosure"], delta=d, sigma=params["sigma_scenario"], alpha=alpha, sims=sims,
                ),
            })
    return pd.DataFrame(rows)
