import asyncio

import pytest

from proxy.adapters.base import AdapterError, SpendTracker
from proxy.adapters.openai_compat import OpenAICompatAdapter, azure_base_url
from proxy.config import ModelSpec


def test_azure_base_url():
    assert azure_base_url("https://res.openai.azure.com") == "https://res.openai.azure.com/openai/v1/"
    assert azure_base_url("https://res.openai.azure.com/") == "https://res.openai.azure.com/openai/v1/"
    assert azure_base_url("https://res.services.ai.azure.com/openai/v1") == "https://res.services.ai.azure.com/openai/v1"
    assert azure_base_url(None) is None


def _spec():
    return ModelSpec(key="az", provider="azure", model="my-deployment", family="x", tier="small")


def test_azure_adapter_requires_endpoint_and_key(monkeypatch):
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    with pytest.raises(AdapterError):
        OpenAICompatAdapter(_spec(), SpendTracker(1.0), asyncio.Semaphore(1), timeout_s=5)
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "k")
    with pytest.raises(AdapterError):
        OpenAICompatAdapter(_spec(), SpendTracker(1.0), asyncio.Semaphore(1), timeout_s=5)
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://res.openai.azure.com")
    a = OpenAICompatAdapter(_spec(), SpendTracker(1.0), asyncio.Semaphore(1), timeout_s=5)
    assert str(a.client.base_url) == "https://res.openai.azure.com/openai/v1/"
