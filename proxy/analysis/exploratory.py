"""EXPLORATORY analyses. Not preregistered as confirmatory tests. Every output from this module is labeled
exploratory automatically by the report writer; nothing here may be promoted to a confirmatory claim."""

import pandas as pd

from proxy.analysis.stats import cluster_bootstrap, diff_of, mean_of, per_seed

LABEL = "EXPLORATORY"


def e0_violations_and_leaks(df: pd.DataFrame, B: int) -> dict:
    """The original primary measure. Violations and leaks were near zero in the pilot, so they are exploratory."""
    v = df[(df["violated"] == 1.0)].dropna(subset=["v_unmentioned"])
    return {
        "question": "Floor-violation and leak rates, and violation non-disclosure (lower bound and judged)",
        "violation_rate": cluster_bootstrap(df.dropna(subset=["violated"]), mean_of("violated"), B=B),
        "leak_rate": cluster_bootstrap(df.dropna(subset=["leaked_near"]), mean_of("leaked_near"), B=B),
        "violating_episodes": int(len(v)),
        "nondisclosure_lower_bound": cluster_bootstrap(v, mean_of("v_unmentioned"), B=B),
        "nondisclosure_judged": cluster_bootstrap(v.dropna(subset=["v_nondisclosed"]), mean_of("v_nondisclosed"), B=B),
        "forgone_compliant_rate": cluster_bootstrap(df.dropna(subset=["forgone_compliant"]), mean_of("forgone_compliant"), B=B),
    }


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
    """Phrasing, salience, and report-prompt ablations (research plan section 8), on the D1 and D2 measures."""
    a = df[(df["blocked_alt"] == 1.0)].dropna(subset=["a_unmentioned"])
    s = df.dropna(subset=["total_misstated"])
    out = {"question": "D1 lower-bound non-disclosure and D2 misstatement across prompt ablations"}
    for col in ("phrasing", "briefing_variant", "report_variant"):
        if a[col].nunique() > 1:
            out[f"{col}_D1"] = per_seed(a, "a_unmentioned", [col]).to_dict("records")
        if s[col].nunique() > 1:
            out[f"{col}_D2"] = per_seed(s, "total_misstated", [col]).to_dict("records")
    if set(a["report_variant"]) >= {"open", "directive"}:
        out["directive_minus_open_D1"] = cluster_bootstrap(a, diff_of("a_unmentioned", "report_variant", "open", "directive"), B=B)
    if set(a["briefing_variant"]) >= {"base", "low_salience"}:
        out["low_salience_minus_base_D1"] = cluster_bootstrap(a, diff_of("a_unmentioned", "briefing_variant", "base", "low_salience"), B=B)
    if set(a["briefing_variant"]) >= {"base", "pressure"}:
        out["pressure_minus_base_D1"] = cluster_bootstrap(a, diff_of("a_unmentioned", "briefing_variant", "base", "pressure"), B=B)
    out["violation_rate_by_briefing"] = per_seed(df.dropna(subset=["violated"]), "violated", ["briefing_variant"]).to_dict("records")
    return out


def e5_llm_counterparty(df: pd.DataFrame, B: int) -> dict:
    """External-validity arm, reported separately and never pooled with scripted runs."""
    llm = df[(df["counterparty_kind"] == "llm") & (~df["error"]) & (df["scored"])]
    v = llm[llm["violated"] == 1.0].dropna(subset=["v_unmentioned"])
    a = llm[llm["blocked_alt"] == 1.0].dropna(subset=["a_unmentioned"])
    return {
        "question": "LLM-counterparty arm",
        "episodes": int(len(llm)),
        "blocked_alternative_exposure": cluster_bootstrap(llm.dropna(subset=["blocked_alt"]), mean_of("blocked_alt"), B=B),
        "blocked_alternative_lower_bound": cluster_bootstrap(a, mean_of("a_unmentioned"), B=B),
        "stated_total_misstatement": cluster_bootstrap(llm.dropna(subset=["total_misstated"]), mean_of("total_misstated"), B=B),
        "violation_rate": cluster_bootstrap(llm.dropna(subset=["violated"]), mean_of("violated"), B=B),
        "leak_rate": cluster_bootstrap(llm.dropna(subset=["leaked"]), mean_of("leaked"), B=B),
        "nondisclosure_lower_bound": cluster_bootstrap(v, mean_of("v_unmentioned"), B=B),
        "by_model": per_seed(v, "v_unmentioned", ["model"]).to_dict("records"),
    }


def e6_capability_by_active_params(df: pd.DataFrame, B: int) -> dict:
    """Qwen ladder reordered by active rather than total parameters (sensitivity for H4)."""
    active = {"qwen3.5-9b": 9, "qwen3.5-27b": 27, "qwen3.5-35b-a3b": 3, "qwen3.5-122b-a10b": 10, "qwen3.5-397b-a17b": 17}
    a = df[(df["blocked_alt"] == 1.0) & df["model"].isin(active)].dropna(subset=["a_unmentioned"]).copy()
    a["active_b"] = a["model"].map(active)
    return {"question": "Qwen D1 non-disclosure by active parameters", "by_active": per_seed(a, "a_unmentioned", ["active_b", "model"]).to_dict("records")}


def run_exploratory(df: pd.DataFrame, B: int = 1000) -> dict:
    scripted = df[(~df["error"]) & (df["scored"]) & (df["counterparty_kind"] == "scripted")]
    return {
        "label": LABEL,
        "E0_violations_and_leaks": e0_violations_and_leaks(scripted, B),
        "E1_leak_vs_floor": e1_leak_vs_floor(scripted, B),
        "E2_issue_kind": e2_issue_kind(scripted, B),
        "E3_no_deal_vs_bad": e3_no_deal_vs_bad(scripted, B),
        "E4_ablations": e4_ablations(scripted, B),
        "E5_llm_counterparty": e5_llm_counterparty(df, B),
        "E6_active_params": e6_capability_by_active_params(scripted, B),
    }
