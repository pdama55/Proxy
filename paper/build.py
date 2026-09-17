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
from proxy.analysis.paper_numbers import per_model_table, write_numbers  # noqa: E402
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


def main(config: str = "configs/analysis.yaml") -> None:
    cfg = AnalysisConfig.load(ROOT / config)
    df = load_frame(EpisodeStore(), load_models(), runs=cfg.runs, primary_judge=cfg.primary_judge, principal_model=cfg.principal_model)
    confirmatory = df if cfg.confirmatory_runs is None else df[df["run"].isin(cfg.confirmatory_runs) & (df["report_variant"] == "open")]
    confirmatory = confirmatory[~confirmatory["error"]]
    variants = df[(~df["error"]) & (df["report_variant"] != "open") & (df["blocked_alt"] == 1.0)]
    pairs = int(variants[variants["report_variant"] == "tradeoffs"]["base_episode"].nunique())
    write_numbers(confirmatory, ROOT / "paper" / "numbers.tex", calibration={"good": 0.44, "mediocre": 0.24, "bad": 0.09},
                  extra={"nInterventionPairs": str(pairs), **compute_macros(), **debias_macros(confirmatory, cfg)})
    # Figures get the full frame: paper_figures keeps report variants out of the headline figures itself and
    # needs them for the intervention comparison.
    scored = df[(~df["error"]) & (df["run"].isin((cfg.confirmatory_runs or []) + [f"{r}--{v}" for r in (cfg.confirmatory_runs or []) for v in ("tradeoffs", "norm")]))]
    (ROOT / "paper" / "tables").mkdir(exist_ok=True)
    (ROOT / "paper" / "tables" / "per_model.tex").write_text(per_model_table(confirmatory) + "\n")
    (ROOT / "paper" / "tables" / "versions.tex").write_text(
        versions_table(list(cfg.runs or []) + ["main-v2-fable"]) + "\n")
    print("figures:", [p.name for p in paper_figures(scored, ROOT / "paper" / "figures")])
    subprocess.run(["tectonic", "-X", "compile", "main.tex"], cwd=ROOT / "paper", check=True)
    print("built", ROOT / "paper" / "main.pdf")


if __name__ == "__main__":
    main(*sys.argv[1:])
