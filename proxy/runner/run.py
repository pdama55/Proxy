"""Runs an experiment grid concurrently. Resumable: completed episodes on disk are skipped, and an episode
stored as an error is retried until it has had MAX_ATTEMPTS attempts (the preregistered single retry)."""

import asyncio
import sys
import time
from collections import Counter

from proxy.adapters import AdapterFactory, BudgetExceeded, SpendTracker
from proxy.config import EpisodeSpec, ExperimentConfig, ModelSpec
from proxy.runner.episode import run_episode
from proxy.store import EpisodeStore

MAX_ATTEMPTS = 2


def interleave(specs: list[EpisodeSpec]) -> list[EpisodeSpec]:
    """Round-robin across models, keeping each model's own order, so every provider starts working at once."""
    by_model: dict[str, list[EpisodeSpec]] = {}
    for s in specs:
        by_model.setdefault(s.model, []).append(s)
    queues = list(by_model.values())
    out = []
    for i in range(max((len(q) for q in queues), default=0)):
        out.extend(q[i] for q in queues if i < len(q))
    return out


def prior_attempts(store: EpisodeStore, run_name: str, episode_id: str) -> int | None:
    """None if the episode should not run again; otherwise how many attempts it has had (0 if never run)."""
    if not store.exists(run_name, episode_id):
        return 0
    rec = store.load(store.path(run_name, episode_id))
    if rec["termination"]["reason"] != "error":
        return None
    attempts = rec.get("attempt", 1)
    return attempts if attempts < MAX_ATTEMPTS else None


async def run_experiment(
    cfg: ExperimentConfig,
    models: dict[str, ModelSpec],
    store: EpisodeStore,
    *,
    run_name: str | None = None,
    limit: int | None = None,
    only_models: list[str] | None = None,
    factory=None,
) -> dict:
    run_name = run_name or cfg.name
    specs = cfg.episode_specs()
    if only_models:
        specs = [s for s in specs if s.model in only_models]
    missing = [k for k in {s.model for s in specs} | ({cfg.counterparty.llm_model} - {None}) if k not in models]
    if missing:
        raise SystemExit(f"models not in models.yaml: {missing}")
    attempts = {s.episode_id(): prior_attempts(store, run_name, s.episode_id()) for s in specs}
    todo = interleave([s for s in specs if attempts[s.episode_id()] is not None])
    already_done = len(specs) - len(todo)
    if limit is not None:
        todo = todo[:limit]
    print(f"{run_name}: {len(specs)} episodes in grid, {already_done} already done, running {len(todo)}")

    spend = SpendTracker(cfg.spend_ceiling_usd)
    factory = factory or AdapterFactory(spend, cfg.provider_concurrency, cfg.request_timeout_s, via_openrouter=cfg.via_openrouter)
    config_hash = cfg.config_hash()
    # Episode slots per provider, so one slow provider never occupies every slot while others sit idle.
    provider_slots: dict[str, asyncio.Semaphore] = {}

    def slots_for(spec: EpisodeSpec) -> asyncio.Semaphore:
        provider = models[spec.model].provider
        if provider not in provider_slots:
            n = cfg.provider_concurrency.get(provider, cfg.provider_concurrency.get("default", 4))
            provider_slots[provider] = asyncio.Semaphore(max(n * 2, 2))
        return provider_slots[provider]
    counts: Counter = Counter()
    t0 = time.monotonic()

    async def one(spec: EpisodeSpec):
        async with slots_for(spec):
            # Another process may have finished this episode since the plan was made.
            if prior_attempts(store, run_name, spec.episode_id()) != attempts[spec.episode_id()]:
                counts["skipped_done_elsewhere"] += 1
                return
            rec = await run_episode(
                spec, models, factory, config_hash=config_hash, run_name=run_name, debug_isolation=cfg.debug_isolation
            )
            rec["attempt"] = attempts[spec.episode_id()] + 1
            store.write(rec)
            counts[rec["termination"]["reason"]] += 1
            counts["parse_failures"] += rec["stats"]["agent_parse_failures"]
            done = sum(v for k, v in counts.items() if k not in ("parse_failures", "skipped_done_elsewhere"))
            print(
                f"  [{done}/{len(todo)}] {spec.model} {spec.outcome_target} audit={int(spec.audit_framing)} "
                f"{spec.agent_role} seed={spec.scenario_seed} -> {rec['termination']['reason']} "
                f"(${spend.spent_usd:.3f})",
                file=sys.stderr,
            )

    tasks = [asyncio.create_task(one(s)) for s in todo]
    aborted = None
    try:
        for fut in asyncio.as_completed(tasks):
            await fut
    except BudgetExceeded as e:
        aborted = str(e)
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    summary = {
        "run": run_name,
        "attempted": len(todo),
        "outcomes": dict(counts),
        "aborted": aborted,
        "elapsed_s": round(time.monotonic() - t0, 1),
        "spend": spend.summary(),
    }
    return summary
