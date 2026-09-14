import asyncio

import pytest

from proxy.counterparty.reference import ReferenceAgent
from proxy.counterparty.scripted import ScriptedCounterparty, ScriptedParams
from proxy.env.briefing import build_briefing
from proxy.env.scenario import generate_scenario
from proxy.runner.episode import run_episode
from proxy.util import rng_for
from tests.conftest import make_spec


def _episode(**kw):
    return asyncio.run(run_episode(make_spec(**kw), {}, None, agent_override=ReferenceAgent(respect_constraints=False)))


def test_counterparty_trajectory_is_deterministic():
    a, b = _episode(scenario_seed=21), _episode(scenario_seed=21)
    strip = lambda ep: [(x["turn"], x["type"], x["package"], x["message"]) for x in ep["actions"]]
    assert strip(a) == strip(b)
    assert a["condition"]["first_mover"] == b["condition"]["first_mover"]
    assert a["episode_id"] == b["episode_id"]


@pytest.mark.parametrize("seed", range(10))
def test_script_never_offers_or_accepts_outside_its_allowed_set(seed):
    ep = _episode(scenario_seed=seed)
    sc = generate_scenario(seed)
    ua = sc.utility_table["buyer"]
    d_a = sc.sides["buyer"].batna
    span = sc.derived["ideal_points"]["buyer"] - d_a
    cap = d_a + 0.5 * span
    for x in ep["actions"]:
        if x["actor"] == "counterparty" and x["type"] == "offer":
            assert ua[sc.index_packages.index(sc.to_index(x["package"]))] <= cap
    if ep["termination"]["final_package"]:
        assert ep["outcomes"]["agent_gain_fraction"] <= 0.5 + 1e-9


def test_outcome_bands_are_ordered_by_agent_cap():
    means = []
    for cap in (0.9, 0.5, 0.2):
        gains = []
        for seed in range(12):
            for role in ("buyer", "seller"):
                ep = _episode(scenario_seed=seed, agent_role=role, counterparty_params={"agent_cap": cap, "compliant_cap_ratio": 0.5})
                if ep["outcomes"]["deal"]:
                    gains.append(ep["outcomes"]["agent_gain_fraction"])
        means.append(sum(gains) / len(gains))
    assert means[0] > means[1] > means[2]


def test_negative_cap_means_no_deal_above_batna():
    for seed in range(8):
        ep = _episode(scenario_seed=seed, counterparty_params={"agent_cap": -0.3, "compliant_cap_ratio": 0.5})
        assert not ep["outcomes"]["beat_batna"]


def test_compliant_option_is_offered_at_the_limit():
    seed = 4
    sc = generate_scenario(seed)
    b = build_briefing(sc, "buyer", rng_for(seed), constraint_types=["floor"])
    cp = ScriptedCounterparty(sc, "seller", ScriptedParams(agent_cap=0.6, compliant_cap_ratio=0.5), b.constraints, seed=1)
    assert cp.compliant_k is not None
    compliant_pkg = sc.to_package(sc.index_packages[cp.compliant_k])
    assert not b.constraints[0].violated_by(compliant_pkg)
    span = sc.derived["ideal_points"]["buyer"] - sc.sides["buyer"].batna
    assert sc.utility_table["buyer"][cp.compliant_k] <= sc.sides["buyer"].batna + 0.3 * span


def test_counterparty_messages_contain_no_figures():
    ep = _episode(scenario_seed=2)
    for x in ep["actions"]:
        if x["actor"] == "counterparty":
            assert not any(ch.isdigit() for ch in x["message"])
