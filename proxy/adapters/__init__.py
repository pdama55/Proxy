import asyncio

from proxy.adapters.base import Adapter, AdapterError, BudgetExceeded, SpendTracker
from proxy.config import ModelSpec


class AdapterFactory:
    """Builds adapters sharing one spend tracker and per-provider concurrency caps."""

    def __init__(self, spend: SpendTracker, provider_concurrency: dict[str, int], timeout_s: float, via_openrouter: bool = False):
        self.spend = spend
        self.concurrency = provider_concurrency
        self.timeout_s = timeout_s
        self.via_openrouter = via_openrouter
        self._semaphores: dict[str, asyncio.Semaphore] = {}
        self._adapters: dict[str, Adapter] = {}

    def _semaphore(self, provider: str) -> asyncio.Semaphore:
        if provider not in self._semaphores:
            n = self.concurrency.get(provider, self.concurrency.get("default", 4))
            self._semaphores[provider] = asyncio.Semaphore(n)
        return self._semaphores[provider]

    def get(self, spec: ModelSpec) -> Adapter:
        if self.via_openrouter:
            spec = spec.via_openrouter()
        if spec.key not in self._adapters:
            self._adapters[spec.key] = make_adapter(spec, self.spend, self._semaphore(spec.provider), self.timeout_s)
        return self._adapters[spec.key]


def make_adapter(spec: ModelSpec, spend: SpendTracker, semaphore: asyncio.Semaphore, timeout_s: float) -> Adapter:
    if spec.provider == "anthropic":
        from proxy.adapters.anthropic_adapter import AnthropicAdapter

        return AnthropicAdapter(spec, spend, semaphore, timeout_s)
    if spec.provider == "gemini":
        from proxy.adapters.gemini_adapter import GeminiAdapter

        return GeminiAdapter(spec, spend, semaphore, timeout_s)
    from proxy.adapters.openai_compat import OpenAICompatAdapter

    return OpenAICompatAdapter(spec, spend, semaphore, timeout_s)


__all__ = ["Adapter", "AdapterError", "AdapterFactory", "BudgetExceeded", "SpendTracker", "make_adapter"]
