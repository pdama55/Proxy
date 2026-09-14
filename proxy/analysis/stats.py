"""Estimators. Episodes on the same scenario are not independent, so every interval resamples scenarios
(clusters), never episodes, and every model-based test clusters on scenario."""

import math
import warnings

import numpy as np
import pandas as pd


def cluster_bootstrap(df: pd.DataFrame, stat, cluster: str = "seed", B: int = 2000, seed: int = 0) -> dict:
    """stat(df) -> float. Returns estimate, percentile 95% CI, and a one-sided bootstrap p for stat <= 0."""
    if df is None or df.empty:
        return {"estimate": math.nan, "ci95": [math.nan, math.nan], "p_le_0": math.nan, "n": 0, "clusters": 0}
    est = stat(df)
    df = df.reset_index(drop=True)
    positions = [idx.to_numpy() for _, idx in df.groupby(cluster).groups.items()]
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(B):
        pick = rng.integers(0, len(positions), len(positions))
        sample = df.iloc[np.concatenate([positions[i] for i in pick])]
        v = stat(sample)
        if v is not None and not (isinstance(v, float) and math.isnan(v)):
            vals.append(v)
    if not vals:
        return {"estimate": est, "ci95": [math.nan, math.nan], "p_le_0": math.nan, "n": len(df), "clusters": len(positions)}
    arr = np.array(vals)
    return {
        "estimate": est,
        "ci95": [float(np.quantile(arr, 0.025)), float(np.quantile(arr, 0.975))],
        "p_le_0": float((np.sum(arr <= 0) + 1) / (len(arr) + 1)),
        "n": int(len(df)),
        "clusters": len(positions),
        "boot_sd": float(arr.std(ddof=1)) if len(arr) > 1 else math.nan,
    }


def mean_of(col: str):
    def f(d: pd.DataFrame) -> float:
        s = d[col].dropna()
        return float(s.mean()) if len(s) else math.nan

    return f


def diff_of(col: str, group_col: str, a, b):
    """mean(col | group_col == b) - mean(col | group_col == a)."""

    def f(d: pd.DataFrame) -> float:
        xa = d.loc[d[group_col] == a, col].dropna()
        xb = d.loc[d[group_col] == b, col].dropna()
        if not len(xa) or not len(xb):
            return math.nan
        return float(xb.mean() - xa.mean())

    return f


def _terms(df: pd.DataFrame, candidates: list[str]) -> list[str]:
    """Keep categorical covariates only when they vary, so single-model or single-condition subsets still fit."""
    out = []
    for c in candidates:
        col = c[2:-1] if c.startswith("C(") else c
        if col in df and df[col].nunique(dropna=True) > 1:
            out.append(c)
    return out


def gee_logit(df: pd.DataFrame, outcome: str, focal: str, covariates: list[str], cluster: str = "seed") -> dict:
    """Population-averaged logistic regression with exchangeable within-scenario correlation and robust SEs."""
    import statsmodels.api as sm
    import statsmodels.formula.api as smf

    d = df.dropna(subset=[outcome]).copy()
    focal_col = focal[2:-1].split(",")[0] if focal.startswith("C(") else focal
    if d.empty or d[outcome].nunique() < 2 or focal_col not in d or d[focal_col].nunique() < 2 or d[cluster].nunique() < 2:
        return {"ok": False, "reason": "insufficient variation", "n": len(d)}
    rhs = " + ".join([focal] + _terms(d, covariates))
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = smf.gee(f"{outcome} ~ {rhs}", groups=d[cluster], data=d, family=sm.families.Binomial(),
                          cov_struct=sm.cov_struct.Exchangeable()).fit()
    except Exception as e:  # separation and singular designs are expected in small pilots
        return {"ok": False, "reason": f"{type(e).__name__}: {e}", "n": len(d)}
    rows = {}
    ci = res.conf_int()
    for name in res.params.index:
        if name == "Intercept":
            continue
        rows[name] = {
            "coef": float(res.params[name]),
            "odds_ratio": float(np.exp(res.params[name])),
            "or_ci95": [float(np.exp(ci.loc[name, 0])), float(np.exp(ci.loc[name, 1]))],
            "p": float(res.pvalues[name]),
        }
    return {"ok": True, "formula": f"{outcome} ~ {rhs}", "n": int(res.nobs), "clusters": int(d[cluster].nunique()), "terms": rows}


def mixed_logit_bayes(df: pd.DataFrame, outcome: str, focal: str, covariates: list[str], cluster: str = "seed") -> dict:
    """Mixed-effects logistic regression with a random intercept per scenario (variational Bayes).
    Reported alongside the GEE as the model named in the research plan."""
    from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM

    d = df.dropna(subset=[outcome]).copy()
    focal_col = focal[2:-1].split(",")[0] if focal.startswith("C(") else focal
    if d.empty or d[outcome].nunique() < 2 or d[focal_col].nunique() < 2 or d[cluster].nunique() < 2:
        return {"ok": False, "reason": "insufficient variation", "n": len(d)}
    rhs = " + ".join([focal] + _terms(d, covariates))
    d["_cluster"] = d[cluster].astype(str)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = BinomialBayesMixedGLM.from_formula(f"{outcome} ~ {rhs}", {"scenario": "0 + C(_cluster)"}, d)
            res = model.fit_vb()
    except Exception as e:
        return {"ok": False, "reason": f"{type(e).__name__}: {e}", "n": len(d)}
    names = model.exog_names
    rows = {}
    for i, name in enumerate(names):
        if name == "Intercept":
            continue
        mean, sd = float(res.fe_mean[i]), float(res.fe_sd[i])
        rows[name] = {"coef": mean, "sd": sd, "ci95": [mean - 1.96 * sd, mean + 1.96 * sd], "odds_ratio": float(np.exp(mean))}
    return {"ok": True, "formula": f"{outcome} ~ {rhs} + (1|scenario)", "n": len(d), "terms": rows,
            "scenario_sd": float(np.exp(res.vcp_mean[0])) if len(res.vcp_mean) else math.nan}


def holm(pvals: dict[str, float]) -> dict[str, float]:
    items = [(k, p) for k, p in pvals.items() if p is not None and not math.isnan(p)]
    items.sort(key=lambda kv: kv[1])
    m = len(items)
    adjusted, running = {}, 0.0
    for i, (k, p) in enumerate(items):
        running = max(running, min(1.0, (m - i) * p))
        adjusted[k] = running
    for k in pvals:
        adjusted.setdefault(k, math.nan)
    return adjusted


def per_seed(df: pd.DataFrame, col: str, by: list[str]) -> pd.DataFrame:
    """Estimate per scenario seed, then mean and SD across seeds: variance across seeds, not a single run."""
    d = df.dropna(subset=[col])
    if d.empty:
        return pd.DataFrame()
    s = d.groupby(by + ["seed"])[col].mean().reset_index()
    return s.groupby(by)[col].agg(seeds="count", mean="mean", sd_across_seeds="std").reset_index()
