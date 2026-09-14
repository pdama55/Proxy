"""Parses and validates a model's turn output into a structured action."""

import json
import re
from dataclasses import dataclass

from proxy.env.issues import Issue, Package, other_role
from proxy.runner.types import ACTION_TYPES, View

FENCE_RE = re.compile(r"```(?:json|JSON)?\s*(.*?)```", re.DOTALL)

ACTION_ALIASES = {
    "counteroffer": "offer",
    "counter_offer": "offer",
    "propose": "offer",
    "proposal": "offer",
    "walk": "walk_away",
    "walkaway": "walk_away",
    "reject_and_walk_away": "walk_away",
    "message": "message_only",
    "messageonly": "message_only",
    "agree": "accept",
}

PAYMENT_ALIASES = {
    "upfront": "upfront",
    "up_front": "upfront",
    "payment_upfront": "upfront",
    "prepaid": "upfront",
    "net30": "net_30",
    "net_30": "net_30",
    "net60": "net_60",
    "net_60": "net_60",
    "net90": "net_90",
    "net_90": "net_90",
}


class ParseError(ValueError):
    pass


@dataclass
class ParsedAction:
    type: str
    package: Package | None
    message: str | None


def extract_json(text: str) -> dict:
    return extract_json_object(text, required_key="action")


def extract_json_object(text: str, required_key: str | None = None) -> dict:
    """The last JSON object in a fenced block, else the last decodable object in the text."""
    candidates = [m.group(1) for m in FENCE_RE.finditer(text)]
    for block in reversed(candidates):
        try:
            obj = json.loads(block.strip())
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue
    # Fall back to the last decodable object (with the required key, if any) anywhere in the text.
    decoder = json.JSONDecoder()
    found = None
    for m in re.finditer(r"\{", text):
        try:
            obj, _ = decoder.raw_decode(text[m.start():])
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and (required_key is None or required_key in obj):
            found = obj
    if found is None:
        what = f'with a "{required_key}" field ' if required_key else ""
        raise ParseError(f"no JSON object {what}was found")
    return found


def _norm_key(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(s).strip().lower()).strip("_")


def coerce_value(issue: Issue, value) -> object:
    if issue.name == "payment_terms":
        key = _norm_key(value).replace("payment_terms_", "")
        if key in PAYMENT_ALIASES:
            return PAYMENT_ALIASES[key]
        raise ParseError(f'"{value}" is not a valid option for {issue.name}; options: {list(issue.domain)}')
    if isinstance(value, bool):
        raise ParseError(f'"{value}" is not a valid option for {issue.name}')
    if isinstance(value, (int, float)):
        num = value
    else:
        digits = re.sub(r"[^0-9.]", "", str(value))
        try:
            num = float(digits)
        except ValueError:
            raise ParseError(f'"{value}" is not a valid option for {issue.name}; options: {list(issue.domain)}')
    if float(num) != int(num) or int(num) not in issue.domain:
        raise ParseError(f'"{value}" is not a valid option for {issue.name}; options: {list(issue.domain)}')
    return int(num)


def coerce_package(issues: tuple[Issue, ...], raw) -> Package:
    if not isinstance(raw, dict):
        raise ParseError("\"package\" must be an object with a value for every term")
    by_key = {}
    for i in issues:
        by_key[_norm_key(i.name)] = i
        by_key[_norm_key(i.label)] = i
    out: Package = {}
    for k, v in raw.items():
        iss = by_key.get(_norm_key(k))
        if iss is None:
            raise ParseError(f'unknown term "{k}"; terms are {[i.name for i in issues]}')
        out[iss.name] = coerce_value(iss, v)
    missing = [i.name for i in issues if i.name not in out]
    if missing:
        raise ParseError(f"offer is missing terms: {missing}")
    return out


def parse_action(text: str, view: View) -> ParsedAction:
    obj = extract_json(text)
    raw_type = obj.get("action")
    if raw_type is None:
        raise ParseError('missing "action" field')
    atype = _norm_key(raw_type)
    atype = ACTION_ALIASES.get(atype, atype)
    if atype not in ACTION_TYPES:
        raise ParseError(f'"action" must be one of {list(ACTION_TYPES)}, got "{raw_type}"')

    message = obj.get("message")
    message = str(message).strip() if message is not None else None
    message = message or None

    package = None
    if atype == "offer":
        if obj.get("package") is None:
            raise ParseError('an "offer" must include a complete "package"')
        package = coerce_package(view.issues, obj["package"])
    elif atype == "accept":
        if view.last_offer_by(other_role(view.role)) is None:
            raise ParseError("there is no offer from the other party to accept")
    elif atype == "message_only":
        if message is None:
            raise ParseError('"message_only" requires a non-empty "message"')
    return ParsedAction(atype, package, message)
