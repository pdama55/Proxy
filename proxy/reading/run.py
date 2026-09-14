"""Reads every episode of a run with the reader agent, then writes the pilot review."""

import asyncio
import sys
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from proxy.adapters import AdapterFactory, BudgetExceeded, SpendTracker
from proxy.config import ModelSpec
from proxy.reading.reader import pilot_checks, pilot_report_markdown, read_episode, reader_tallies, synthesize
from proxy.store import EpisodeStore


class ReadingConfig(BaseModel):
    name: str
    reader: str
    spend_ceiling_usd: float = 10.0
    provider_concurrency: dict[str, int] = Field(default_factory=lambda: {"default": 4})
    request_timeout_s: float = 600.0
    gates: dict

    @classmethod
    def load(cls, path) -> "ReadingConfig":
        return cls(**yaml.safe_load(Path(path).read_text()))


async def read_run(store: EpisodeStore, cfg: ReadingConfig, models: dict[str, ModelSpec], run: str, *, force: bool = False, factory=None) -> dict:
    spend = SpendTracker(cfg.spend_ceiling_usd)
    factory = factory or AdapterFactory(spend, cfg.provider_concurrency, cfg.request_timeout_s)
    reader = factory.get(models[cfg.reader])
    paths = list(store.iter_paths(run))
    if not paths:
        raise SystemExit(f"no episodes in run {run}")
    slots = asyncio.Semaphore(max(sum(cfg.provider_concurrency.values()), 2))
    done = 0

    async def one(path):
        nonlocal done
        async with slots:
            ep = store.load(path)
            await read_episode(ep, reader, force=force)
            store.write(ep)
            done += 1
            sev = ((ep["diagnostics"]["reader"].get("findings") or {}).get("severity")) or "reader failed"
            print(f"  read [{done}/{len(paths)}] {ep['episode_id']} {ep['spec']['model']} {ep['spec']['outcome_target']} -> {sev}", file=sys.stderr)

    aborted = None
    tasks = [asyncio.create_task(one(p)) for p in paths]
    try:
        for fut in asyncio.as_completed(tasks):
            await fut
    except BudgetExceeded as e:
        aborted = str(e)
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    episodes = [store.load(p) for p in paths]
    checks = pilot_checks(episodes, cfg.gates)
    tallies = reader_tallies(episodes)
    synthesis = "## Review\n\n(skipped: reading was aborted by the spend ceiling)" if aborted else await synthesize(episodes, checks, tallies, reader)
    report = pilot_report_markdown(run, checks, tallies, synthesis, episodes, cfg.reader)
    out = store.runs_dir / run / "pilot_review.md"
    out.write_text(report)
    return {"review": str(out), "read": tallies["read"], "reader_failures": tallies["failed"], "aborted": aborted,
            "failed_checks": [c["check"] for c in checks if c["passed"] is False], "spend": spend.summary()}
