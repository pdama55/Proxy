import dataclasses

import pytest

from proxy.config import ExperimentConfig
from proxy.env.briefing import build_briefing
from proxy.env.scenario import generate_scenario
from proxy.runner import render
from proxy.runner.isolation import IsolationViolation, check_view, side_markers
from proxy.runner.types import Action, PublicAction, View
from proxy.util import rng_for


def _views(seed=9):
    sc = generate_scenario(seed)
    buyer = build_briefing(sc, "buyer", rng_for(seed, "b"), constraint_types=["floor", "secrecy"])
    seller = build_briefing(sc, "seller", rng_for(seed, "s"), constraint_types=["floor", "secrecy"])
    history = (PublicAction(0, "seller", "offer", sc.to_package(sc.index_packages[0]), "Opening."),)
    vb = View("buyer", buyer, tuple(sc.issues), history, 1, 16)
    return sc, buyer, seller, vb


def test_clean_view_passes_and_contains_no_opposing_tokens():
    sc, buyer, seller, vb = _views()
    check_view(vb, side_markers(sc, "seller", seller), side_markers(sc, "buyer", buyer))
    text = render.system_prompt(vb) + render.turn_prompt(vb)
    for c in seller.constraints:
        assert c.text not in text
        if c.secret_token:
            assert c.secret_token not in text
    assert buyer.text in text


def test_contaminated_briefing_is_caught():
    sc, buyer, seller, vb = _views()
    leaked_line = next(m for m in side_markers(sc, "seller", seller) if m.startswith("Price:"))
    bad = dataclasses.replace(buyer, text=buyer.text + "\n" + leaked_line)
    with pytest.raises(IsolationViolation):
        check_view(dataclasses.replace(vb, briefing=bad), side_markers(sc, "seller", seller), side_markers(sc, "buyer", buyer))


def test_scripted_counterparty_values_are_markers_even_without_a_briefing():
    sc, buyer, _, vb = _views()
    markers = side_markers(sc, "seller", None)
    line = next(m for m in markers if m.startswith("Warranty"))
    bad = dataclasses.replace(buyer, text=buyer.text + "\n" + line)
    with pytest.raises(IsolationViolation):
        check_view(dataclasses.replace(vb, briefing=bad), markers, side_markers(sc, "buyer", buyer))


def test_public_history_rejects_full_actions():
    sc, buyer, seller, vb = _views()
    raw = Action(0, "counterparty", "seller", "offer", None, "hi", raw_output="secret reasoning", parse_ok=True)
    with pytest.raises(IsolationViolation):
        check_view(dataclasses.replace(vb, public_history=(raw,)), side_markers(sc, "seller", seller), set())


def test_what_the_other_side_says_publicly_is_not_a_violation():
    """A leak by the other side is data, not a harness bug: history is excluded from the check."""
    sc, buyer, seller, vb = _views()
    secret = next(c for c in seller.constraints if c.type == "secrecy")
    history = (PublicAction(0, "seller", "message_only", None, f"Our floor is {secret.secret_token}."),)
    check_view(dataclasses.replace(vb, public_history=history), side_markers(sc, "seller", seller), side_markers(sc, "buyer", buyer))
