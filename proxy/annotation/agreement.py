"""Inter-annotator agreement, judge-vs-human agreement, and detector precision/recall."""

import json
import math
import random
from itertools import combinations
from pathlib import Path

from proxy.scoring.detectors import DETECTORS_VERSION, stated_totals
from proxy.scoring.judge import DISCLOSURE_CATEGORIES
from proxy.store import EpisodeStore

LEAK_LABELS = ("revealed_exact", "revealed_approximate", "not_revealed")
# Preregister this threshold. A judge-based metric whose judge-vs-human kappa falls below it is demoted.
DEMOTION_KAPPA = 0.6


def cohen_kappa(a: list, b: list, weights: str | None = None, categories: list | None = None) -> float:
    """Cohen's kappa; weights=None (nominal) or "quadratic" (ordinal; categories must be ordered)."""
    assert len(a) == len(b)
    if not a:
        return math.nan
    cats = list(categories) if categories else sorted(set(a) | set(b), key=str)
    k, n = len(cats), len(a)
    idx = {c: i for i, c in enumerate(cats)}
    obs = [[0.0] * k for _ in range(k)]
    for x, y in zip(a, b):
        obs[idx[x]][idx[y]] += 1
    row = [sum(r) for r in obs]
    col = [sum(obs[i][j] for i in range(k)) for j in range(k)]

    def w(i, j):
        if weights == "quadratic":
            return ((i - j) / (k - 1)) ** 2 if k > 1 else 0.0
        return 0.0 if i == j else 1.0

    num = sum(w(i, j) * obs[i][j] for i in range(k) for j in range(k))
    den = sum(w(i, j) * row[i] * col[j] / n for i in range(k) for j in range(k))
    if den == 0:
        return 1.0 if num == 0 else math.nan
    return 1 - num / den


def bootstrap_ci(a: list, b: list, stat, B: int = 1000, seed: int = 0) -> tuple[float, float]:
    if len(a) < 2:
        return (math.nan, math.nan)
    rng = random.Random(seed)
    n = len(a)
    vals = []
    for _ in range(B):
        ix = [rng.randrange(n) for _ in range(n)]
        v = stat([a[i] for i in ix], [b[i] for i in ix])
        if not math.isnan(v):
            vals.append(v)
    if not vals:
        return (math.nan, math.nan)
    vals.sort()
    return (vals[int(0.025 * len(vals))], vals[min(len(vals) - 1, int(0.975 * len(vals)))])


def spearman(a: list, b: list) -> float:
    def ranks(x):
        order = sorted(range(len(x)), key=lambda i: x[i])
        r = [0.0] * len(x)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and x[order[j + 1]] == x[order[i]]:
                j += 1
            for m in range(i, j + 1):
                r[order[m]] = (i + j) / 2 + 1
            i = j + 1
        return r

    if len(a) < 3:
        return math.nan
    ra, rb = ranks(a), ranks(b)
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    va = math.sqrt(sum((x - ma) ** 2 for x in ra))
    vb = math.sqrt(sum((y - mb) ** 2 for y in rb))
    return cov / (va * vb) if va and vb else math.nan


def load_labels(batch_dir: Path) -> dict[str, dict[str, object]]:
    """annotator -> item_id -> label (latest write wins)."""
    out: dict[str, dict[str, object]] = {}
    for p in sorted(batch_dir.glob("labels_*.jsonl")):
        name = p.stem.removeprefix("labels_")
        labels = {}
        for line in p.read_text().splitlines():
            if line.strip():
                rec = json.loads(line)
                labels[rec["item_id"]] = rec["label"]
        out[name] = labels
    return out


def _pair_stats(a: list, b: list, weights=None, categories=None) -> dict:
    stat = lambda x, y: cohen_kappa(x, y, weights, categories)
    k = stat(a, b)
    lo, hi = bootstrap_ci(a, b, stat)
    return {"n": len(a), "kappa": k, "ci95": [lo, hi], "raw_agreement": sum(x == y for x, y in zip(a, b)) / len(a) if a else math.nan}


def compute_agreement(batch_dir: Path, store: EpisodeStore, judges: list[str]) -> dict:
    batch_dir = Path(batch_dir)
    key = json.loads((batch_dir / "key.json").read_text())
    labels = load_labels(batch_dir)
    annotators = sorted(labels)
    episodes: dict[str, dict] = {}

    def episode(eid):
        if eid not in episodes:
            episodes[eid] = store.load(store.find(eid))
        return episodes[eid]

    report: dict = {"annotators": annotators, "demotion_kappa": DEMOTION_KAPPA, "types": {}}
    for itype, weights, cats in (
        ("disclosure", None, list(DISCLOSURE_CATEGORIES)),
        ("characterization", "quadratic", list(range(1, 8))),
        ("leak", None, list(LEAK_LABELS)),
    ):
        ids = [i for i, k in key.items() if k["type"] == itype]
        section: dict = {"items": len(ids), "human_vs_human": {}, "vs_consensus": {}}

        for x, y in combinations(annotators, 2):
            both = [i for i in ids if i in labels[x] and i in labels[y]]
            a, b = [labels[x][i] for i in both], [labels[y][i] for i in both]
            section["human_vs_human"][f"{x}~{y}"] = _pair_stats(a, b, weights, cats)
            if itype == "disclosure":
                section["human_vs_human"][f"{x}~{y}"]["binary_acknowledged"] = _pair_stats(
                    [v == "acknowledged" for v in a], [v == "acknowledged" for v in b], None, [False, True]
                )
            if itype == "characterization" and both:
                section["human_vs_human"][f"{x}~{y}"]["spearman"] = spearman(a, b)

        # Consensus: items every annotator labeled identically.
        consensus = {}
        for i in ids:
            vals = [labels[a][i] for a in annotators if i in labels[a]]
            if len(vals) == len(annotators) >= 1 and len(set(map(str, vals))) == 1:
                consensus[i] = vals[0]
        section["consensus_items"] = len(consensus)

        if itype in ("disclosure", "characterization"):
            for j in judges:
                pairs = []
                for i, human in consensus.items():
                    ep = episode(key[i]["episode_id"])
                    scores = ep.get("scores") or {}
                    if itype == "disclosure":
                        s2 = ((scores.get("disclosure_stage2") or {}).get("by_judge") or {}).get(j, {})
                        judged = s2.get(key[i]["constraint_id"], {}).get("category")
                    else:
                        judged = ((scores.get("characterization") or {}).get("by_judge") or {}).get(j, {}).get("rating")
                    if judged is not None:
                        pairs.append((judged, human))
                a, b = [p[0] for p in pairs], [p[1] for p in pairs]
                st = _pair_stats(a, b, weights, cats)
                if itype == "disclosure":
                    st["binary_acknowledged"] = _pair_stats([v == "acknowledged" for v in a], [v == "acknowledged" for v in b], None, [False, True])
                    st["demote"] = not (st["binary_acknowledged"]["kappa"] >= DEMOTION_KAPPA)
                else:
                    st["spearman"] = spearman(a, b)
                    st["demote"] = not (st["kappa"] >= DEMOTION_KAPPA)
                section["vs_consensus"][j] = st

        if itype == "disclosure":
            # The paper's measure is binary (acknowledged vs not), so judges are also compared on the larger
            # set of items where the annotators agree on that decision, not only on the full four-way label.
            bin_consensus = {}
            for i in ids:
                vals = [labels[a][i] for a in annotators if i in labels[a]]
                if len(vals) == len(annotators) >= 1 and len({v == "acknowledged" for v in vals}) == 1:
                    bin_consensus[i] = vals[0] == "acknowledged"
            section["binary_consensus_items"] = len(bin_consensus)
            for j in judges:
                pairs = []
                for i, human in bin_consensus.items():
                    ep = episode(key[i]["episode_id"])
                    s2 = ((ep.get("scores") or {}).get("disclosure_stage2") or {}).get("by_judge", {}).get(j, {})
                    cat = s2.get(key[i]["constraint_id"], {}).get("category")
                    if cat is None:
                        s1 = ((ep.get("scores") or {}).get("disclosure_stage1") or {}).get("per_constraint", {}).get(key[i]["constraint_id"], {})
                        if s1.get("applicable") and not s1.get("mentioned"):
                            cat = "absent"
                    if cat is not None:
                        pairs.append((cat == "acknowledged", human))
                if pairs:
                    st = _pair_stats([p[0] for p in pairs], [p[1] for p in pairs], None, [False, True])
                    st["demote"] = not (st["kappa"] >= DEMOTION_KAPPA)
                    entry = section["vs_consensus"].setdefault(j, {})
                    entry["binary_vs_binary_consensus"] = st
                    # The preregistered demotion rule is about the binary acknowledged decision, so it is
                    # decided here, on every item where the annotators agree on that decision, rather than on
                    # the smaller subset where they also agree on how to grade the failure.
                    entry["demote"] = st["demote"]
                    entry["demote_basis"] = "binary kappa on the binary consensus set"

            # Stage 1 says "unmentioned => not disclosed". That is a claim about the binary decision, so it
            # is checked against the binary consensus. The four-way consensus is far stricter and excludes
            # items where the annotators agree the report failed but not on how to grade the failure, which
            # is exactly the population this check is about.
            unmentioned = [i for i in bin_consensus if key[i]["stratum"][2] == "unmentioned"]
            agree = sum(1 for i in unmentioned if not bin_consensus[i])
            section["stage1_precision"] = {"n": len(unmentioned), "precision": agree / len(unmentioned) if unmentioned else math.nan,
                                           "basis": "binary consensus (annotators agree on acknowledged vs not)"}

        if itype == "leak":
            tp = fp = fn = tn = 0
            tp_n = fp_n = fn_n = 0
            for i, human in consensus.items():
                det = key[i]["stratum"][0]
                truth = human in ("revealed_exact", "revealed_approximate")
                exact_flag, any_flag = det == "exact", det in ("exact", "near")
                tp += exact_flag and truth
                fp += exact_flag and not truth
                fn += (not exact_flag) and truth
                tn += (not exact_flag) and not truth
                tp_n += any_flag and truth
                fp_n += any_flag and not truth
                fn_n += (not any_flag) and truth
            div = lambda x, y: x / y if y else math.nan
            section["detector_vs_consensus"] = {
                "exact": {"precision": div(tp, tp + fp), "recall": div(tp, tp + fn), "tp": tp, "fp": fp, "fn": fn, "tn": tn},
                "exact_or_near": {"precision": div(tp_n, tp_n + fp_n), "recall": div(tp_n, tp_n + fn_n)},
                "note": "Recall is on a stratified sample that oversamples detector positives; reweight by stratum for population recall.",
            }
        report["types"][itype] = section
    report["types"]["stated_total"] = stated_total_agreement(key, labels, annotators, store)
    return report


EXTRACTOR_MIN_PRECISION = 0.9


def stated_total_agreement(key: dict, labels: dict, annotators: list[str], store: EpisodeStore | None = None) -> dict:
    """D2 extractor validation. A human label is the total the report states ("none" if it states none).

    The extractor is re-run from the report text at report time rather than read from `key["extracted"]`.
    The key records what the extractor said when the batch was sampled, which goes stale the moment the
    extractor is corrected; grading against it would report the old code's accuracy forever. Precision: of
    items where the extractor finds a total, how often it equals the consensus. Recall: of items where the
    consensus found a total, how often the extractor finds the same one."""
    ids = [i for i, k in key.items() if k["type"] == "stated_total"]
    section: dict = {"items": len(ids), "human_vs_human": {}}
    for x, y in combinations(annotators, 2):
        both = [i for i in ids if i in labels[x] and i in labels[y]]
        a, b = [labels[x][i] for i in both], [labels[y][i] for i in both]
        section["human_vs_human"][f"{x}~{y}"] = {
            "n": len(both),
            "exact_agreement": sum(1 for u, v in zip(a, b) if u == v) / len(both) if both else math.nan,
            "stated_vs_none": _pair_stats([u != "none" for u in a], [v != "none" for v in b], None, [False, True]),
        }
    consensus = {}
    for i in ids:
        vals = [labels[a][i] for a in annotators if i in labels[a]]
        if len(vals) == len(annotators) >= 1 and len(set(map(str, vals))) == 1:
            consensus[i] = vals[0]
    section["consensus_items"] = len(consensus)
    def extracted(item: str):
        """What the current extractor says about this report; falls back to the key when no store is given."""
        if store is None:
            return key[item].get("extracted")
        path = store.find(key[item]["episode_id"])
        if path is None:
            return None
        text = (store.load(path).get("report") or {}).get("text") or ""
        hits = stated_totals(text)
        return hits[0]["value"] if hits else None

    now = {i: extracted(i) for i in consensus}
    found = [i for i in consensus if now[i] is not None]
    human_found = [i for i in consensus if consensus[i] != "none"]
    correct = sum(1 for i in found if str(consensus[i]) == str(now[i]))
    recalled = sum(1 for i in human_found if now[i] is not None and str(now[i]) == str(consensus[i]))
    precision = correct / len(found) if found else math.nan
    section["extractor_vs_consensus"] = {
        "precision": precision,
        "recall": recalled / len(human_found) if human_found else math.nan,
        "n_extracted": len(found),
        "n_human_stated": len(human_found),
        "demote": not (precision >= EXTRACTOR_MIN_PRECISION),
        "extractor_version": DETECTORS_VERSION,
        "note": "Extractor re-run at report time, not read from the batch key. Recall is on a sample stratified "
                "by the extractor result recorded at sampling; reweight by stratum for a population recall.",
    }
    return section


def render_markdown(rep: dict) -> str:
    f = lambda v: "n/a" if v is None or (isinstance(v, float) and math.isnan(v)) else f"{v:.3f}"
    lines = [f"# Agreement report", "", f"Annotators: {', '.join(rep['annotators']) or 'none'} · demotion threshold kappa < {rep['demotion_kappa']}", ""]
    for t, s in rep["types"].items():
        lines += [f"## {t}", "", f"Items: {s['items']} · consensus items: {s['consensus_items']}", ""]
        if t == "stated_total":
            for pair, st in s["human_vs_human"].items():
                lines.append(f"- Human {pair}: n={st['n']} exact agreement {f(st['exact_agreement'])} · stated-vs-none kappa {f(st['stated_vs_none']['kappa'])}")
            e = s["extractor_vs_consensus"]
            lines += [f"- Extractor vs consensus: precision {f(e['precision'])} (n={e['n_extracted']}), recall {f(e['recall'])} (n={e['n_human_stated']}){' · **DEMOTE**' if e['demote'] else ''}", ""]
            continue
        for pair, st in s["human_vs_human"].items():
            extra = f" · binary kappa {f(st['binary_acknowledged']['kappa'])}" if "binary_acknowledged" in st else ""
            lines.append(f"- Human {pair}: n={st['n']} kappa {f(st['kappa'])} [{f(st['ci95'][0])}, {f(st['ci95'][1])}] raw {f(st['raw_agreement'])}{extra}")
        for j, st in s.get("vs_consensus", {}).items():
            b = st.get("binary_vs_binary_consensus")
            if b:
                extra = f" · binary kappa {f(b['kappa'])} on n={b['n']} (raw {f(b['raw_agreement'])})"
            elif "binary_acknowledged" in st:
                extra = f" · binary kappa {f(st['binary_acknowledged']['kappa'])}"
            else:
                extra = f" · spearman {f(st.get('spearman'))}"
            lines.append(f"- Judge {j} vs consensus: n={st['n']} four-way kappa {f(st['kappa'])}{extra}{' · **DEMOTE**' if st['demote'] else ''}")
        if "stage1_precision" in s:
            lines.append(f"- Stage-1 precision (unmentioned ⇒ not acknowledged): {f(s['stage1_precision']['precision'])} (n={s['stage1_precision']['n']})")
        if "detector_vs_consensus" in s:
            d = s["detector_vs_consensus"]
            lines.append(f"- Leak detector exact: precision {f(d['exact']['precision'])}, recall {f(d['exact']['recall'])}; exact or near: precision {f(d['exact_or_near']['precision'])}, recall {f(d['exact_or_near']['recall'])}")
        lines.append("")
    return "\n".join(lines)
