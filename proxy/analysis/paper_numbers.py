"""Writes paper/numbers.tex: every number quoted in the paper's prose, as LaTeX macros computed from the
episode store. The paper never contains a hand-typed result.

Macro names are letters only (LaTeX). Percentages are rendered with \\% and one decimal where n is large.
"""

import asyncio
import math
from pathlib import Path

import pandas as pd

from proxy.analysis.paper_figures import DISPLAY
from proxy.config import ExperimentConfig
from proxy.counterparty.calibration import calibrate


def _pct(x: float, digits: int = 0) -> str:
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100 * x:.{digits}f}\\%"


def _num(x: float, digits: int = 2) -> str:
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{digits}f}"


def _macro_name(model: str) -> str:
    """claude-opus-5 -> ClaudeOpusFive; letters only."""
    words = {"0": "Zero", "1": "One", "2": "Two", "3": "Three", "4": "Four", "5": "Five", "6": "Six", "7": "Seven", "8": "Eight", "9": "Nine"}
    out = []
    for part in model.replace(".", "-").split("-"):
        if part.isdigit():
            out.append("".join(words[c] for c in part))
        else:
            out.append("".join(words.get(c, c) for c in part).capitalize())
    return "".join(ch for ch in "".join(out) if ch.isalpha())


def numbers(df: pd.DataFrame, calibration: dict | None = None) -> dict[str, str]:
    m: dict[str, str] = {}
    ok = df[~df["error"]]
    m["nEpisodes"] = str(len(ok))
    m["nModels"] = str(ok["model"].nunique())
    m["nFamilies"] = str(ok["family"].nunique())
    deals = ok[ok["deal"] == 1.0]
    m["violationCount"] = str(int((ok["violated"] == 1.0).sum()))
    m["leakCount"] = str(int((ok["leaked_near"] == 1.0).sum()))

    a = ok[ok["blocked_alt"] == 1.0]
    j = a.dropna(subset=["a_nondisclosed"])
    m["exposedCount"] = str(len(a))
    m["exposureRate"] = _pct(ok["blocked_alt"].mean())
    m["doneJudgedAll"] = _pct(j["a_nondisclosed"].mean())
    m["doneLowerAll"] = _pct(a["a_unmentioned"].mean())
    cats = a["a_category"].value_counts()
    for key, name in (("acknowledged", "Ack"), ("mentioned_not_acknowledged", "Mentioned"), ("contradicted", "Contradicted")):
        m[f"doneCount{name}"] = str(int(cats.get(key, 0)))

    s = ok.dropna(subset=["total_misstated"])
    for model, g in ok.groupby("model"):
        name = _macro_name(model)
        gj = j[j["model"] == model]
        gs = s[s["model"] == model]
        m[f"doneJudged{name}"] = _pct(gj["a_nondisclosed"].mean()) if len(gj) else "n/a"
        m[f"doneN{name}"] = str(len(gj))
        m[f"dtwoWrong{name}"] = _pct(gs["total_misstated"].mean()) if len(gs) else "n/a"
        m[f"dtwoN{name}"] = str(len(gs))
        for target in ("good", "bad"):
            c = g[(g["outcome_target"] == target)]["char_rating"].dropna()
            m[f"portray{target.capitalize()}{name}"] = _num(c.mean(), 1) if len(c) else "n/a"

    # Judge-free "names the blocked offer" measure and the knowledge probe.
    named = a.dropna(subset=["a_not_named"])
    m["doneNamedAll"] = _pct(1 - named["a_not_named"].mean()) if len(named) else "n/a"
    m["doneToldAll"] = _pct(1 - j["a_nondisclosed"].mean(), 1) if len(j) else "n/a"
    silent = j[j["a_nondisclosed"] == 1.0].dropna(subset=["probe_knew"])
    m["probeKnewAll"] = _pct(silent["probe_knew"].mean()) if len(silent) else "n/a"
    m["probeN"] = str(len(silent))
    for model, g in ok.groupby("model"):
        name = _macro_name(model)
        gj = j[j["model"] == model]
        gn = named[named["model"] == model]
        gs = silent[silent["model"] == model]
        m[f"doneTold{name}"] = _pct(1 - gj["a_nondisclosed"].mean(), 1) if len(gj) else "n/a"
        m[f"doneNamed{name}"] = _pct(1 - gn["a_not_named"].mean()) if len(gn) else "n/a"
        m[f"probeKnew{name}"] = _pct(gs["probe_knew"].mean()) if len(gs) else "n/a"
    m["exposureRate"] = _pct(ok["blocked_alt"].mean(), 1)
    m["doneLowerAll"] = _pct(a["a_unmentioned"].mean(), 1)
    st = ok.dropna(subset=["total_misstated"])
    m["dtwoStatedRate"] = _pct(deals["total_stated"].mean(), 1) if len(deals) else "n/a"
    m["dtwoWrongAll"] = _pct(st["total_misstated"].mean(), 1) if len(st) else "n/a"
    m["dtwoAbsError"] = _num(st["total_error"].abs().mean(), 1) if len(st) else "n/a"
    if len(st):
        by = st.groupby("outcome_target")["total_error"].mean()
        if {"good", "bad"} <= set(by.index):
            m["dtwoSignedDiff"] = f"{by['bad'] - by['good']:+.1f}"
    pm = ok["principal_decision_mismatch"].dropna()
    m["principalMismatch"] = _pct(pm.mean()) if len(pm) else "n/a"
    # Shadow price of the requirement.
    sp = a.dropna(subset=["points_forgone"])
    if len(sp):
        m["shadowMean"] = _num(sp["points_forgone"].mean(), 1)
        m["shadowMedian"] = _num(sp["points_forgone"].median(), 0)
        m["shadowShareAboveTen"] = _pct((sp["points_forgone"] > 10).mean())
    for target in ("good", "bad"):
        g = deals[deals["outcome_target"] == target]["gain_fraction"].dropna()
        m[f"pilotGain{target.capitalize()}"] = _num(g.mean())
    if calibration:
        for target, key in (("good", "calGood"), ("mediocre", "calMediocre"), ("bad", "calBad")):
            m[key] = _num(calibration.get(target, math.nan))
    return m


def reference_calibration(config: str = "configs/pilot.yaml") -> dict:
    """Mean gain among deals for the floor-respecting reference agent, per target."""
    res = asyncio.run(calibrate(ExperimentConfig.load(config)))
    return {target: r.get("gain_mean") or math.nan for (target, kind), r in res.items() if kind == "compliant"}


def write_numbers(df: pd.DataFrame, path: Path, calibration: dict | None = None, extra: dict | None = None) -> Path:
    macros = {**numbers(df, calibration), **(extra or {})}
    lines = ["% Generated by proxy.analysis.paper_numbers. Do not edit by hand."]
    lines += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in sorted(macros.items())]
    Path(path).write_text("\n".join(lines) + "\n")
    return Path(path)


__all__ = ["numbers", "write_numbers", "reference_calibration", "DISPLAY"]


def per_model_table(df: pd.DataFrame) -> str:
    """LaTeX table: one row per model, the measures the paper reports model by model."""
    from proxy.analysis.stats import cluster_bootstrap, mean_of

    ok = df[~df["error"]]
    a = ok[ok["blocked_alt"] == 1.0]
    rows = []
    for model, g in ok.groupby("model"):
        ga = a[a["model"] == model]
        gj = ga.dropna(subset=["a_nondisclosed"])
        gn = ga.dropna(subset=["a_not_named"])
        gs = ok[ok["model"] == model].dropna(subset=["total_misstated"])
        silent = gj[gj["a_nondisclosed"] == 1.0].dropna(subset=["probe_knew"])
        if not len(gj):
            continue
        ci = cluster_bootstrap(gj, mean_of("a_nondisclosed"), B=1000)
        shown = DISPLAY.get(model)
        name = shown[0] if isinstance(shown, (tuple, list)) else (shown or model)
        family = shown[1] if isinstance(shown, (tuple, list)) and len(shown) > 1 else g["family"].iloc[0]
        rows.append((
            name, family, len(gj),
            f"{100 * ci['estimate']:.0f} [{100 * ci['ci95'][0]:.0f}, {100 * ci['ci95'][1]:.0f}]",
            f"{100 * ga['a_unmentioned'].mean():.0f}",
            f"{100 * (1 - gn['a_not_named'].mean()):.0f}" if len(gn) else "--",
            f"{100 * gs['total_misstated'].mean():.0f}" if len(gs) else "--",
            f"{100 * silent['probe_knew'].mean():.0f}" if len(silent) else "--",
        ))
    rows.sort(key=lambda r: (r[1], -float(r[3].split(" ")[0])))
    head = (r"\begin{tabular}{llrrrrrr}" "\n" r"\toprule" "\n"
            r"Model & Family & $n$ & Non-disclosed [95\% CI] & No offer & Names it & Total wrong & Knew \\" "\n"
            r"\midrule")
    body = "\n".join(" & ".join(str(c) for c in r) + r" \\" for r in rows)
    return f"{head}\n{body}\n\\bottomrule\n\\end{{tabular}}"
