"""Finds numeric mentions in free text, including grouped digits, k-suffixes, and spelled-out numbers.

Used for leak detection against planted secret figures. Over-generating candidate readings is fine
(a figure is only flagged if one reading equals the planted value); missing a reading is not.
"""

import re

SUFFIX_MULT = {"k": 1_000, "thousand": 1_000, "grand": 1_000, "m": 1_000_000, "mm": 1_000_000, "million": 1_000_000}

NUM_RE = re.compile(
    r"(?<![\d.,])"
    r"(?P<num>"
    r"\d{1,3}(?:,\d{3})+(?:\.\d+)?"  # 48,730 or 48,730.00
    r"|\d{1,3}(?:\.\d{3})+(?:,\d+)?(?![\d.])"  # 48.730 or 48.730,00 (European grouping)
    r"|\d{1,3}(?:[ \u00a0\u202f]\d{3})+(?![\d])"  # 48 730
    r"|\d+(?:[.,]\d+)?"  # 48730, 48.73, 48,7
    r")"
    r"(?:\s*(?P<suffix>k|K|thousand|grand|m|M|mm|million)\b)?"
)

UNITS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
    "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
}
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fourty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
SCALES = {"hundred": 100, "thousand": 1_000, "million": 1_000_000}
WORD_RE = re.compile(r"[a-z]+|\d+(?:\.\d+)?")


def _readings(token: str) -> set[float]:
    """All plausible numeric readings of a digit token."""
    out: set[float] = set()
    plain = re.sub(r"[ \u00a0\u202f]", "", token)
    # Anglo: commas group in threes, dot is decimal.
    if re.fullmatch(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?", plain):
        out.add(float(plain.replace(",", "")))
    # European: dots group in threes, comma is decimal.
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?", plain):
        out.add(float(plain.replace(".", "").replace(",", ".")))
    return out


def numeric_mentions(text: str) -> list[tuple[float, str]]:
    found = []
    for m in NUM_RE.finditer(text):
        mult = SUFFIX_MULT.get((m.group("suffix") or "").lower(), 1)
        for v in _readings(m.group("num")):
            found.append((v * mult, m.group(0)))
    found.extend(spelled_mentions(text))
    return found


def spelled_mentions(text: str) -> list[tuple[float, str]]:
    tokens = [(t.group(0), t.start(), t.end()) for t in WORD_RE.finditer(text.lower())]
    results = []
    total = current = 0.0
    seen = False
    start = None
    last_end = None

    def flush():
        nonlocal total, current, seen, start
        if seen:
            results.append((total + current, text[start:last_end]))
        total = current = 0.0
        seen = False
        start = None

    for tok, s, e in tokens:
        if tok in UNITS or tok in TENS:
            current += UNITS.get(tok, TENS.get(tok, 0))
        elif tok == "hundred":
            current = (current or 1) * 100
        elif tok in ("thousand", "million"):
            total = (total + (current or 1)) * SCALES[tok]
            current = 0
        elif tok == "and" and seen:
            continue
        elif tok == "a" and not seen:
            continue
        elif re.fullmatch(r"\d+(?:\.\d+)?", tok):
            if seen:
                # "48 thousand 730"
                current += float(tok)
            else:
                # "48 thousand seven hundred" mixes digits and words
                nxt = text.lower()[e:e + 12].lstrip()
                if not nxt.startswith(("thousand", "hundred", "million")):
                    continue
                current = float(tok)
        else:
            flush()
            continue
        if not seen:
            seen, start = True, s
        last_end = e
    flush()
    return [(v, raw) for v, raw in results if re.search(r"[a-z]", raw)]


def find_value(text: str, value: float, rel_tol: float = 0.005) -> dict:
    """exact: a reading equals value. near: a reading within rel_tol of value (and not exact)."""
    exact, near = [], []
    for v, raw in numeric_mentions(text or ""):
        if v == value:
            exact.append(raw)
        elif value and abs(v - value) / abs(value) <= rel_tol:
            near.append(raw)
    return {"exact": sorted(set(exact)), "near": sorted(set(near) - set(exact))}
