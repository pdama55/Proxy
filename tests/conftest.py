import asyncio
from collections.abc import Callable

import pytest

from proxy.adapters.base import Adapter, SpendTracker
from proxy.config import EpisodeSpec, ModelSpec
from proxy.runner.types import Completion

FLOOR_ISSUES = ["delivery_days", "warranty_months", "payment_terms"]
CP_PARAMS = {"agent_cap": 0.5, "compliant_cap_ratio": 0.5, "probe_moves": [1, 3]}


class FakeAdapter(Adapter):
    """Deterministic stand-in for a model: `policy(system, messages)` returns the completion text."""

    supports_seed = True

    def __init__(self, policy: Callable[[str, list[dict]], str], key: str = "fake"):
        spec = ModelSpec(key=key, provider="openrouter", model=key, family="fake", tier="small", price_in_per_mtok=1, price_out_per_mtok=1)
        super().__init__(spec, SpendTracker(ceiling_usd=100.0), asyncio.Semaphore(4), timeout_s=10)
        self.policy = policy
        self.calls: list[tuple[str, list[dict]]] = []

    async def _complete(self, system, messages, *, seed):
        self.calls.append((system, list(messages)))
        text = self.policy(system, messages)
        return Completion(text=text, tokens_in=100, tokens_out=20, finish_reason="stop", model_version=f"{self.spec.key}-v0")


class FakeFactory:
    def __init__(self, adapters: dict[str, FakeAdapter]):
        self.adapters = adapters

    def get(self, spec: ModelSpec):
        return self.adapters[spec.key]


def make_spec(**overrides) -> EpisodeSpec:
    base = dict(
        model="fake",
        outcome_target="mediocre",
        audit_framing=False,
        briefing_variant="base",
        phrasing="plain",
        report_variant="open",
        agent_role="buyer",
        constraint_set=["floor", "secrecy"],
        scenario_seed=11,
        replicate=0,
        turn_cap=16,
        counterparty_kind="scripted",
        counterparty_model=None,
        counterparty_params=dict(CP_PARAMS),
        floor_issues=list(FLOOR_ISSUES),
    )
    base.update(overrides)
    return EpisodeSpec(**base)


def fake_models(*keys) -> dict[str, ModelSpec]:
    return {k: ModelSpec(key=k, provider="openrouter", model=k, family="fake", tier="small") for k in keys}


@pytest.fixture
def run():
    return lambda coro: asyncio.run(coro)
