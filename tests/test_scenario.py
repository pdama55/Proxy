import pytest

from proxy.env.briefing import BRIEFING_VARIANTS, PHRASINGS, build_briefing
from proxy.env.scenario import Scenario, assert_integrative, generate_scenario
from proxy.util import rng_for


@pytest.mark.parametrize("seed", range(25))
def test_generated_scenarios_are_valid(seed):
    sc = generate_scenario(seed)
    assert_integrative(sc)
    for side in sc.sides.values():
        assert sum(side.weights.values()) == 100
        for iss in sc.issues:
            pts = side.points[iss.name]
            assert min(pts) == 0 and max(pts) == side.weights[iss.name]
    assert len(sc.index_packages) == sc.derived["n_packages"] <= 5000
    assert 0.08 <= sc.derived["zopa_size"] <= 0.45
    assert all(0 <= u <= 100 for u in sc.utility_table["buyer"])


def test_scenario_generation_is_deterministic():
    a, b = generate_scenario(42).to_dict(), generate_scenario(42).to_dict()
    assert a == b
    assert generate_scenario(43).to_dict() != a


def test_scenario_roundtrip():
    sc = generate_scenario(5)
    d = sc.to_dict()
    back = Scenario.from_dict(__import__("json").loads(__import__("json").dumps(d)))
    assert back.utility_table == sc.utility_table
    assert back.to_dict()["derived"]["nash_solution"] == d["derived"]["nash_solution"]


@pytest.mark.parametrize("seed", range(15))
@pytest.mark.parametrize("role", ["buyer", "seller"])
def test_constraints_are_identical_across_prompt_conditions(seed, role):
    """Paired design: phrasing, salience, and audit framing change wording only, never the planted facts."""
    sc = generate_scenario(seed)
    facts = set()
    for variant in BRIEFING_VARIANTS:
        for phrasing in PHRASINGS:
            for audit in (False, True):
                b = build_briefing(
                    sc, role, rng_for(seed, role), constraint_types=["floor", "secrecy"],
                    audit_framing=audit, prompt_variant=variant, phrasing=phrasing,
                )
                facts.add(tuple((c.constraint_id, str(c.bound), str(c.allowed), c.secret_value) for c in b.constraints))
                assert ("I will read the full transcript" in b.text) == audit
    assert len(facts) == 1


@pytest.mark.parametrize("seed", range(30))
def test_secret_tokens_are_distinctive(seed):
    sc = generate_scenario(seed)
    prices = sc.issue("price").domain
    for role in ("buyer", "seller"):
        b = build_briefing(sc, role, rng_for(seed, role, "s"), constraint_types=["secrecy"])
        v = b.constraints[0].secret_value
        assert v % 50 != 0
        assert all(abs(v - p) / p >= 0.02 for p in prices)


@pytest.mark.parametrize("seed", range(15))
def test_floor_bound_leaves_both_compliant_and_violating_deals(seed):
    sc = generate_scenario(seed)
    for role in ("buyer", "seller"):
        b = build_briefing(sc, role, rng_for(seed, role, "f"), constraint_types=["floor"])
        c = b.constraints[0]
        assert 0 < c.zopa_violation_fraction < 1
        assert c.bound in c.allowed
        assert 0 < len(c.allowed) < len(sc.issue(c.issue).domain)
