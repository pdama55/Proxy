"""Runs the judge and principal-simulation passes over stored episodes. Resumable and idempotent."""

import asyncio
import sys
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from proxy.adapters import AdapterFactory, BudgetExceeded, SpendTracker
from proxy.config import ModelSpec
from proxy.scoring.judge import JudgeConflict, judge_episode
from proxy.scoring.principal import simulate_principal
from proxy.scoring.score import SCORING_VERSION, score_episode
from proxy.store import EpisodeStore

TASKS = ("disclosure", "characterization", "principal")


class JudgingConfig(BaseModel):
    name: str
    judges: list[str]
    primary_judge: str
    principal_models: list[str] = Field(default_factory=list)
    tasks: list[str] = list(TASKS)
    spend_ceiling_usd: float = 20.0
    provider_concurrency: dict[str, int] = Field(default_factory=lambda: {"default": 4})
    request_timeout_s: float = 300.0
    via_openrouter: bool = False

    @classmethod
    def load(cls, path: str | Path) -> "JudgingConfig":
        cfg = cls(**yaml.safe_load(Path(path).read_text()))
        assert cfg.primary_judge in cfg.judges, "primary_judge must be one of judges"
        assert set(cfg.tasks) <= set(TASKS), f"unknown tasks {set(cfg.tasks) - set(TASKS)}"
        return cfg


async def judge_store(
    store: EpisodeStore,
    cfg: JudgingConfig,
    models: dict[str, ModelSpec],
    *,
    run: str | None = None,
    limit: int | None = None,
    force: bool = False,
    factory=None,
) -> dict:
    spend = SpendTracker(cfg.spend_ceiling_usd)
    factory = factory or AdapterFactory(spend, cfg.provider_concurrency, cfg.request_timeout_s, via_openrouter=cfg.via_openrouter)
    judges = [factory.get(models[k]) for k in cfg.judges]
    sims = [factory.get(models[k]) for k in cfg.principal_models] if "principal" in cfg.tasks else []
    judge_tasks = [t for t in cfg.tasks if t != "principal"]

    paths = list(store.iter_paths(run))
    if limit is not None:
        paths = paths[:limit]
    slots = asyncio.Semaphore(max(sum(cfg.provider_concurrency.values()), 2))
    counts = {"episodes": 0, "skipped_error": 0, "conflicts": 0}

    async def one(path):
        async with slots:
            ep = store.load(path)
            if ep["termination"]["reason"] == "error":
                counts["skipped_error"] += 1
                return
            if (ep.get("scores") or {}).get("scoring_version") != SCORING_VERSION:
                ep = score_episode(ep)
            family = models[ep["spec"]["model"]].family if ep["spec"]["model"] in models else None
            try:
                for j in judges:
                    await judge_episode(ep, j, agent_family=family, tasks=judge_tasks, force=force)
                for s in sims:
                    await simulate_principal(ep, s, agent_family=family, force=force)
            except JudgeConflict as e:
                counts["conflicts"] += 1
                print(f"  {ep['episode_id']}: {e}", file=sys.stderr)
                return
            store.write(ep)
            counts["episodes"] += 1

    tasks = [asyncio.create_task(one(p)) for p in paths]
    aborted = None
    try:
        for fut in asyncio.as_completed(tasks):
            await fut
    except BudgetExceeded as e:
        aborted = str(e)
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
    return {**counts, "aborted": aborted, "spend": spend.summary()}
