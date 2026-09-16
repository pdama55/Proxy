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


def main(config: str = "configs/analysis.yaml") -> None:
    cfg = AnalysisConfig.load(ROOT / config)
    df = load_frame(EpisodeStore(), load_models(), runs=cfg.runs, primary_judge=cfg.primary_judge, principal_model=cfg.principal_model)
    confirmatory = df if cfg.confirmatory_runs is None else df[df["run"].isin(cfg.confirmatory_runs) & (df["report_variant"] == "open")]
    confirmatory = confirmatory[~confirmatory["error"]]
    variants = df[(~df["error"]) & (df["report_variant"] != "open") & (df["blocked_alt"] == 1.0)]
    pairs = int(variants[variants["report_variant"] == "tradeoffs"]["base_episode"].nunique())
    write_numbers(confirmatory, ROOT / "paper" / "numbers.tex", calibration={"good": 0.44, "mediocre": 0.24, "bad": 0.09},
                  extra={"nInterventionPairs": str(pairs), **debias_macros(confirmatory, cfg)})
    # Figures get the full frame: paper_figures keeps report variants out of the headline figures itself and
    # needs them for the intervention comparison.
    scored = df[(~df["error"]) & (df["run"].isin((cfg.confirmatory_runs or []) + [f"{r}--{v}" for r in (cfg.confirmatory_runs or []) for v in ("tradeoffs", "norm")]))]
    (ROOT / "paper" / "tables").mkdir(exist_ok=True)
    (ROOT / "paper" / "tables" / "per_model.tex").write_text(per_model_table(confirmatory) + "\n")
    print("figures:", [p.name for p in paper_figures(scored, ROOT / "paper" / "figures")])
    subprocess.run(["tectonic", "-X", "compile", "main.tex"], cwd=ROOT / "paper", check=True)
    print("built", ROOT / "paper" / "main.pdf")


if __name__ == "__main__":
    main(*sys.argv[1:])
