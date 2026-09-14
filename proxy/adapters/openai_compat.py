"""OpenAI Chat Completions and OpenAI-compatible servers (OpenRouter, Ollama, vLLM)."""

import os

import openai

from proxy.adapters.base import Adapter, AdapterError
from proxy.runner.types import Completion

ENDPOINTS = {
    "openai": (None, "OPENAI_API_KEY"),
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
    "ollama": (os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1"), None),
    "vllm": (os.environ.get("VLLM_BASE_URL", "http://localhost:8000/v1"), "VLLM_API_KEY"),
}


class OpenAICompatAdapter(Adapter):
    supports_seed = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        base_url, key_env = ENDPOINTS[self.spec.provider]
        api_key = os.environ.get(key_env) if key_env else "ollama"
        if self.spec.provider in ("openai", "openrouter") and not api_key:
            raise AdapterError(f"{self.spec.key}: {key_env} is not set")
        self.client = openai.AsyncOpenAI(
            api_key=api_key or "EMPTY", base_url=base_url, timeout=self.timeout_s, max_retries=5
        )

    async def _complete(self, system: str, messages: list[dict], *, seed: int | None) -> Completion:
        params = dict(self.spec.params)
        extra_body = dict(params.pop("extra_body", {}) or {})
        if self.spec.provider == "openrouter" and self.spec.openrouter_provider:
            extra_body["provider"] = self.spec.openrouter_provider
        token_arg = "max_completion_tokens" if self.spec.provider == "openai" else "max_tokens"
        kwargs = {
            "model": self.spec.model,
            "messages": [{"role": "system", "content": system}, *messages],
            token_arg: self.spec.max_tokens,
            **params,
        }
        if seed is not None:
            kwargs["seed"] = seed
        if extra_body:
            kwargs["extra_body"] = extra_body
        try:
            resp = await self.client.chat.completions.create(**kwargs)
        except openai.APIStatusError as e:
            raise AdapterError(f"{self.spec.key}: HTTP {e.status_code}: {str(e.message)[:300]}") from e
        except openai.APIConnectionError as e:
            raise AdapterError(f"{self.spec.key}: connection error: {e}") from e

        if not resp.choices:
            raise AdapterError(f"{self.spec.key}: response had no choices")
        choice = resp.choices[0]
        usage = resp.usage
        details = getattr(usage, "completion_tokens_details", None) if usage else None
        meta = {"id": resp.id, "system_fingerprint": getattr(resp, "system_fingerprint", None)}
        extra = resp.model_extra or {}
        if "provider" in extra:
            meta["served_by"] = extra["provider"]
        return Completion(
            text=choice.message.content or "",
            tokens_in=usage.prompt_tokens if usage else 0,
            tokens_out=usage.completion_tokens if usage else 0,
            reasoning_tokens=(getattr(details, "reasoning_tokens", 0) or 0) if details else 0,
            finish_reason=choice.finish_reason,
            model_version=resp.model,
            raw_meta=meta,
        )

    async def list_models(self) -> list[str]:
        return [m.id async for m in self.client.models.list()]
