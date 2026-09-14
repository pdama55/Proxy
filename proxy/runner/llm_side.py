from proxy.adapters.base import Adapter
from proxy.runner import render
from proxy.runner.parse import ParseError, parse_action
from proxy.runner.types import Action, View
from proxy.util import derive_seed


class LLMSide:
    kind = "llm"

    def __init__(self, adapter: Adapter, actor: str, seed: int):
        self.adapter = adapter
        self.actor = actor
        self.seed = seed if adapter.supports_seed else None

    def _seed(self, *parts) -> int | None:
        return None if self.seed is None else derive_seed(self.seed, *parts) % (2**31)

    async def act(self, view: View) -> Action:
        system = render.system_prompt(view)
        messages = [{"role": "user", "content": render.turn_prompt(view)}]
        totals = {"tokens_in": 0, "tokens_out": 0, "reasoning_tokens": 0, "latency_ms": 0, "cost_usd": 0.0}
        raws: list[str] = []
        errors: list[str] = []
        c = None
        for attempt in (1, 2):
            c = await self.adapter.complete(system, messages, seed=self._seed("turn", view.turn, attempt))
            raws.append(c.text)
            for k in totals:
                totals[k] += getattr(c, k)
            try:
                parsed = parse_action(c.text, view)
            except ParseError as e:
                errors.append(str(e))
                messages += [
                    {"role": "assistant", "content": c.text or "(empty response)"},
                    {"role": "user", "content": render.format_correction(str(e))},
                ]
                continue
            return Action(
                turn=view.turn,
                actor=self.actor,
                role=view.role,
                type=parsed.type,
                package=parsed.package,
                message=parsed.message,
                raw_output=raws[0],
                raw_retry_output=raws[1] if len(raws) > 1 else None,
                parse_ok=True,
                attempts=attempt,
                parse_errors=errors,
                finish_reason=c.finish_reason,
                model_version=c.model_version,
                **totals,
            )
        # Two failed parses: the turn becomes an empty message_only and the episode continues.
        return Action(
            turn=view.turn,
            actor=self.actor,
            role=view.role,
            type="message_only",
            package=None,
            message=None,
            raw_output=raws[0],
            raw_retry_output=raws[1],
            parse_ok=False,
            attempts=2,
            parse_errors=errors,
            finish_reason=c.finish_reason if c else None,
            model_version=c.model_version if c else None,
            **totals,
        )

    async def report(self, system: str, user: str) -> tuple[str, dict]:
        c = await self.adapter.complete(system, [{"role": "user", "content": user}], seed=self._seed("report"))
        return c.text, {
            "tokens_in": c.tokens_in,
            "tokens_out": c.tokens_out,
            "reasoning_tokens": c.reasoning_tokens,
            "latency_ms": c.latency_ms,
            "cost_usd": c.cost_usd,
            "finish_reason": c.finish_reason,
            "model_version": c.model_version,
        }

    def describe(self) -> dict:
        spec = self.adapter.spec
        return {
            "kind": self.kind,
            "model_key": spec.key,
            "provider": spec.provider,
            "model": spec.model,
            "params": spec.params,
            "max_tokens": spec.max_tokens,
            "seed": self.seed,
            "structured_output_mode": "json_block",
        }
