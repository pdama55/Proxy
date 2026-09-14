import os

from google import genai
from google.genai import errors, types

from proxy.adapters.base import Adapter, AdapterError
from proxy.runner.types import Completion


class GeminiAdapter(Adapter):
    supports_seed = True
    bills_reasoning_separately = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise AdapterError(f"{self.spec.key}: GEMINI_API_KEY is not set")
        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=int(self.timeout_s * 1000),
                retry_options=types.HttpRetryOptions(attempts=6, http_status_codes=[408, 429, 500, 502, 503, 504]),
            ),
        )

    async def _complete(self, system: str, messages: list[dict], *, seed: int | None) -> Completion:
        contents = [
            types.Content(role="user" if m["role"] == "user" else "model", parts=[types.Part(text=m["content"])])
            for m in messages
        ]
        config = types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=self.spec.max_tokens,
            seed=seed,
            **self.spec.params,
        )
        try:
            resp = await self.client.aio.models.generate_content(model=self.spec.model, contents=contents, config=config)
        except errors.APIError as e:
            raise AdapterError(f"{self.spec.key}: HTTP {e.code}: {str(e.message)[:300]}") from e

        text = ""
        finish = None
        if resp.candidates:
            cand = resp.candidates[0]
            finish = cand.finish_reason.name if cand.finish_reason else None
            if cand.content and cand.content.parts:
                text = "".join(p.text for p in cand.content.parts if p.text and not p.thought)
        u = resp.usage_metadata
        return Completion(
            text=text,
            tokens_in=(u.prompt_token_count or 0) if u else 0,
            tokens_out=(u.candidates_token_count or 0) if u else 0,
            reasoning_tokens=(u.thoughts_token_count or 0) if u else 0,
            finish_reason=finish,
            model_version=resp.model_version,
            raw_meta={"response_id": resp.response_id},
        )

    async def list_models(self) -> list[str]:
        pager = await self.client.aio.models.list()
        return [m.name.removeprefix("models/") async for m in pager]
