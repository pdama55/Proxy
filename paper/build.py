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
from proxy.analysis.paper_numbers import write_numbers  # noqa: E402
from proxy.analysis.report import AnalysisConfig  # noqa: E402
from proxy.config import load_models  # noqa: E402
from proxy.store import EpisodeStore  # noqa: E402


def main(config: str = "configs/analysis.yaml") -> None:
    cfg = AnalysisConfig.load(ROOT / config)
    df = load_frame(EpisodeStore(), load_models(), runs=cfg.runs, primary_judge=cfg.primary_judge, principal_model=cfg.principal_model)
    confirmatory = df if cfg.confirmatory_runs is None else df[df["run"].isin(cfg.confirmatory_runs) & (df["report_variant"] == "open")]
    confirmatory = confirmatory[~confirmatory["error"]]
    write_numbers(confirmatory, ROOT / "paper" / "numbers.tex", calibration={"good": 0.44, "mediocre": 0.24, "bad": 0.09})
    print("figures:", [p.name for p in paper_figures(confirmatory, ROOT / "paper" / "figures")])
    subprocess.run(["tectonic", "-X", "compile", "main.tex"], cwd=ROOT / "paper", check=True)
    print("built", ROOT / "paper" / "main.pdf")


if __name__ == "__main__":
    main(*sys.argv[1:])
