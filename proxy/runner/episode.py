"""The episode loop. Generates and persists; never scores."""

import datetime as dt
import subprocess
from functools import lru_cache

from proxy import REPO_ROOT
from proxy.adapters import AdapterError, AdapterFactory
from proxy.config import EpisodeSpec, ModelSpec
from proxy.counterparty.scripted import ScriptedCounterparty, ScriptedParams
from proxy.env.benchmarks import compute_outcomes
from proxy.env.briefing import build_briefing
from proxy.env.issues import other_role
from proxy.env.scenario import generate_scenario
from proxy.prompts import prompt_template_hash
from proxy.runner import render
from proxy.runner.isolation import check_view, side_markers
from proxy.runner.llm_side import LLMSide
from proxy.runner.types import Action, View
from proxy.util import rng_for

SCHEMA_VERSION = "episode-v1"
# Bump when episode generation behavior changes; it is part of every episode id.
RUNNER_VERSION = "runner-v2"


@lru_cache(maxsize=1)
def harness_commit() -> str | None:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=5)
        dirty = subprocess.run(["git", "status", "--porcelain", "proxy", "prompts"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=5)
        return out.stdout.strip() + ("-dirty" if dirty.stdout.strip() else "") if out.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


async def run_episode(
    spec: EpisodeSpec,
    models: dict[str, ModelSpec],
    factory: AdapterFactory | None,
    *,
    config_hash: str = "",
    run_name: str = "",
    agent_override=None,
    debug_isolation: bool = True,
) -> dict:
    sc = generate_scenario(spec.scenario_seed)
    pair = spec.pairing_seed()
    agent_role = spec.agent_role
    cp_role = other_role(agent_role)

    agent_briefing = build_briefing(
        sc,
        agent_role,
        rng_for(pair, "agent-briefing"),
        constraint_types=spec.constraint_set,
        floor_issues=tuple(spec.floor_issues),
        audit_framing=spec.audit_framing,
        prompt_variant=spec.briefing_variant,
        phrasing=spec.phrasing,
    )
    first_mover = "agent" if rng_for(pair, "first-mover").random() < 0.5 else "counterparty"

    if agent_override is not None:
        agent = agent_override
    else:
        agent = LLMSide(factory.get(models[spec.model]), "agent", seed=rng_for(pair, "agent-seed", spec.replicate).getrandbits(31))

    cp_briefing = None
    if spec.counterparty_kind == "scripted":
        cp_params = dict(spec.counterparty_params)
        cp_params["probe_moves"] = tuple(cp_params.get("probe_moves", ()))
        counterparty = ScriptedCounterparty(
            sc,
            cp_role,
            ScriptedParams(**cp_params),
            [c for c in agent_briefing.constraints if c.type == "floor"],
            seed=pair,
        )
    else:
        cp_briefing = build_briefing(sc, cp_role, rng_for(pair, "cp-briefing"), constraint_types=[])
        counterparty = LLMSide(factory.get(models[spec.counterparty_model]), "counterparty", seed=rng_for(pair, "cp-seed", spec.replicate).getrandbits(31))

    agent_markers = side_markers(sc, agent_role, agent_briefing)
    cp_markers = side_markers(sc, cp_role, cp_briefing)

    actions: list[Action] = []
    reason, final_package, error = "turn_cap", None, None
    # The agent always gets the last move, so it can accept or refuse the counterparty's final offer. When the
    # agent moves first, that takes one extra turn.
    last_turn_is_agent = ((spec.turn_cap - 1) % 2 == 0) == (first_mover == "agent")
    turn_cap = spec.turn_cap if last_turn_is_agent else spec.turn_cap + 1
    try:
        for turn in range(turn_cap):
            agent_turn = (turn % 2 == 0) == (first_mover == "agent")
            side, role, briefing = (agent, agent_role, agent_briefing) if agent_turn else (counterparty, cp_role, cp_briefing)
            view = View(
                role=role,
                briefing=briefing,
                issues=tuple(sc.issues),
                public_history=tuple(a.public() for a in actions),
                turn=turn,
                turn_cap=turn_cap,
            )
            if debug_isolation:
                if agent_turn:
                    check_view(view, cp_markers, agent_markers)
                else:
                    check_view(view, agent_markers, cp_markers)
            action = await side.act(view)
            assert action.role == role and action.turn == turn
            actions.append(action)
            if action.type == "accept":
                reason = "accept"
                final_package = view.last_offer_by(other_role(role)).package
                break
            if action.type == "walk_away":
                reason = "walk_away"
                break
    except AdapterError as e:
        reason, error = "error", str(e)

    outcomes = compute_outcomes(sc, agent_role, final_package) if reason != "error" else None

    report = None
    if reason != "error":
        public = [a.public() for a in actions]
        system, user = render.report_messages(
            agent_briefing, tuple(sc.issues), public, reason, final_package, turn_cap, spec.report_variant
        )
        try:
            text, meta = await agent.report(system, user)
            report = {"variant": spec.report_variant, "system": system, "prompt": user, "text": text, **meta}
        except AdapterError as e:
            reason, error = "error", f"report failed: {e}"

    agent_actions = [a for a in actions if a.actor == "agent"]
    cost = sum(a.cost_usd for a in actions) + ((report or {}).get("cost_usd") or 0.0)
    versions = sorted({a.model_version for a in agent_actions if a.model_version} | ({report["model_version"]} if report and report.get("model_version") else set()))

    return {
        "schema_version": SCHEMA_VERSION,
        "runner_version": RUNNER_VERSION,
        "episode_id": spec.episode_id(),
        "run": run_name,
        "config_hash": config_hash,
        "harness_commit": harness_commit(),
        "prompt_template_hash": prompt_template_hash(),
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "spec": spec.model_dump(),
        "scenario": sc.to_dict(),
        "condition": {
            "outcome_target": spec.outcome_target,
            "audit_framing": spec.audit_framing,
            "briefing_variant": spec.briefing_variant,
            "phrasing": spec.phrasing,
            "report_variant": spec.report_variant,
            "counterparty_kind": spec.counterparty_kind,
            "counterparty_params": spec.counterparty_params,
            "first_mover": first_mover,
            "effective_turn_cap": turn_cap,
        },
        "agent": {
            "model": spec.model,
            "model_versions": versions,
            **agent.describe(),
        },
        "counterparty": counterparty.describe(),
        "briefing": agent_briefing.to_dict(),
        "counterparty_briefing": cp_briefing.to_dict() if cp_briefing else None,
        "actions": [a.to_dict() for a in actions],
        "termination": {
            "reason": reason,
            "final_package": final_package,
            "turns_used": len(actions),
            "error": error,
        },
        "outcomes": outcomes,
        "report": report,
        "stats": {
            "cost_usd": cost,
            "agent_parse_failures": sum(1 for a in agent_actions if not a.parse_ok),
            "agent_retries": sum(1 for a in agent_actions if a.attempts > 1),
            "agent_tokens_in": sum(a.tokens_in for a in agent_actions),
            "agent_tokens_out": sum(a.tokens_out for a in agent_actions),
            "isolation_checked": debug_isolation,
        },
        "detectors": {},
        "scores": {},
    }
