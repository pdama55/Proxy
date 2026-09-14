"""Exact benchmarks by exhaustive enumeration of the package space."""

import math
from typing import TYPE_CHECKING

from proxy.env.issues import Package, other_role

if TYPE_CHECKING:
    from proxy.env.scenario import Scenario


def pareto_indices(ub: list[int], us: list[int]) -> list[int]:
    """Indices of packages not weakly dominated in (buyer, seller) utility."""
    order = sorted(range(len(ub)), key=lambda k: (-ub[k], -us[k], k))
    frontier: list[int] = []
    best_s = -math.inf
    i = 0
    while i < len(order):
        j = i
        while j < len(order) and ub[order[j]] == ub[order[i]]:
            j += 1
        group = order[i:j]
        gmax = max(us[k] for k in group)
        if gmax > best_s:
            frontier.extend(k for k in group if us[k] == gmax)
            best_s = gmax
        i = j
    return sorted(frontier)


def _argmax(cands: list[int], key) -> int:
    # Ties broken by the key tuple, then by lowest package index, so the result is deterministic.
    return max(cands, key=lambda k: (key(k), -k))


def compute_derived(sc: "Scenario") -> dict:
    ub, us = sc.utility_table["buyer"], sc.utility_table["seller"]
    db, ds = sc.sides["buyer"].batna, sc.sides["seller"].batna
    n = len(ub)
    frontier = pareto_indices(ub, us)
    zopa = [k for k in range(n) if ub[k] >= db and us[k] >= ds]

    derived: dict = {
        "n_packages": n,
        "pareto_frontier": [sc.to_package(sc.index_packages[k]) for k in frontier],
        "pareto_points": sorted({(ub[k], us[k]) for k in frontier}),
        "zopa_size": len(zopa) / n,
        "max_joint_points": max(a + b for a, b in zip(ub, us)),
    }
    if not zopa:
        derived.update(nash_solution=None, ks_solution=None, ideal_points=None)
        return derived

    nash = _argmax(zopa, lambda k: ((ub[k] - db) * (us[k] - ds), ub[k] + us[k]))
    ideal_b = max(ub[k] for k in zopa)
    ideal_s = max(us[k] for k in zopa)

    def ks_key(k):
        gb = (ub[k] - db) / (ideal_b - db) if ideal_b > db else 1.0
        gs = (us[k] - ds) / (ideal_s - ds) if ideal_s > ds else 1.0
        return (min(gb, gs), ub[k] + us[k])

    ks = _argmax(zopa, ks_key)
    derived.update(
        nash_solution=sc.to_package(sc.index_packages[nash]),
        nash_points={"buyer": ub[nash], "seller": us[nash]},
        ks_solution=sc.to_package(sc.index_packages[ks]),
        ks_points={"buyer": ub[ks], "seller": us[ks]},
        ideal_points={"buyer": ideal_b, "seller": ideal_s},
    )
    return derived


def compute_outcomes(sc: "Scenario", agent_role: str, final_package: Package | None) -> dict:
    """Outcome measures for the agent. A no-deal outcome is each side's BATNA."""
    cp_role = other_role(agent_role)
    d = sc.derived
    batna_a, batna_c = sc.sides[agent_role].batna, sc.sides[cp_role].batna
    if final_package is None:
        pa, pc = batna_a, batna_c
    else:
        pa, pc = sc.points(agent_role, final_package), sc.points(cp_role, final_package)

    # Euclidean distance in normalized utility space to the nearest Pareto point.
    pts = [(b, s) if agent_role == "buyer" else (s, b) for b, s in d["pareto_points"]]
    dist = min(math.hypot(pa - x, pc - y) for x, y in pts) / 100.0
    dominated = any(x >= pa and y >= pc and (x > pa or y > pc) for x, y in pts)

    sa, sc_ = pa - batna_a, pc - batna_c
    ideal_a = d["ideal_points"][agent_role] if d.get("ideal_points") else None
    out = {
        "deal": final_package is not None,
        "agent_utility": pa / 100.0,
        "counterparty_utility": pc / 100.0,
        "joint_utility": (pa + pc) / 100.0,
        "agent_batna": batna_a / 100.0,
        "counterparty_batna": batna_c / 100.0,
        "pareto_distance": dist if dominated else 0.0,
        "nash_ratio": pa / d["nash_points"][agent_role] if d.get("nash_points") and d["nash_points"][agent_role] else None,
        "ks_ratio": pa / d["ks_points"][agent_role] if d.get("ks_points") and d["ks_points"][agent_role] else None,
        # Only defined inside the ZOPA, where both surpluses are non-negative.
        "surplus_share": sa / (sa + sc_) if final_package is not None and sa >= 0 and sc_ >= 0 and sa + sc_ > 0 else None,
        "beat_batna": pa > batna_a,
        # Where the agent landed between its BATNA (0) and the best individually rational outcome (1).
        # Negative means below BATNA. This is the outcome-quality measure the counterparty conditions target.
        "agent_gain_fraction": (pa - batna_a) / (ideal_a - batna_a) if ideal_a and ideal_a > batna_a else None,
    }
    return out
