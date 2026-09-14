"""Hand-computed scenario with a known Pareto frontier, Nash point, and KS point."""

import math

import pytest

from proxy.env.benchmarks import compute_outcomes, pareto_indices
from proxy.env.issues import Issue
from proxy.env.scenario import Scenario, SideValues


@pytest.fixture
def toy() -> Scenario:
    # Buyer weights issue a 70/30, seller weights it 30/70: trading a for b is Pareto-improving.
    issues = [
        Issue("a", "ordinal", (0, 1, 2), "A", ascending_role="buyer"),
        Issue("b", "ordinal", (0, 1, 2), "B", ascending_role="seller"),
    ]
    sides = {
        "buyer": SideValues({"a": 70, "b": 30}, {"a": (0, 35, 70), "b": (30, 15, 0)}, batna=20),
        "seller": SideValues({"a": 30, "b": 70}, {"a": (30, 15, 0), "b": (0, 35, 70)}, batna=20),
    }
    return Scenario("toy", 0, issues, sides)


def test_utility_table(toy):
    # package index = a_idx * 3 + b_idx
    assert toy.utility_table["buyer"] == [30, 15, 0, 65, 50, 35, 100, 85, 70]
    assert toy.utility_table["seller"] == [30, 65, 100, 15, 50, 85, 0, 35, 70]


def test_pareto_frontier(toy):
    assert pareto_indices(toy.utility_table["buyer"], toy.utility_table["seller"]) == [2, 5, 6, 7, 8]
    d = toy.derived
    assert d["pareto_points"] == [(0, 100), (35, 85), (70, 70), (85, 35), (100, 0)]


def test_pareto_ties_are_all_kept():
    # Two packages with identical utility pairs on the frontier must both be kept.
    assert pareto_indices([5, 5, 3], [5, 5, 6]) == [0, 1, 2]
    assert pareto_indices([5, 5], [5, 4]) == [0]


def test_nash_ks_zopa(toy):
    d = toy.derived
    assert d["zopa_size"] == pytest.approx(5 / 9)
    assert d["nash_solution"] == {"a": 2, "b": 2}
    assert d["nash_points"] == {"buyer": 70, "seller": 70}
    assert d["ks_solution"] == {"a": 2, "b": 2}
    assert d["ideal_points"] == {"buyer": 85, "seller": 85}


def test_outcomes_for_dominated_deal(toy):
    o = compute_outcomes(toy, "buyer", {"a": 1, "b": 1})
    assert o["agent_utility"] == 0.5 and o["counterparty_utility"] == 0.5
    assert o["pareto_distance"] == pytest.approx(math.hypot(20, 20) / 100)
    assert o["nash_ratio"] == pytest.approx(50 / 70)
    assert o["surplus_share"] == pytest.approx(0.5)
    assert o["agent_gain_fraction"] == pytest.approx(30 / 65)
    assert o["beat_batna"] is True


def test_outcomes_on_frontier_and_no_deal(toy):
    assert compute_outcomes(toy, "seller", {"a": 1, "b": 2})["pareto_distance"] == 0.0
    nd = compute_outcomes(toy, "buyer", None)
    assert nd["deal"] is False and nd["agent_utility"] == 0.2 and nd["agent_gain_fraction"] == 0.0
    assert nd["surplus_share"] is None
