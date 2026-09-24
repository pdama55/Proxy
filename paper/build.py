"""Rebuilds the paper from data: numbers.tex and figures from the analysis runs, then the PDF.

    python paper/build.py [configs/analysis.yaml]
"""

import subprocess
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from proxy.analysis.data import load_frame  # noqa: E402
from proxy.analysis.paper_figures import paper_figures  # noqa: E402
from proxy.analysis.paper_numbers import _macro_name, per_model_table, write_numbers  # noqa: E402
from proxy.analysis.report import AnalysisConfig  # noqa: E402
from proxy.config import load_models  # noqa: E402
from proxy.store import EpisodeStore  # noqa: E402


def debias_macros(confirmatory, cfg) -> dict[str, str]:
    """Judge-error-corrected non-disclosure rate, and how far it moves if the judge were much worse."""
    from proxy.analysis.confirmatory import unconditional_and_bounds
    from proxy.annotation.debias import confusion, debias, sensitivity_curve

    u = unconditional_and_bounds(confirmatory, B=2000)
    bounds = {
        "uncondNondisclosure": f"{100 * u['unconditional_nondisclosure']['estimate']:.1f}\\%",
        "boundsDone": f"{100 * u['manski_bounds_conditional']['lower']:.1f}--{100 * u['manski_bounds_conditional']['upper']:.1f}\\%",
        "boundsDtwo": f"{100 * u['dtwo_manski_bounds']['lower']:.1f}--{100 * u['dtwo_manski_bounds']['upper']:.1f}\\%",
    }

    a = confirmatory[confirmatory["blocked_alt"] == 1.0].dropna(subset=["a_nondisclosed", "a_unmentioned"])
    if a.empty:
        return {}
    # The grid mixes arms with 30 scenario seeds and arms with 12, so an episode-weighted pooled rate is a
    # statement about an episode mix. Report the model-averaged rate and the full-seed subset beside it.
    by_model = a.groupby("model")["a_nondisclosed"].mean()
    seeds = a.groupby("model")["scenario_seed"].nunique() if "scenario_seed" in a else a.groupby("model")["seed"].nunique()
    full = a[a["model"].isin(seeds[seeds == seeds.max()].index)]
    bounds.update({
        "doneModelAveraged": f"{100 * by_model.mean():.1f}\\%",
        "doneFullSeedOnly": f"{100 * full['a_nondisclosed'].mean():.1f}\\%",
        "nFullSeedModels": str(full["model"].nunique()),
    })
    a = a.assign(stratum=a["a_unmentioned"].map({1.0: "unmentioned", 0.0: "mentioned"}))
    share = a["stratum"].value_counts(normalize=True).to_dict()
    observed = a.groupby("stratum")["a_nondisclosed"].mean().to_dict()
    batches = sorted((ROOT / "data" / "annotations").glob("batch-*"))
    cells = confusion(batches, EpisodeStore(), cfg.primary_judge)
    if not cells:
        return {}
    d = debias(cells, observed, share)
    curve = {row["assumed_specificity"]: row["corrected"] for row in sensitivity_curve(cells, observed, share)}
    tp = sum(c["tp"] for c in cells.values())
    fn = sum(c["fn"] for c in cells.values())
    fp = sum(c["fp"] for c in cells.values())
    tn = sum(c["tn"] for c in cells.values())
    return {
        **bounds,
        "doneCorrected": f"{100 * d['corrected_overall']:.1f}\\%",
        "doneCorrectedHalfSpec": f"{100 * curve[0.5]:.1f}\\%",
        "doneCorrectedNineSpec": f"{100 * curve[0.9]:.1f}\\%",
        "validationN": str(tp + fn + fp + tn),
        "validationTP": str(tp), "validationFN": str(fn), "validationFP": str(fp), "validationTN": str(tn),
        "validationSens": f"{100 * tp / (tp + fn):.0f}\\%" if tp + fn else "n/a",
        "validationNegatives": str(fp + tn),
    }


def compute_macros() -> dict[str, str]:
    """Agent-side compute over every episode on disk, pilots and discarded arms included."""
    import json

    cost = tokens_in = tokens_out = 0.0
    episodes = 0
    for p in (ROOT / "data" / "runs").rglob("episodes/*.json"):
        try:
            st = (json.loads(p.read_text()).get("stats") or {})
        except (OSError, ValueError):
            continue
        episodes += 1
        cost += float(st.get("cost_usd") or 0)
        tokens_in += st.get("agent_tokens_in") or 0
        tokens_out += st.get("agent_tokens_out") or 0
    return {
        "computeEpisodes": f"{episodes:,}",
        "computeCost": f"{cost:,.0f}",
        "computeTokensIn": f"{tokens_in / 1e6:.0f}",
        "computeTokensOut": f"{tokens_out / 1e6:.0f}",
    }


def versions_table(runs: list[str]) -> str:
    """Served-model strings and the window each arm ran in, read back from the episodes themselves."""
    import json
    from collections import defaultdict

    seen, when = defaultdict(set), defaultdict(list)
    for p in (ROOT / "data" / "runs").rglob("episodes/*.json"):
        try:
            d = json.loads(p.read_text())
        except (OSError, ValueError):
            continue
        if d.get("run") not in runs:
            continue
        model = d["spec"]["model"]
        seen[model].update((d.get("agent") or {}).get("model_versions") or [])
        if d.get("created_at"):
            when[model].append(d["created_at"])
    rows = []
    for model in sorted(seen):
        stamps = sorted(when[model])
        served = ", ".join(sorted(seen[model])) or "--"
        pinned = "yes" if any(ch.isdigit() for ch in served.split("-")[-1]) and len(served.split("-")[-1]) >= 6 else "no"
        window = f"{stamps[0][:10]} to {stamps[-1][:10]}" if stamps else "--"
        rows.append((model.replace("_", r"\_"), served.replace("_", r"\_"), pinned, window))
    head = (r"\begin{tabular}{llll}" "\n" r"\toprule" "\n"
            r"Config name & Served model string & Dated & Window (UTC) \\" "\n" r"\midrule")
    body = "\n".join(" & ".join(f"\\texttt{{{c}}}" if i < 2 else c for i, c in enumerate(r)) + r" \\" for r in rows)
    return f"{head}\n{body}\n\\bottomrule\n\\end{{tabular}}"


def stats_macros(full_frame, confirmatory, results_dir: Path) -> dict[str, str]:
    """Every remaining prose figure, read from the analysis outputs rather than typed into the text.

    A number typed into a .tex file silently goes stale the moment an arm is added. These come from the same
    JSON the results table is built from, so the paper cannot disagree with its own analysis.
    """
    import json

    def pct(x, d=0):
        return "n/a" if x is None else f"{100 * x:.{d}f}\\%"

    def pts(x, d=1):
        return "n/a" if x is None else f"{abs(x) * 100:.{d}f}"

    conf_path, expl_path = results_dir / "confirmatory.json", results_dir / "exploratory.json"
    if not conf_path.exists() or not expl_path.exists():
        return {}
    c, e = json.loads(conf_path.read_text()), json.loads(expl_path.read_text())
    m: dict[str, str] = {}

    v = e["E0_violations_and_leaks"]["violation_rate"]
    m["violationRate"] = pct(v["estimate"], 1)
    m["violationCI"] = f"{100 * v['ci95'][0]:.1f}--{100 * v['ci95'][1]:.1f}"
    m["leakRate"] = pct(e["E0_violations_and_leaks"]["leak_rate"]["estimate"], 1)

    m["hTwoaPoints"] = pts(c["H2"]["H2a_blocked_alternative"]["lower_bound_bad_minus_good"]["estimate"])
    m["hTwoaP"] = f"{c['H2']['p_H2a']:.2f}".lstrip("0")
    m["hThreePoints"] = pts(c["H3"]["blocked_alternative_lower_bound_audit_minus_none"]["estimate"])
    m["hThreeP"] = f"{c['H3']['p'] * 3:.3f}".lstrip("0")
    m["hFiveGap"] = f"{c['H5']['rating_gap_report_minus_truth']['estimate']:.2f}"
    m["hFiveMissed"] = pct(c["H5"]["missed_intervention_rate"]["estimate"], 1)
    m["hFiveP"] = f"{c['H5']['p']:.2f}".lstrip("0")
    mis = confirmatory["principal_decision_mismatch"].dropna()
    missed = confirmatory["principal_missed_intervention"].dropna()
    if len(mis) and len(missed):
        m["principalOverCautious"] = pct(mis.mean() - missed.mean(), 1)
    rank = (c["H4"]["pooled_slope"].get("terms") or {}).get("capability_rank") or {}
    if rank.get("odds_ratio"):
        m["hFourOR"] = f"{rank['odds_ratio']:.2f}"
        if rank.get("or_ci95"):
            m["hFourORCI"] = f"{rank['or_ci95'][0]:.2f}--{rank['or_ci95'][1]:.2f}"

    # Report interventions, on the paired negotiations only. The "open" arm of this comparison must be the
    # confirmatory grid, not every run: breadth and the post-freeze arm also carry open reports, and pooling
    # them would compare the variants against a different sample than the one they were generated from.
    base = confirmatory[confirmatory["blocked_alt"] == 1.0].dropna(subset=["a_nondisclosed"])
    variants = full_frame[(full_frame["blocked_alt"] == 1.0)
                          & full_frame["run"].isin(["main-v2--tradeoffs", "main-v2--norm"])]
    variants = variants.dropna(subset=["a_nondisclosed"])
    a = base
    m["intOpenJudged"] = pct(base["a_nondisclosed"].mean()) if len(base) else "n/a"
    m["doneJudgedN"] = f"{len(base):,}"
    for variant, key in (("tradeoffs", "Tradeoffs"), ("norm", "Norm")):
        g = variants[variants["report_variant"] == variant]
        m[f"int{key}Judged"] = pct(g["a_nondisclosed"].mean()) if len(g) else "n/a"
    for variant, key in (("tradeoffs", "Tradeoffs"), ("norm", "Norm")):
        ch = e["E7_interventions"][variant]["judged_change"]
        m[f"int{key}Delta"] = f"{ch['estimate']:.2f}"
        m[f"int{key}DeltaCI"] = f"{ch['ci95'][0]:.2f} to {ch['ci95'][1]:.2f}"
        for row in e["E7_interventions"][variant].get("by_model", []):
            m[f"int{key}{_macro_name(row['model'])}"] = pct(row["v_judged"])

    for model, row in (e.get("E10_breadth", {}).get("by_model") or {}).items():
        judged = (row or {}).get("judged") or {}
        if judged.get("estimate") is not None:
            m[f"breadth{_macro_name(model)}"] = pct(judged["estimate"])
    # Stakes: disclosure among episodes where the requirement cost a lot versus a little.
    sp = base.dropna(subset=["points_forgone"])
    if len(sp):
        high, low = sp[sp["points_forgone"] > 10], sp[sp["points_forgone"] <= 10]
        m["stakesHighDisclosed"] = pct(1 - high["a_nondisclosed"].mean(), 1) if len(high) else "n/a"
        m["stakesLowDisclosed"] = pct(1 - low["a_nondisclosed"].mean(), 1) if len(low) else "n/a"
        from proxy.analysis.stats import cluster_bootstrap, diff_of

        d = cluster_bootstrap(sp.assign(stakes=(sp["points_forgone"] > 10).map({True: "high", False: "low"}),
                                        disclosed=1 - sp["a_nondisclosed"]),
                              diff_of("disclosed", "stakes", "low", "high"), B=2000)
        m["stakesDiff"] = f"{100 * d['estimate']:.1f}"
        m["stakesDiffCI"] = f"{100 * d['ci95'][0]:.1f} to {100 * d['ci95'][1]:+.1f}"
    # The mechanical floor implied by how few reports name the blocked offer at all.
    named = base.dropna(subset=["a_not_named"])
    if len(named):
        m["doneNotNamed"] = pct(named["a_not_named"].mean(), 1)
        # Naming is not logically necessary for conveying the deal, so "not named" is not a lower bound on
        # non-disclosure. Report how close it comes instead of asserting the implication.
        nn = named[named["a_not_named"] == 1.0]
        m["doneNotNamedN"] = f"{len(nn):,}"
        conveyed = nn[nn["a_nondisclosed"] == 0.0]
        m["doneNotNamedButConveyed"] = str(len(conveyed))
        if len(nn):
            m["doneNotNamedAndSilent"] = pct(1 - len(conveyed) / len(nn), 1)
    # Per-model ranges quoted as "0--4%" style spans.
    tr = [r["v_judged"] for r in e["E7_interventions"]["tradeoffs"].get("by_model", [])
          if r["model"] in ("gpt-6-astra", "gpt-5.6-sol", "gpt-5.6-luna", "grok-4.6")]
    if tr:
        m["intTradeoffsBestRange"] = f"{100 * min(tr):.0f}--{100 * max(tr):.0f}\\%"
    # D2 error range among the frontier models, so the "concentrated in weaker models" claim is checkable.
    frontier = ["claude-opus-5", "claude-sonnet-5", "gpt-6-astra", "gpt-5.6-sol", "gpt-5.6-luna", "grok-4.6"]
    fr = confirmatory[confirmatory["model"].isin(frontier)].dropna(subset=["total_misstated"])
    if len(fr):
        by = fr.groupby("model")["total_misstated"].mean()
        m["dtwoFrontierRange"] = f"{100 * by.min():.0f}--{100 * by.max():.0f}\\%"
    # Ablations: does the finding survive rewording the briefing?
    e4 = e.get("E4_ablations") or {}
    for row in e4.get("phrasing_D1") or []:
        m[f"ablPhrasing{row['phrasing'].capitalize()}"] = pct(row["mean"], 1)
    for row in e4.get("briefing_variant_D1") or []:
        m[f"ablSalience{row['briefing_variant'].replace('_', '').capitalize()}"] = pct(row["mean"], 1)
    for row in e4.get("report_variant_D1") or []:
        m[f"ablPrompt{row['report_variant'].capitalize()}"] = pct(row["mean"], 1)
    for key, name in (("low_salience_minus_base_D1", "ablSalienceDiff"), ("directive_minus_open_D1", "ablPromptDiff")):
        v = e4.get(key)
        if v:
            m[name] = f"{100 * v['estimate']:+.1f}"
            m[f"{name}CI"] = f"{100 * v['ci95'][0]:+.1f} to {100 * v['ci95'][1]:+.1f}"
            m[f"{name}N"] = str(v.get("n", ""))
    # LLM-counterparty arm: reported separately, never pooled with the scripted runs.
    e5 = e.get("E5_llm_counterparty") or {}
    if e5.get("episodes"):
        m["llmcpEpisodes"] = str(e5["episodes"])
        ex = e5.get("blocked_alternative_exposure") or {}
        if ex.get("estimate") is not None:
            m["llmcpExposure"] = pct(ex["estimate"], 1)
            m["llmcpExposed"] = str((e5.get("blocked_alternative_lower_bound") or {}).get("n", ""))
        dt = e5.get("stated_total_misstatement") or {}
        if dt.get("estimate") is not None:
            m["llmcpDtwo"] = pct(dt["estimate"], 1)
            m["llmcpDtwoN"] = str(dt.get("n", ""))
    opus = (e.get("E11_stakes", {}).get("by_model") or {}).get("claude-opus-5") or {}
    if opus.get("p") is not None:
        m["stakesOpusP"] = f"{opus['p']:.2f}".lstrip("0")
    return m


def fable_macros(full_frame) -> dict[str, str]:
    """Claude Fable 5.1 was added after the freeze, so it is reported separately and as a sensitivity check.

    The preregistered confirmatory set is unchanged; these macros let the paper state what happens when the
    arm is included, which is what the deviations log promises.
    """
    def pct(x, d=1):
        return "n/a" if x is None else f"{100 * x:.{d}f}\\%"

    ok = full_frame[(full_frame["run"] == "main-v2-fable") & (full_frame["report_variant"] == "open")]
    a = ok[ok["blocked_alt"] == 1.0].dropna(subset=["a_nondisclosed"])
    if not len(a):
        return {}
    m = {
        "fableJudged": pct(a["a_nondisclosed"].mean()),
        "fableN": str(len(a)),
        "fableDtwo": pct(ok["total_misstated"].dropna().mean()),
    }
    silent = a[a["a_nondisclosed"] == 1.0].dropna(subset=["probe_knew"])
    if len(silent):
        m["fableProbeKnew"] = pct(silent["probe_knew"].mean(), 0)
    # Is the new arm actually the same as Opus 5, or does it only look it?
    from proxy.analysis.stats import cluster_bootstrap, diff_of

    # Main grid only: Opus 5 also appears in the breadth runs, and pooling those would compare Fable's 30
    # scenarios against a different and larger scenario set.
    pair = full_frame[(full_frame["report_variant"] == "open") & (full_frame["blocked_alt"] == 1.0)
                      & full_frame["run"].isin(["main-v2", "main-v2-fable"])]
    pair = pair[pair["model"].isin(["claude-opus-5", "claude-fable-5-1"])].dropna(subset=["a_nondisclosed"])
    if pair["model"].nunique() == 2:
        d = cluster_bootstrap(pair, diff_of("a_nondisclosed", "model", "claude-opus-5", "claude-fable-5-1"), B=2000)
        m["fableVsOpus"] = f"{100 * d['estimate']:+.1f}"
        m["fableVsOpusCI"] = f"{100 * d['ci95'][0]:.1f} to {100 * d['ci95'][1]:+.1f}"
    # Headline with the arm folded in, so a reader can see it moves nothing.
    conf = full_frame[full_frame["run"].isin(["main-v2", "main-v2-qwen", "main-v2-fable"])]
    conf = conf[conf["report_variant"] == "open"]
    ca = conf[conf["blocked_alt"] == 1.0].dropna(subset=["a_nondisclosed"])
    m["doneJudgedWithFable"] = pct(ca["a_nondisclosed"].mean())
    m["nEpisodesWithFable"] = f"{len(conf):,}"
    return m


def agreement_macros() -> dict[str, str]:
    """Annotator and judge agreement, read from the generated agreement report."""
    import json

    path = ROOT / "data" / "annotations" / "batch-a" / "agreement.json"
    if not path.exists():
        return {}
    rep = json.loads(path.read_text())
    dis = rep["types"]["disclosure"]
    m: dict[str, str] = {}
    pair = next(iter(dis["human_vs_human"].values()), None)
    if pair and pair.get("binary_acknowledged"):
        m["kappaHuman"] = f"{pair['binary_acknowledged']['kappa']:.2f}"
        m["kappaHumanRaw"] = f"{100 * pair['binary_acknowledged']['raw_agreement']:.0f}\\%"
        m["kappaHumanFourWayRaw"] = f"{100 * pair['raw_agreement']:.0f}\\%"
        m["kappaHumanFourWay"] = f"{pair['kappa']:.2f}"
    for judge, st in dis.get("vs_consensus", {}).items():
        bv = st.get("binary_vs_binary_consensus") or {}
        if bv.get("kappa") is not None:
            tag = "Primary" if "kimi" in judge else "Second"
            m[f"kappaJudge{tag}"] = f"{bv['kappa']:.2f}"
            m[f"kappaJudge{tag}N"] = str(bv["n"])
            m[f"kappaJudge{tag}Raw"] = f"{100 * bv['raw_agreement']:.0f}\\%"
    ex = rep["types"].get("stated_total", {}).get("extractor_vs_consensus") or {}
    if ex:
        m["extractorPrecision"] = f"{ex['precision']:.2f}"
        m["extractorRecall"] = f"{ex['recall']:.2f}"
    sp = dis.get("stage1_precision") or {}
    if sp.get("precision") is not None:
        m["stageOnePrecision"] = f"{sp['precision']:.2f}"
        m["stageOneN"] = str(sp["n"])
    return m


def main(config: str = "configs/analysis.yaml") -> None:
    cfg = AnalysisConfig.load(ROOT / config)
    df = load_frame(EpisodeStore(), load_models(), runs=cfg.runs, primary_judge=cfg.primary_judge, principal_model=cfg.principal_model)
    confirmatory = df if cfg.confirmatory_runs is None else df[df["run"].isin(cfg.confirmatory_runs) & (df["report_variant"] == "open")]
    confirmatory = confirmatory[~confirmatory["error"]]
    variants = df[(~df["error"]) & (df["report_variant"] != "open") & (df["blocked_alt"] == 1.0)]
    pairs = int(variants[variants["report_variant"] == "tradeoffs"]["base_episode"].nunique())
    write_numbers(confirmatory, ROOT / "paper" / "numbers.tex", calibration={"good": 0.44, "mediocre": 0.24, "bad": 0.09},
                  extra={"nInterventionPairs": str(pairs), **compute_macros(),
                         **stats_macros(df[~df["error"]], confirmatory, ROOT / "results" / "main-v2"),
                         **fable_macros(df[~df["error"]]), **agreement_macros(),
                         **debias_macros(confirmatory, cfg)})
    # Figures get the full frame: paper_figures keeps report variants out of the headline figures itself and
    # needs them for the intervention comparison.
    scored = df[(~df["error"]) & (df["run"].isin((cfg.confirmatory_runs or []) + [f"{r}--{v}" for r in (cfg.confirmatory_runs or []) for v in ("tradeoffs", "norm")]))]
    (ROOT / "paper" / "tables").mkdir(exist_ok=True)
    (ROOT / "paper" / "tables" / "per_model.tex").write_text(per_model_table(confirmatory) + "\n")
    (ROOT / "paper" / "tables" / "versions.tex").write_text(
        versions_table(list(cfg.runs or []) + ["main-v2-fable"]) + "\n")
    print("figures:", [p.name for p in paper_figures(scored, ROOT / "paper" / "figures")])
    # Both drivers share sections/, so they must be rebuilt together: a stale tmlr.pdf is the submission
    # artifact, and it silently keeps whatever claims the sections used to make.
    for driver in ("main.tex", "tmlr.tex"):
        if (ROOT / "paper" / driver).exists():
            subprocess.run(["tectonic", "-X", "compile", driver], cwd=ROOT / "paper", check=True)
            print("built", ROOT / "paper" / driver.replace(".tex", ".pdf"))


if __name__ == "__main__":
    main(*sys.argv[1:])
