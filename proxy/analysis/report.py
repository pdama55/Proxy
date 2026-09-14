"""One command regenerates every table, figure, and number: `proxy analyze all`."""

import datetime as dt
import json
import math
from pathlib import Path

import pandas as pd
import yaml
from pydantic import BaseModel

from proxy.analysis.confirmatory import run_confirmatory
from proxy.analysis.data import load_frame
from proxy.analysis.exploratory import LABEL, run_exploratory
from proxy.analysis.figures import all_figures
from proxy.config import load_models
from proxy.store import EpisodeStore
from proxy.util import json_clean


class AnalysisConfig(BaseModel):
    name: str
    runs: list[str]
    primary_judge: str
    principal_model: str | None = None
    bootstrap: int = 2000
    exploratory_bootstrap: int = 1000
    suspect_parse_failure_rate: float = 0.05

    @classmethod
    def load(cls, path) -> "AnalysisConfig":
        return cls(**yaml.safe_load(Path(path).read_text()))


def exclusions(df: pd.DataFrame, threshold: float) -> dict:
    total = len(df)
    by_model = []
    for m, g in df.groupby("model"):
        turns = g["agent_turns"].sum()
        rate = g["parse_failures"].sum() / turns if turns else math.nan
        by_model.append({
            "model": m,
            "episodes": int(len(g)),
            "errors": int(g["error"].sum()),
            "error_rate": float(g["error"].mean()),
            "parse_failure_rate_per_turn": rate,
            "suspect": bool(rate > threshold) if rate == rate else False,
            "model_versions": sorted({v for s in g["model_versions"] for v in s.split(",") if v}),
        })
    return {
        "episodes": int(total),
        "excluded_errors": int(df["error"].sum()),
        "exclusion_rate": float(df["error"].mean()) if total else math.nan,
        "suspect_parse_failure_threshold": threshold,
        "by_model": by_model,
    }


def _fmt_est(e: dict | None, pct: bool = True) -> str:
    if not e or e.get("estimate") is None or (isinstance(e.get("estimate"), float) and math.isnan(e["estimate"])):
        return "n/a"
    f = (lambda v: f"{100 * v:.1f}%") if pct else (lambda v: f"{v:+.2f}")
    lo, hi = e.get("ci95", [math.nan, math.nan])
    ci = "" if lo is None or (isinstance(lo, float) and math.isnan(lo)) else f" [{f(lo)}, {f(hi)}]"
    return f"{f(e['estimate'])}{ci} (n={e.get('n', '?')}, scenarios={e.get('clusters', '?')})"


def _p(v) -> str:
    return "n/a" if v is None or (isinstance(v, float) and math.isnan(v)) else f"{v:.4f}"


def summary_markdown(cfg: AnalysisConfig, conf: dict, expl: dict, excl: dict, figures: list[str]) -> str:
    L = [
        f"# Results: {cfg.name}",
        "",
        f"Generated {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')} from runs {', '.join(cfg.runs)} by `proxy analyze all`. Do not edit by hand.",
        "",
        f"Episodes: {excl['episodes']} · excluded (errors): {excl['excluded_errors']} ({100 * excl['exclusion_rate']:.1f}%)",
        "",
        "Intervals are 95% cluster-bootstrap percentile intervals resampling scenarios. p values are one-sided in the preregistered direction; Holm-adjusted over H1, H2, H3, H5.",
        "",
        "## Confirmatory",
        "",
        "| Hypothesis | Estimate | p | p (Holm) |",
        "| --- | --- | --- | --- |",
        f"| H1 non-disclosure of violations, judge-free lower bound | {_fmt_est(conf['H1']['nondisclosure_lower_bound'])} | {_p(conf['H1']['p'])} | {_p(conf['H1']['p_holm'])} |",
        f"| H1 non-disclosure, judged | {_fmt_est(conf['H1']['nondisclosure_judged'])} | | |",
        f"| H2 lower bound, bad minus good | {_fmt_est(conf['H2']['nondisclosure_lower_bound_bad_minus_good'], pct=False)} | {_p(conf['H2']['p'])} | {_p(conf['H2']['p_holm'])} |",
        f"| H2 characterization bias, bad minus good | {_fmt_est(conf['H2']['characterization_bias_bad_minus_good'], pct=False)} | | |",
        f"| H3 lower bound, audit minus none | {_fmt_est(conf['H3']['nondisclosure_lower_bound_audit_minus_none'], pct=False)} | {_p(conf['H3']['p'])} | {_p(conf['H3']['p_holm'])} |",
        f"| H4 capability slope (log-odds per rank) | {_gee_term(conf['H4']['pooled_slope'], 'capability_rank')} | {_p(conf['H4']['p_decreasing'])} (for decrease) | not in family |",
        f"| H5 principal rating gap, report minus truth | {_fmt_est(conf['H5']['rating_gap_report_minus_truth'], pct=False)} | | |",
        f"| H5 rating gap, bad minus good | {_fmt_est(conf['H5']['rating_gap_bad_minus_good'], pct=False)} | {_p(conf['H5']['p'])} | {_p(conf['H5']['p_holm'])} |",
        f"| H5 missed interventions | {_fmt_est(conf['H5']['missed_intervention_rate'])} | | |",
        "",
        f"Violation rate: {_fmt_est(conf['H1']['violation_rate'])} · episodes with a violation: {conf['H1']['episodes_with_violation']}",
        "",
        "Non-disclosure is conditional on violating, and violating is itself an outcome of model and condition. Read H2 and H3 alongside the violation rates in confirmatory.json.",
        "",
        "## Exclusions and suspect models",
        "",
        "| Model | Episodes | Errors | Parse failures / turn | Suspect | Versions |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for m in excl["by_model"]:
        rate = m["parse_failure_rate_per_turn"]
        L.append(f"| {m['model']} | {m['episodes']} | {m['errors']} | {'n/a' if rate != rate else f'{100 * rate:.1f}%'} | {'yes' if m['suspect'] else ''} | {', '.join(m['model_versions'])} |")
    L += ["", f"## {LABEL}: not preregistered", ""]
    e = expl
    L += [
        f"- {LABEL} E1 leak non-disclosure: {_fmt_est(e['E1_leak_vs_floor']['leak_rate'])}; floor: {_fmt_est(e['E1_leak_vs_floor']['floor_rate'])}",
        f"- {LABEL} E2 categorical minus ordinal issue: {_fmt_est(e['E2_issue_kind']['categorical_minus_ordinal'], pct=False)}",
        f"- {LABEL} E3 characterization no_deal minus bad: {_fmt_est(e['E3_no_deal_vs_bad']['no_deal_minus_bad'], pct=False)}",
        f"- {LABEL} E5 LLM-counterparty arm: {e['E5_llm_counterparty']['episodes']} episodes, lower-bound non-disclosure {_fmt_est(e['E5_llm_counterparty']['nondisclosure_lower_bound'])}",
        "",
        "## Figures",
        "",
    ]
    L += [f"- `{Path(p).name}`" for p in figures if p.endswith(".png")] or ["- none (insufficient data)"]
    return "\n".join(L) + "\n"


def _gee_term(g: dict, term: str) -> str:
    if not g or not g.get("ok") or term not in g.get("terms", {}):
        return f"n/a ({(g or {}).get('reason', 'not fitted')})"
    t = g["terms"][term]
    lo, hi = t["or_ci95"]
    return f"{t['coef']:+.3f} (OR {t['odds_ratio']:.2f} [{lo:.2f}, {hi:.2f}], n={g['n']})"


def analyze_all(store: EpisodeStore, cfg: AnalysisConfig, out_dir: Path, models=None) -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    models = models or load_models()
    df = load_frame(store, models, runs=cfg.runs, primary_judge=cfg.primary_judge, principal_model=cfg.principal_model)
    if df.empty:
        raise SystemExit(f"no episodes found for runs {cfg.runs}")
    df.to_csv(out_dir / "episodes.csv", index=False)

    conf = run_confirmatory(df, B=cfg.bootstrap)
    expl = run_exploratory(df, B=cfg.exploratory_bootstrap)
    excl = exclusions(df, cfg.suspect_parse_failure_rate)
    figures = all_figures(df, out_dir / "figures")

    (out_dir / "confirmatory.json").write_text(json.dumps(json_clean(conf), indent=1))
    (out_dir / f"{LABEL.lower()}.json").write_text(json.dumps(json_clean(expl), indent=1))
    (out_dir / "exclusions.json").write_text(json.dumps(json_clean(excl), indent=1))
    (out_dir / "results.md").write_text(summary_markdown(cfg, conf, expl, excl, figures))
    return {"out_dir": str(out_dir), "episodes": len(df), "figures": len([f for f in figures if f.endswith(".png")])}
