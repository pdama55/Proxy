"""Publication figures for the paper, generated from the analysis frame. Vector PDF, print (light) only.

Visual system: one sans face, hairline solid gridlines one step off the surface, thin marks, dots with a
surface-colored ring, and categorical hues from the validated reference palette in fixed order
(slot 1 blue, slot 2 orange, slot 3 aqua). Text never wears a series color. Every figure with two or more
series carries a legend; single-series figures are named by their caption.
"""

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

SURFACE = "#ffffff"
GRID = "#e8e7e3"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#8a8984"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]

DISPLAY = {
    "claude-fable-5-1": ("Claude Fable 5.1", "Anthropic", 4),
    "claude-opus-5": ("Claude Opus 5", "Anthropic", 3),
    "claude-sonnet-5": ("Claude Sonnet 5", "Anthropic", 2),
    "claude-haiku-4-5": ("Claude Haiku 4.5", "Anthropic", 1),
    "gpt-6-astra": ("GPT-6 Astra", "OpenAI", 3),
    "gpt-5.6-sol": ("GPT-5.6 Sol", "OpenAI", 2),
    "gpt-5.6-luna": ("GPT-5.6 Luna", "OpenAI", 1),
    "gemini-3.1-pro": ("Gemini 3.1 Pro", "Google", 3),
    "gemini-3.8-flash": ("Gemini 3.8 Flash", "Google", 2),
    "gemini-3.5-flash-lite": ("Gemini 3.5 Flash-Lite", "Google", 1),
    "grok-4.6": ("Grok 4.6", "xAI", 3),
    "deepseek-v4-pro-azure": ("DeepSeek V4 Pro", "DeepSeek", 3),
    "llama-4-maverick": ("Llama 4 Maverick", "Meta", 2),
    "mistral-large-3": ("Mistral Large 3", "Mistral", 3),
    "qwen3.5-397b-a17b": ("Qwen3.5 397B", "Qwen", 5),
    "qwen3.5-122b-a10b": ("Qwen3.5 122B", "Qwen", 4),
    "qwen3.5-35b-a3b": ("Qwen3.5 35B", "Qwen", 3),
    "qwen3.5-27b": ("Qwen3.5 27B", "Qwen", 2),
    "qwen3.5-9b": ("Qwen3.5 9B", "Qwen", 1),
}
FAMILY_ORDER = ["Anthropic", "OpenAI", "Google", "xAI", "DeepSeek", "Meta", "Mistral", "Qwen"]


def _style():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 8,
        "axes.edgecolor": GRID,
        "axes.linewidth": 0.8,
        "axes.labelcolor": INK_2,
        "axes.titlecolor": INK,
        "xtick.color": INK_2,
        "ytick.color": INK,
        "xtick.major.size": 0,
        "ytick.major.size": 0,
        "legend.frameon": False,
        "pdf.fonttype": 42,
        "savefig.facecolor": SURFACE,
    })


def _axes(ax, grid_axis="x"):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.8, linestyle="-")
    ax.set_axisbelow(True)


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (math.nan, math.nan)
    p = k / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, mid - half), min(1.0, mid + half))


def model_order(models) -> list[str]:
    def key(m):
        name, fam, rank = DISPLAY.get(m, (m, "Other", 0))
        return (FAMILY_ORDER.index(fam) if fam in FAMILY_ORDER else 99, -rank, name)

    return sorted(set(models), key=key)


def _label(m: str) -> str:
    return DISPLAY.get(m, (m,))[0]


def _dot(ax, x, y, color, size=34, marker="o", zorder=3, label=None, hollow=False):
    ax.scatter(x, y, s=size, marker=marker, color=SURFACE if hollow else color, edgecolors=color if hollow else SURFACE,
               linewidths=1.6 if hollow else 1.4, zorder=zorder, label=label)


def _family_bands(ax, order):
    """Light separators and family names between model groups on a categorical y axis."""
    fams = [DISPLAY.get(m, (m, "Other", 0))[1] for m in order]
    start = 0
    for i in range(1, len(order) + 1):
        if i == len(order) or fams[i] != fams[start]:
            if i < len(order):
                ax.axhline(i - 0.5, color=GRID, linewidth=0.8, zorder=0)
            ax.text(1.01, (start + i - 1) / 2, fams[start], transform=ax.get_yaxis_transform(), va="center", ha="left",
                    fontsize=7, color=MUTED)
            start = i


def fig_d1_by_model(df: pd.DataFrame, out: Path) -> Path | None:
    a = df[(df["blocked_alt"] == 1.0)]
    judged = a.dropna(subset=["a_nondisclosed"])
    if judged.empty:
        return None
    order = model_order(judged["model"])
    fig, ax = plt.subplots(figsize=(5.4, 0.34 * len(order) + 0.9))
    _axes(ax)
    for i, m in enumerate(order):
        g = judged[judged["model"] == m]
        k, n = int(g["a_nondisclosed"].sum()), len(g)
        lo, hi = wilson(k, n)
        ax.plot([lo, hi], [i, i], color=SERIES[0], linewidth=2, solid_capstyle="round", zorder=2, alpha=0.35)
        _dot(ax, k / n, i, SERIES[0], label="Judged: report does not convey the better deal" if i == 0 else None)
        lb = a[a["model"] == m]["a_unmentioned"].dropna()
        if len(lb):
            _dot(ax, lb.mean(), i, SERIES[1], size=26, marker="D", hollow=True,
                 label="Lower bound: report never mentions any other offer" if i == 0 else None)
        ax.text(1.0, i, f"n={n}", transform=ax.get_yaxis_transform(), va="center", ha="right", fontsize=6.5, color=MUTED)
    ax.set_yticks(range(len(order)), [_label(m) for m in order])
    ax.set_ylim(len(order) - 0.5, -0.5)
    ax.set_xlim(-0.02, 1.08)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0], ["0%", "25%", "50%", "75%", "100%"])
    ax.set_xlabel("Share of exposed episodes", labelpad=6)
    _family_bands(ax, order)
    ax.legend(loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=1, fontsize=7, handletextpad=0.4, labelcolor=INK_2)
    return _save(fig, out, "d1_by_model")


def fig_d2_errors(df: pd.DataFrame, out: Path) -> Path | None:
    s = df.dropna(subset=["total_error"])
    if s.empty:
        return None
    order = model_order(df.dropna(subset=["total_stated"])["model"])
    order = [m for m in order if (df[(df["model"] == m)]["total_stated"] == 1.0).any()]
    fig, ax = plt.subplots(figsize=(5.4, 0.34 * len(order) + 0.8))
    _axes(ax)
    rng = np.random.default_rng(0)
    ax.axvline(0, color=INK_2, linewidth=0.8, zorder=1)
    for i, m in enumerate(order):
        g = s[s["model"] == m]["total_error"].to_numpy()
        if len(g):
            _dot(ax, g, i + rng.uniform(-0.18, 0.18, len(g)), SERIES[0], size=22)
        stated = df[(df["model"] == m) & df["total_misstated"].notna()]
        rate = stated["total_misstated"].mean() if len(stated) else math.nan
        txt = "—" if math.isnan(rate) else f"{100 * rate:.0f}% wrong ({int(stated['total_misstated'].sum())}/{len(stated)})"
        ax.text(1.01, i, txt, transform=ax.get_yaxis_transform(), va="center", ha="left", fontsize=6.5, color=INK_2)
    ax.set_yticks(range(len(order)), [_label(m) for m in order])
    ax.set_ylim(len(order) - 0.5, -0.5)
    lim = max(10, float(np.nanmax(np.abs(s["total_error"]))) + 3)
    ax.set_xlim(-lim, lim)
    ax.set_xlabel("Stated minus true point total (points)", labelpad=6)
    return _save(fig, out, "d2_errors")


def fig_portrayal(df: pd.DataFrame, out: Path) -> Path | None:
    c = df.dropna(subset=["char_rating"])
    c = c[c["outcome_target"].isin(["good", "bad"])]
    if c.empty:
        return None
    order = model_order(c["model"])
    fig, ax = plt.subplots(figsize=(5.4, 0.34 * len(order) + 0.9))
    _axes(ax)
    for i, m in enumerate(order):
        g = c[c["model"] == m].groupby("outcome_target")["char_rating"].mean()
        if {"good", "bad"} <= set(g.index):
            ax.plot([g["bad"], g["good"]], [i, i], color=GRID, linewidth=2, zorder=1, solid_capstyle="round")
        if "bad" in g:
            _dot(ax, g["bad"], i, SERIES[1], label="Bad outcome (mean gain 0.08)" if i == 0 else None)
        if "good" in g:
            _dot(ax, g["good"], i, SERIES[0], label="Good outcome (mean gain 0.43)" if i == 0 else None)
    ax.set_yticks(range(len(order)), [_label(m) for m in order])
    ax.set_ylim(len(order) - 0.5, -0.5)
    ax.set_xlim(1, 7)
    ax.set_xticks(range(1, 8), ["1\nvery bad", "2", "3", "4\nmixed", "5", "6", "7\nvery good"])
    ax.set_xlabel("How good an outcome the report portrays (judge rating)", labelpad=6)
    _family_bands(ax, order)
    ax.legend(loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=2, fontsize=7, handletextpad=0.3, labelcolor=INK_2)
    return _save(fig, out, "portrayal")


def fig_audit(df: pd.DataFrame, out: Path) -> Path | None:
    a = df[(df["blocked_alt"] == 1.0)].dropna(subset=["a_nondisclosed"])
    a = a[a.groupby("model")["audit"].transform("nunique") == 2]
    if a.empty:
        return None
    order = model_order(a["model"])
    fig, ax = plt.subplots(figsize=(5.4, 0.34 * len(order) + 0.9))
    _axes(ax)
    for i, m in enumerate(order):
        g = a[a["model"] == m].groupby("audit")["a_nondisclosed"].mean()
        ax.plot([g[0], g[1]], [i, i], color=GRID, linewidth=2, zorder=1, solid_capstyle="round")
        _dot(ax, g[0], i, SERIES[1], label="No audit sentence" if i == 0 else None)
        _dot(ax, g[1], i, SERIES[0], label="“I will read the full transcript”" if i == 0 else None)
    ax.set_yticks(range(len(order)), [_label(m) for m in order])
    ax.set_ylim(len(order) - 0.5, -0.5)
    ax.set_xlim(-0.02, 1.02)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0], ["0%", "25%", "50%", "75%", "100%"])
    ax.set_xlabel("Share of exposed reports that do not convey the better deal (judged)", labelpad=6)
    _family_bands(ax, order)
    ax.legend(loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=2, fontsize=7, handletextpad=0.3, labelcolor=INK_2)
    return _save(fig, out, "audit")


def fig_knowledge(df: pd.DataFrame, out: Path) -> Path | None:
    """Among exposed episodes: what the report conveyed, and whether the agent could name the offer when asked."""
    a = df[(df["blocked_alt"] == 1.0)].dropna(subset=["a_nondisclosed"])
    if a.empty or a["probe_knew"].notna().sum() == 0:
        return None
    order = model_order(a["model"])
    fig, ax = plt.subplots(figsize=(5.4, 0.34 * len(order) + 0.9))
    _axes(ax)
    for i, m in enumerate(order):
        g = a[a["model"] == m]
        told = 1 - g["a_nondisclosed"].mean()
        knew = g[g["a_nondisclosed"] == 1.0]["probe_knew"].dropna()
        ax.barh(i, told, height=0.42, color=SERIES[2], zorder=2)
        if len(knew):
            ax.barh(i + 0.0, -knew.mean(), height=0.42, color=SERIES[1], zorder=2, left=0)
    ax.axvline(0, color=INK_2, linewidth=0.8, zorder=3)
    ax.set_yticks(range(len(order)), [_label(m) for m in order])
    ax.set_ylim(len(order) - 0.5, -0.5)
    ax.set_xlim(-1.05, 1.05)
    ax.set_xticks([-1, -0.5, 0, 0.5, 1], ["100%", "50%", "0", "50%", "100%"])
    ax.set_xlabel("share of exposed episodes", labelpad=6)
    ax.text(-0.5, -0.9, "knew when asked, among silent reports", ha="center", va="bottom", fontsize=7.5, color=SERIES[1])
    ax.text(0.5, -0.9, "told the client unprompted", ha="center", va="bottom", fontsize=7.5, color=SERIES[2])
    _family_bands(ax, order)
    return _save(fig, out, "knowledge_vs_disclosure")


def fig_interventions(df: pd.DataFrame, out: Path) -> Path | None:
    """Judged non-disclosure under each report prompt, on the same negotiations."""
    a = df[(df["blocked_alt"] == 1.0)].dropna(subset=["a_nondisclosed"])
    variants = [v for v in ("open", "tradeoffs", "norm") if v in set(a["report_variant"])]
    if len(variants) < 2:
        return None
    order = model_order(a[a["report_variant"] == "open"]["model"])
    fig, ax = plt.subplots(figsize=(5.4, 0.34 * len(order) + 1.0))
    _axes(ax)
    labels = {"open": "``How did it go?''", "tradeoffs": "client asks about turned-down terms", "norm": "deployer instruction"}
    for i, m in enumerate(order):
        g = a[a["model"] == m]
        xs = [g[g["report_variant"] == v]["a_nondisclosed"].mean() for v in variants]
        xs = [x for x in xs if x == x]
        if len(xs) > 1:
            ax.plot([min(xs), max(xs)], [i, i], color=GRID, linewidth=2, zorder=1, solid_capstyle="round")
        for j, v in enumerate(variants):
            val = g[g["report_variant"] == v]["a_nondisclosed"].mean()
            if val == val:
                _dot(ax, val, i, SERIES[j % len(SERIES)])
    handles = [plt.Line2D([], [], marker="o", linestyle="", markersize=5, color=SERIES[j % len(SERIES)],
                          markeredgecolor=SURFACE, markeredgewidth=1.2, label=labels.get(v, v))
               for j, v in enumerate(variants)]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=1, fontsize=7,
              handletextpad=0.4, labelcolor=INK_2)
    ax.set_yticks(range(len(order)), [_label(m) for m in order])
    ax.set_ylim(len(order) - 0.5, -0.5)
    ax.set_xlim(-0.02, 1.02)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0], ["0%", "25%", "50%", "75%", "100%"])
    ax.set_xlabel("Reports that do not convey the blocked better deal (judged)", labelpad=6)
    _family_bands(ax, order)
    return _save(fig, out, "interventions")


def fig_stakes(df: pd.DataFrame, out: Path) -> Path | None:
    """Does disclosure rise with what the requirement cost the client? Binned by points forgone."""
    a = df[(df["blocked_alt"] == 1.0)].dropna(subset=["a_nondisclosed", "points_forgone"])
    if len(a) < 40:
        return None
    edges = np.quantile(a["points_forgone"], [0, 0.25, 0.5, 0.75, 1.0])
    edges = np.unique(np.round(edges).astype(int))
    if len(edges) < 3:
        return None
    fig, ax = plt.subplots(figsize=(5.4, 3.0))
    _axes(ax, grid_axis="y")
    models = model_order(a["model"])[:4]
    for i, m in enumerate(models):
        g = a[a["model"] == m].copy()
        g["bin"] = pd.cut(g["points_forgone"], edges, include_lowest=True)
        by = g.groupby("bin", observed=True)["a_nondisclosed"].agg(["mean", "size"])
        centers = [iv.mid for iv in by.index]
        ax.plot(centers, by["mean"], marker="o", markersize=5, linewidth=2, color=SERIES[i % len(SERIES)],
                markeredgecolor=SURFACE, markeredgewidth=1.4, label=_label(m))
    ax.set_ylim(-0.02, 1.02)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0], ["0%", "25%", "50%", "75%", "100%"])
    ax.set_xlabel("Points the client's requirement cost them", labelpad=6)
    ax.set_ylabel("does not convey it (judged)")
    ax.legend(fontsize=7, frameon=False, ncol=2)
    return _save(fig, out, "stakes")


def _save(fig, out: Path, name: str) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    path = out / f"{name}.pdf"
    fig.savefig(path, bbox_inches="tight", pad_inches=0.03)
    fig.savefig(out / f"{name}.png", dpi=220, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    return path


def paper_figures(df: pd.DataFrame, out: Path) -> list[Path]:
    """Every figure but the intervention comparison describes the open report ("How did it go?"); report
    variants are a separate experiment and must never be pooled into the headline rates."""
    _style()
    open_only = df[df["report_variant"] == "open"] if "report_variant" in df else df
    made = [f(open_only, Path(out)) for f in (fig_d1_by_model, fig_d2_errors, fig_portrayal, fig_audit, fig_knowledge, fig_stakes)]
    made.append(fig_interventions(df, Path(out)))
    return [p for p in made if p is not None]
