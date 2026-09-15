"""Sample-size planning for the confirmatory grid, by simulation of the actual design.

Each claim the paper makes is simulated with pilot-based parameters and a scenario random effect on the
logit scale, analysed the way the preregistration says (per-scenario paired differences, or a
cluster-bootstrap-style interval), and summarised as power or interval half-width against the number of
scenario seeds S. Episodes per model per scenario: 2 targets x 2 audit conditions x 2 roles = 8.
"""

import math

import numpy as np
import pandas as pd
from scipy import stats

EPISODES_PER_CELL = 2  # roles, within each (target, audit) cell of a scenario


def _expit(x):
    return 1 / (1 + np.exp(-x))


def _logit(p):
    p = min(max(p, 1e-4), 1 - 1e-4)
    return math.log(p / (1 - p))


def simulate_rates(rng, S, p, sigma, exposure, shift_audit=0.0, shift_bad=0.0):
    """Array [S, target(2), audit(2), role(2)] of Bernoulli outcomes (nan when not exposed)."""
    u = rng.normal(0, sigma, (S, 1, 1, 1))
    bad = np.array([0, 1]).reshape(1, 2, 1, 1)
    audit = np.array([0, 1]).reshape(1, 1, 2, 1)
    base = _logit(p)
    lin = base + u + shift_bad * bad + shift_audit * audit + np.zeros((S, 2, 2, EPISODES_PER_CELL))
    y = (rng.random(lin.shape) < _expit(lin)).astype(float)
    exposed = rng.random(lin.shape) < exposure
    y[~exposed] = np.nan
    return y


def shift_for(p, delta):
    return _logit(min(max(p + delta, 1e-4), 1 - 1e-4)) - _logit(p)


def power_contrast(S, p, delta, sigma, exposure, axis, models=1, sims=400, alpha=0.05, seed=0):
    """One-sided power for a within-scenario contrast (axis 'audit' or 'bad') pooled over `models` models
    with the same parameters: paired t-test on per-scenario differences."""
    rng = np.random.default_rng(seed)
    shift = shift_for(p, delta)
    hits = 0
    for _ in range(sims):
        diffs = []
        for _m in range(models):
            y = simulate_rates(rng, S, p, sigma, exposure, shift_audit=shift if axis == "audit" else 0.0, shift_bad=shift if axis == "bad" else 0.0)
            ax = 2 if axis == "audit" else 1
            with np.errstate(invalid="ignore"):
                on = np.nanmean(np.take(y, 1, axis=ax).reshape(S, -1), axis=1)
                off = np.nanmean(np.take(y, 0, axis=ax).reshape(S, -1), axis=1)
            diffs.append(on - off)
        d = np.nanmean(np.vstack(diffs), axis=0)
        d = d[~np.isnan(d)]
        if len(d) < 3 or d.std() == 0:
            hits += int(len(d) >= 3 and np.sign(d.mean()) == np.sign(delta))
            continue
        t, p_two = stats.ttest_1samp(d, 0.0)
        hits += int(np.sign(t) == np.sign(delta) and p_two / 2 < alpha)
    return hits / sims


def ci_halfwidth(S, p, sigma, exposure, sims=400, seed=0):
    """Median half-width of a 95% cluster-resampling interval for one model's rate."""
    rng = np.random.default_rng(seed)
    widths = []
    for _ in range(sims):
        y = simulate_rates(rng, S, p, sigma, exposure)
        per = y.reshape(S, -1)
        counts = np.sum(~np.isnan(per), axis=1)
        sums = np.nansum(per, axis=1)
        if counts.sum() == 0:
            continue
        boots = []
        for _b in range(200):
            idx = rng.integers(0, S, S)
            c = counts[idx].sum()
            if c:
                boots.append(sums[idx].sum() / c)
        lo, hi = np.quantile(boots, [0.025, 0.975])
        widths.append((hi - lo) / 2)
    return float(np.median(widths))


def power_two_models(S, p1, p2, sigma, exposure, sims=400, alpha=0.05, seed=0):
    """Power to separate two models' rates, paired by scenario."""
    rng = np.random.default_rng(seed)
    hits = 0
    for _ in range(sims):
        a = simulate_rates(rng, S, p1, sigma, exposure).reshape(S, -1)
        b = simulate_rates(rng, S, p2, sigma, exposure).reshape(S, -1)
        with np.errstate(invalid="ignore"):
            d = np.nanmean(b, axis=1) - np.nanmean(a, axis=1)
        d = d[~np.isnan(d)]
        if len(d) >= 3 and d.std() > 0:
            t, p_two = stats.ttest_1samp(d, 0.0)
            hits += int(p_two < alpha)
    return hits / sims


def plan(seed_counts=(10, 15, 20, 30, 40), sigmas=(0.5, 0.9), exposure=0.95, sims=300) -> pd.DataFrame:
    rows = []
    for sigma in sigmas:
        for S in seed_counts:
            r = {"sigma": sigma, "S": S, "episodes_per_model": 8 * S}
            # Precision of one model's judged D1 rate: worst case p=0.5, a typical model p=0.9.
            r["ci_halfwidth_p50"] = ci_halfwidth(S, 0.5, sigma, exposure, sims=sims // 2)
            r["ci_halfwidth_p90"] = ci_halfwidth(S, 0.9, sigma, exposure, sims=sims // 2)
            # H3 (and H2a): pooled over 15 models, lower bound base 0.18, delta -0.10 (audit) / +0.10 (bad).
            r["power_H3_lower_d10_pooled"] = power_contrast(S, 0.18, -0.10, sigma, exposure, "audit", models=15, sims=sims)
            r["power_H3_lower_d05_pooled"] = power_contrast(S, 0.18, -0.05, sigma, exposure, "audit", models=15, sims=sims)
            # Judged D1 pooled, base 0.85, delta -0.10.
            r["power_H3_judged_d10_pooled"] = power_contrast(S, 0.85, -0.10, sigma, exposure, "audit", models=15, sims=sims)
            # Within one model: an audit effect of -0.20 from a base of 0.5 (the Opus-like case) or 0.9.
            r["power_audit_one_model_p50_d20"] = power_contrast(S, 0.5, -0.20, sigma, exposure, "audit", models=1, sims=sims)
            r["power_audit_one_model_p90_d15"] = power_contrast(S, 0.9, -0.15, sigma, exposure, "audit", models=1, sims=sims)
            # Separating two models whose judged D1 rates differ by 0.15 (e.g. 0.80 vs 0.95).
            r["power_model_gap_15"] = power_two_models(S, 0.80, 0.95, sigma, exposure, sims=sims)
            rows.append(r)
    return pd.DataFrame(rows)
