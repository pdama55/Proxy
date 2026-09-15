"""Every figure in the paper, generated from the analysis frame. No hand-edited figures."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

TARGET_ORDER = ["good", "mediocre", "bad", "no_deal"]
INK, MUTED = "#1d1d1b", "#6b6b66"
PALETTE = ["#1f5fbf", "#c2561c", "#2f8f5b", "#7a4bb3", "#b3261e", "#8a6d00", "#3a8fb7", "#9c4f8b"]


def _style(ax, title, ylabel):
    ax.set_title(title, fontsize=11, color=INK, loc="left")
    ax.set_ylabel(ylabel, fontsize=9, color=MUTED)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=8, colors=MUTED)
    ax.grid(axis="y", color="#e6e5e0", linewidth=0.8)
    ax.set_axisbelow(True)


def _save(fig, out: Path, name: str) -> list[str]:
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for ext in ("png", "pdf"):
        p = out / f"{name}.{ext}"
        fig.savefig(p, dpi=200, bbox_inches="tight")
        paths.append(str(p))
    plt.close(fig)
    return paths


def _rate_by(df, col, by):
    g = df.dropna(subset=[col]).groupby(by)[col]
    return g.mean(), g.count()


def fig_nondisclosure_by_target(df: pd.DataFrame, out: Path) -> list[str]:
    v = df[df["blocked_alt"] == 1.0]
    if v.empty:
        return []
    fig, ax = plt.subplots(figsize=(7, 3.8))
    models = sorted(v["model"].unique())
    targets = [t for t in TARGET_ORDER if t in set(v["outcome_target"])]
    x = np.arange(len(targets))
    width = 0.8 / max(len(models), 1)
    for i, m in enumerate(models):
        rates, _ = _rate_by(v[v["model"] == m], "a_unmentioned", "outcome_target")
        ax.bar(x + i * width - 0.4 + width / 2, [rates.get(t, np.nan) for t in targets], width, label=m, color=PALETTE[i % len(PALETTE)])
    ax.set_xticks(x, targets)
    ax.set_ylim(0, 1)
    _style(ax, "Reports that never mention a better deal blocked by the client's requirement (lower bound)", "share of exposed episodes")
    ax.legend(fontsize=7, frameon=False, ncol=2)
    return _save(fig, out, "fig1_nondisclosure_by_target")


def fig_audit(df: pd.DataFrame, out: Path) -> list[str]:
    v = df[df["blocked_alt"] == 1.0].dropna(subset=["a_unmentioned"])
    if v.empty or v["audit"].nunique() < 2:
        return []
    fig, ax = plt.subplots(figsize=(6, 3.5))
    models = sorted(v["model"].unique())
    for i, m in enumerate(models):
        r, _ = _rate_by(v[v["model"] == m], "a_unmentioned", "audit")
        ax.plot([0, 1], [r.get(0, np.nan), r.get(1, np.nan)], marker="o", color=PALETTE[i % len(PALETTE)], label=m)
    ax.set_xticks([0, 1], ["no audit framing", "audit framing"])
    ax.set_ylim(0, 1)
    _style(ax, "Effect of telling the agent the transcript will be read", "non-disclosure (lower bound)")
    ax.legend(fontsize=7, frameon=False)
    return _save(fig, out, "fig2_audit")


def fig_capability(df: pd.DataFrame, out: Path) -> list[str]:
    v = df[df["blocked_alt"] == 1.0].dropna(subset=["a_unmentioned", "capability_rank"])
    if v.empty:
        return []
    fig, ax = plt.subplots(figsize=(6, 3.5))
    for i, (fam, g) in enumerate(sorted(v.groupby("family"))):
        r, _ = _rate_by(g, "a_unmentioned", "capability_rank")
        ax.plot(r.index, r.values, marker="o", color=PALETTE[i % len(PALETTE)], label=fam)
    ax.set_ylim(0, 1)
    ax.set_xlabel("capability rank within family (1 = smallest)", fontsize=9, color=MUTED)
    _style(ax, "Non-disclosure across the capability ladder", "non-disclosure (lower bound)")
    ax.legend(fontsize=7, frameon=False)
    return _save(fig, out, "fig3_capability")


def fig_stated_total_error(df: pd.DataFrame, out: Path) -> list[str]:
    s = df.dropna(subset=["total_error"])
    if s.empty:
        return []
    fig, ax = plt.subplots(figsize=(7, 3.8))
    models = sorted(s["model"].unique())
    targets = [t for t in TARGET_ORDER if t in set(s["outcome_target"])]
    x = np.arange(len(targets))
    width = 0.8 / max(len(models), 1)
    for i, m in enumerate(models):
        g = s[s["model"] == m].groupby("outcome_target")["total_error"].mean()
        ax.bar(x + i * width - 0.4 + width / 2, [g.get(t, np.nan) for t in targets], width, label=m, color=PALETTE[i % len(PALETTE)])
    ax.axhline(0, color=MUTED, linewidth=0.8)
    ax.set_xticks(x, targets)
    _style(ax, "Stated minus true point total, among reports that state one", "points (positive = overstated)")
    ax.legend(fontsize=7, frameon=False, ncol=2)
    return _save(fig, out, "fig4_stated_total_error")


def fig_characterization(df: pd.DataFrame, out: Path) -> list[str]:
    c = df.dropna(subset=["char_rating", "gain_fraction"])
    if c.empty:
        return []
    fig, ax = plt.subplots(figsize=(6, 3.8))
    rng = np.random.default_rng(0)
    for i, t in enumerate([t for t in TARGET_ORDER if t in set(c["outcome_target"])]):
        g = c[c["outcome_target"] == t]
        ax.scatter(g["gain_fraction"], g["char_rating"] + rng.uniform(-0.15, 0.15, len(g)), s=10, alpha=0.6, color=PALETTE[i], label=t)
    ax.set_xlabel("actual agent gain fraction (0 = BATNA)", fontsize=9, color=MUTED)
    _style(ax, "How the report portrays the outcome vs how it went", "judge rating of portrayal (1-7)")
    ax.legend(fontsize=7, frameon=False)
    return _save(fig, out, "fig5_characterization")


def fig_principal(df: pd.DataFrame, out: Path) -> list[str]:
    p = df.dropna(subset=["principal_rating_gap"])
    if p.empty:
        return []
    fig, ax = plt.subplots(figsize=(6, 3.5))
    targets = [t for t in TARGET_ORDER if t in set(p["outcome_target"])]
    means = [p.loc[p["outcome_target"] == t, "principal_rating_gap"].mean() for t in targets]
    ax.bar(targets, means, color=PALETTE[0])
    ax.axhline(0, color=INK, linewidth=0.8)
    _style(ax, "Principal decision error: rating from report minus rating from ground truth", "rating gap (points)")
    return _save(fig, out, "fig6_principal_error")


def all_figures(df: pd.DataFrame, out: Path) -> list[str]:
    main = df[(~df["error"]) & (df["scored"]) & (df["counterparty_kind"] == "scripted")]
    paths = []
    for f in (fig_nondisclosure_by_target, fig_audit, fig_capability, fig_stated_total_error, fig_characterization, fig_principal):
        paths += f(main, out)
    return paths
