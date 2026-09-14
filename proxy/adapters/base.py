import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from proxy.config import ModelSpec
from proxy.runner.types import Completion


class BudgetExceeded(RuntimeError):
    pass


class AdapterError(RuntimeError):
    """A model call failed after the SDK's own retries."""


@dataclass
class SpendTracker:
    ceiling_usd: float
    spent_usd: float = 0.0
    calls: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    by_model: dict = field(default_factory=dict)

    def check(self) -> None:
        if self.spent_usd >= self.ceiling_usd:
            raise BudgetExceeded(f"spend ceiling ${self.ceiling_usd:.2f} reached (${self.spent_usd:.2f} spent)")

    def record(self, key: str, c: Completion) -> None:
        self.calls += 1
        self.spent_usd += c.cost_usd
        self.tokens_in += c.tokens_in
        self.tokens_out += c.tokens_out
        m = self.by_model.setdefault(key, {"calls": 0, "usd": 0.0, "tokens_in": 0, "tokens_out": 0})
        m["calls"] += 1
        m["usd"] += c.cost_usd
        m["tokens_in"] += c.tokens_in
        m["tokens_out"] += c.tokens_out

    def summary(self) -> str:
        lines = [f"spend ${self.spent_usd:.4f} / ${self.ceiling_usd:.2f} over {self.calls} calls"]
        for k, m in sorted(self.by_model.items()):
            lines.append(f"  {k}: ${m['usd']:.4f}, {m['calls']} calls, {m['tokens_in']} in / {m['tokens_out']} out")
        return "\n".join(lines)


class Adapter(ABC):
    def __init__(self, spec: ModelSpec, spend: SpendTracker, semaphore: asyncio.Semaphore, timeout_s: float):
        self.spec = spec
        self.spend = spend
        self.semaphore = semaphore
        self.timeout_s = timeout_s

    # Whether the provider accepts a sampling seed. Recorded per episode; null seed when False.
    supports_seed = False

    async def complete(self, system: str, messages: list[dict], *, seed: int | None = None) -> Completion:
        """messages: [{"role": "user"|"assistant", "content": str}]"""
        self.spend.check()
        async with self.semaphore:
            self.spend.check()
            t0 = time.monotonic()
            try:
                c = await asyncio.wait_for(self._complete(system, messages, seed=seed), timeout=self.timeout_s * 3)
            except asyncio.TimeoutError as e:
                raise AdapterError(f"{self.spec.key}: call timed out") from e
            c.latency_ms = int((time.monotonic() - t0) * 1000)
        billed_out = c.tokens_out + (c.reasoning_tokens if self.bills_reasoning_separately else 0)
        c.cost_usd = self.spec.cost(c.tokens_in, billed_out)
        self.spend.record(self.spec.key, c)
        return c

    # Gemini reports thinking tokens outside candidates_token_count; others include them in output tokens.
    bills_reasoning_separately = False

    @abstractmethod
    async def _complete(self, system: str, messages: list[dict], *, seed: int | None) -> Completion: ...

    async def list_models(self) -> list[str]:
        raise NotImplementedError
