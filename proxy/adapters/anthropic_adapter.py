import anthropic

from proxy.adapters.base import Adapter, AdapterError
from proxy.runner.types import Completion


class AnthropicAdapter(Adapter):
    """Claude via the official Anthropic SDK.

    Server-side refusal fallbacks are deliberately NOT enabled: a fallback would silently serve a turn
    from a different model than the one under test. Refusals are recorded via finish_reason instead.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = anthropic.AsyncAnthropic(timeout=self.timeout_s, max_retries=5)

    async def _complete(self, system: str, messages: list[dict], *, seed: int | None) -> Completion:
        try:
            resp = await self.client.messages.create(
                model=self.spec.model,
                max_tokens=self.spec.max_tokens,
                system=system,
                messages=messages,
                **self.spec.params,
            )
        except anthropic.APIStatusError as e:
            raise AdapterError(f"{self.spec.key}: HTTP {e.status_code}: {str(e.message)[:300]}") from e
        except anthropic.APIConnectionError as e:
            raise AdapterError(f"{self.spec.key}: connection error: {e}") from e

        text = "".join(b.text for b in resp.content if b.type == "text")
        meta = {"request_id": resp._request_id}
        if resp.stop_reason == "refusal" and getattr(resp, "stop_details", None):
            meta["stop_details"] = resp.stop_details.to_dict()
        return Completion(
            text=text,
            tokens_in=resp.usage.input_tokens,
            tokens_out=resp.usage.output_tokens,
            finish_reason=resp.stop_reason,
            model_version=resp.model,
            raw_meta=meta,
        )

    async def list_models(self) -> list[str]:
        return [m.id async for m in self.client.models.list()]
