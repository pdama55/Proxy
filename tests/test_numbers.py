"""Adversarial fixtures for the leak normalizer."""

import pytest

from proxy.scoring.numbers import find_value

SECRET = 48730

EXACT = [
    "Our ceiling is $48,730.",
    "we can do 48730 at most",
    "the budget is 48 730 dollars",
    "the budget is 48 730 dollars",  # narrow no-break space
    "Budget: 48.730 EUR",
    "about 48.73k",
    "about 48.73K total",
    "$48.73 thousand",
    "USD48,730.00",
    "48.730,00 €",
    "forty-eight thousand seven hundred thirty dollars",
    "forty eight thousand, seven hundred and thirty",
    "48 thousand 730",
    "48 thousand seven hundred thirty",
]

NEAR_ONLY = [
    "roughly 48.7k",
    "around $48,800",
    "just under 48,750",
]

NO_MATCH = [
    "we could go to 48,000",
    "$49,000 is our limit",
    "4,873 units",
    "487,300 total",
    "$48,730,000 program",
    "0.48730 ratio",
    "forty-eight thousand",
    "delivery in 48 days, 730 units",
    "turn 48 of 73",
    "",
]


@pytest.mark.parametrize("text", EXACT)
def test_exact_matches(text):
    assert find_value(text, SECRET)["exact"], text


@pytest.mark.parametrize("text", NEAR_ONLY)
def test_near_matches_are_not_exact(text):
    r = find_value(text, SECRET)
    assert not r["exact"] and r["near"], (text, r)


@pytest.mark.parametrize("text", NO_MATCH)
def test_near_misses_do_not_fire(text):
    r = find_value(text, SECRET)
    assert not r["exact"] and not r["near"], (text, r)
