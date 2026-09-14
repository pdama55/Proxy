import pytest

from proxy.env.scenario import generate_scenario
from proxy.runner.parse import ParseError, parse_action
from proxy.runner.types import PublicAction, View

SC = generate_scenario(3)
PRICES = SC.issue("price").domain
P = PRICES[4]


def view(history=()):
    return View(role="buyer", briefing=None, issues=tuple(SC.issues), public_history=tuple(history), turn=len(history), turn_cap=16)


SELLER_OFFER = PublicAction(0, "seller", "offer", {"price": P, "delivery_days": 30, "warranty_months": 12, "payment_terms": "net_30"}, "hi")


def test_clean_fenced_offer():
    text = f'```json\n{{"action": "offer", "package": {{"price": {P}, "delivery_days": 30, "warranty_months": 24, "payment_terms": "net_60"}}, "message": "Hello"}}\n```'
    a = parse_action(text, view())
    assert a.type == "offer" and a.package["price"] == P and a.message == "Hello"


def test_prose_around_unfenced_json_and_string_values():
    text = f'Let me think.\n{{"action": "Counter-offer", "package": {{"Price": "${P:,}", "Delivery time": "45 days", "warranty_months": "24 months", "payment_terms": "Net 30"}}, "message": null}}\nDone.'
    a = parse_action(text, view())
    assert a.type == "offer"
    assert a.package == {"price": P, "delivery_days": 45, "warranty_months": 24, "payment_terms": "net_30"}
    assert a.message is None


def test_last_fenced_block_wins():
    text = '```json\n{"action": "walk_away"}\n```\nActually:\n```json\n{"action": "message_only", "message": "Wait"}\n```'
    assert parse_action(text, view()).type == "message_only"


@pytest.mark.parametrize(
    "text,err",
    [
        ("no json here", "no JSON"),
        ('```json\n{"package": null}\n```', "missing \"action\""),
        ('```json\n{"action": "haggle"}\n```', "must be one of"),
        (f'```json\n{{"action": "offer", "package": {{"price": {P}}}}}\n```', "missing terms"),
        (f'```json\n{{"action": "offer", "package": {{"price": 1, "delivery_days": 30, "warranty_months": 12, "payment_terms": "net_30"}}}}\n```', "not a valid option"),
        ('```json\n{"action": "offer", "package": null}\n```', "complete \"package\""),
        ('```json\n{"action": "message_only", "message": "  "}\n```', "non-empty"),
        ('```json\n{"action": "accept"}\n```', "no offer from the other party"),
        ('```json\n{"action": "offer", "package": {"price": 1,}}\n```', "no JSON"),
    ],
)
def test_malformed_outputs(text, err):
    with pytest.raises(ParseError, match=err):
        parse_action(text, view())


def test_accept_requires_other_sides_offer():
    assert parse_action('```json\n{"action": "accept", "message": "Deal"}\n```', view([SELLER_OFFER])).type == "accept"
    own = PublicAction(0, "buyer", "offer", SELLER_OFFER.package, None)
    with pytest.raises(ParseError):
        parse_action('```json\n{"action": "accept"}\n```', view([own]))
