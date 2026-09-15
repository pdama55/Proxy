"""A model call that must return one JSON object, with one format retry. Shared by the judge and the
principal simulation."""

from dataclasses import asdict, dataclass

from proxy.adapters.base import Adapter
from proxy.runner.parse import ParseError, extract_json_object


@dataclass
class TaskResult:
    ok: bool
    parsed: dict | None
    raw: str
    raw_retry: str | None
    error: str | None
    model_key: str
    model_version: str | None
    tokens_in: int
    tokens_out: int
    cost_usd: float

    def to_dict(self) -> dict:
        return asdict(self)


RETRY = "Your response could not be used: {error}. Respond again with only the JSON object in a ```json code block."


async def json_task(adapter: Adapter, system: str, user: str | list[dict], validate, *, seed: int | None = None) -> TaskResult:
    """validate(obj) returns the cleaned object or raises ParseError. `user` is one user message, or a full
    message history ending in a user turn."""
    messages = [{"role": "user", "content": user}] if isinstance(user, str) else list(user)
    raws: list[str] = []
    tokens_in = tokens_out = 0
    cost = 0.0
    error = None
    version = None
    for _ in (1, 2):
        c = await adapter.complete(system, messages, seed=seed if adapter.supports_seed else None)
        raws.append(c.text)
        tokens_in, tokens_out, cost, version = tokens_in + c.tokens_in, tokens_out + c.tokens_out, cost + c.cost_usd, c.model_version
        try:
            parsed = validate(extract_json_object(c.text))
            return TaskResult(True, parsed, raws[0], raws[1] if len(raws) > 1 else None, None, adapter.spec.key, version, tokens_in, tokens_out, cost)
        except ParseError as e:
            error = str(e)
            messages += [{"role": "assistant", "content": c.text or "(empty response)"}, {"role": "user", "content": RETRY.format(error=error)}]
    return TaskResult(False, None, raws[0], raws[1], error, adapter.spec.key, version, tokens_in, tokens_out, cost)


def require_int(obj: dict, key: str, lo: int, hi: int) -> int:
    v = obj.get(key)
    try:
        iv = int(v)
    except (TypeError, ValueError):
        raise ParseError(f'"{key}" must be an integer from {lo} to {hi}')
    if isinstance(v, float) and v != iv or not lo <= iv <= hi:
        raise ParseError(f'"{key}" must be an integer from {lo} to {hi}')
    return iv


def require_choice(obj: dict, key: str, choices: tuple[str, ...]) -> str:
    v = str(obj.get(key, "")).strip().lower().replace(" ", "_").replace("-", "_")
    if v not in choices:
        raise ParseError(f'"{key}" must be one of {list(choices)}')
    return v
