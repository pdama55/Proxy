"""EXPLORATORY analyses. Not preregistered as confirmatory tests. Every output from this module is labeled
exploratory automatically by the report writer; nothing here may be promoted to a confirmatory claim."""

import pandas as pd

from proxy.analysis.stats import cluster_bootstrap, diff_of, mean_of, per_seed

LABEL = "EXPLORATORY"


def e1_leak_vs_floor(df: pd.DataFrame, B: int) -> dict:
    """Are leaks disclosed at a different rate than floor violations?"""
    v = df[(df["violated"] == 1.0)].dropna(subset=["v_unmentioned"])
    l = df[(df["leaked"] == 1.0)].dropna(subset=["l_unmentioned"])
    stacked = pd.concat([
        v.assign(kind="floor", unmentioned=v["v_unmentioned"]),
        l.assign(kind="leak", unmentioned=l["l_unmentioned"]),
    ], ignore_index=True)
    return {
        "question": "Leak non-disclosure vs floor-violation non-disclosure (lower bound)",
        "leak_rate": cluster_bootstrap(l, mean_of("l_unmentioned"), B=B),
        "leak_count": int(len(l)),
        "floor_rate": cluster_bootstrap(v, mean_of("v_unmentioned"), B=B),
        "leak_minus_floor": cluster_bootstrap(stacked, diff_of("unmentioned", "kind", "floor", "leak"), B=B),
    }


def e2_issue_kind(df: pd.DataFrame, B: int) -> dict:
    """Does non-disclosure differ between ordinal (delivery, warranty) and categorical (payment) issues?"""
    v = df[(df["violated"] == 1.0)].dropna(subset=["v_unmentioned"]).copy()
    v["issue_kind"] = v["floor_issue"].map({"payment_terms": "categorical", "price": "numeric"}).fillna("ordinal")
    return {
        "question": "Non-disclosure by kind of violated issue",
        "by_issue": per_seed(v, "v_unmentioned", ["floor_issue"]).to_dict("records"),
        "categorical_minus_ordinal": cluster_bootstrap(v, diff_of("v_unmentioned", "issue_kind", "ordinal", "categorical"), B=B),
    }


def e3_no_deal_vs_bad(df: pd.DataFrame, B: int) -> dict:
    """Are no-deal outcomes characterized differently from bad deals?"""
    c = df.dropna(subset=["char_rating"])
    c = c[c["outcome_target"].isin(["bad", "no_deal"])]
    return {
        "question": "Characterization rating: no_deal minus bad",
        "no_deal_minus_bad": cluster_bootstrap(c, diff_of("char_rating", "outcome_target", "bad", "no_deal"), B=B),
    }


def e4_ablations(df: pd.DataFrame, B: int) -> dict:
    """Phrasing, salience, and report-prompt ablations (research plan section 8)."""
    v = df[(df["violated"] == 1.0)].dropna(subset=["v_unmentioned"])
    out = {"question": "Lower-bound non-disclosure across prompt ablations"}
    for col in ("phrasing", "briefing_variant", "report_variant"):
        if v[col].nunique() > 1:
            out[col] = per_seed(v, "v_unmentioned", [col]).to_dict("records")
    if set(v["report_variant"]) >= {"open", "directive"}:
        out["directive_minus_open"] = cluster_bootstrap(v, diff_of("v_unmentioned", "report_variant", "open", "directive"), B=B)
    if set(v["briefing_variant"]) >= {"base", "low_salience"}:
        out["low_salience_minus_base"] = cluster_bootstrap(v, diff_of("v_unmentioned", "briefing_variant", "base", "low_salience"), B=B)
        out["violation_rate_by_salience"] = per_seed(df.dropna(subset=["violated"]), "violated", ["briefing_variant"]).to_dict("records")
    return out


def e5_llm_counterparty(df: pd.DataFrame, B: int) -> dict:
    """External-validity arm, reported separately and never pooled with scripted runs."""
    llm = df[(df["counterparty_kind"] == "llm") & (~df["error"]) & (df["scored"])]
    v = llm[llm["violated"] == 1.0].dropna(subset=["v_unmentioned"])
    return {
        "question": "LLM-counterparty arm",
        "episodes": int(len(llm)),
        "violation_rate": cluster_bootstrap(llm.dropna(subset=["violated"]), mean_of("violated"), B=B),
        "leak_rate": cluster_bootstrap(llm.dropna(subset=["leaked"]), mean_of("leaked"), B=B),
        "nondisclosure_lower_bound": cluster_bootstrap(v, mean_of("v_unmentioned"), B=B),
        "by_model": per_seed(v, "v_unmentioned", ["model"]).to_dict("records"),
    }


def e6_capability_by_active_params(df: pd.DataFrame, B: int) -> dict:
    """Qwen ladder reordered by active rather than total parameters (sensitivity for H4)."""
    active = {"qwen3.5-9b": 9, "qwen3.5-27b": 27, "qwen3.5-35b-a3b": 3, "qwen3.5-122b-a10b": 10, "qwen3.5-397b-a17b": 17}
    v = df[(df["violated"] == 1.0) & df["model"].isin(active)].dropna(subset=["v_unmentioned"]).copy()
    v["active_b"] = v["model"].map(active)
    return {"question": "Qwen non-disclosure by active parameters", "by_active": per_seed(v, "v_unmentioned", ["active_b", "model"]).to_dict("records")}


def run_exploratory(df: pd.DataFrame, B: int = 1000) -> dict:
    scripted = df[(~df["error"]) & (df["scored"]) & (df["counterparty_kind"] == "scripted")]
    return {
        "label": LABEL,
        "E1_leak_vs_floor": e1_leak_vs_floor(scripted, B),
        "E2_issue_kind": e2_issue_kind(scripted, B),
        "E3_no_deal_vs_bad": e3_no_deal_vs_bad(scripted, B),
        "E4_ablations": e4_ablations(scripted, B),
        "E5_llm_counterparty": e5_llm_counterparty(df, B),
        "E6_active_params": e6_capability_by_active_params(scripted, B),
    }
