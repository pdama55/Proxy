"""Experiment and model configuration."""

import itertools
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, model_validator

from proxy import CONFIGS_DIR
from proxy.counterparty.scripted import ScriptedParams
from proxy.env.scenario import GENERATOR_VERSION
from proxy.prompts import prompt_template_hash
from proxy.util import derive_seed, hash_obj

PROVIDERS = ("anthropic", "openai", "gemini", "openrouter", "azure", "ollama", "vllm")


class ModelSpec(BaseModel):
    key: str
    provider: str
    model: str
    family: str
    tier: str  # frontier | mid | small (within its arm)
    # Order within the family, 1 = least capable. Used for the H4 capability trend.
    capability_rank: int | None = None
    open_weight: bool = False
    params: dict = Field(default_factory=dict)  # passed to the API verbatim; {} = provider defaults
    max_tokens: int = 16000
    # Name of the output-token limit parameter when a server rejects the provider default (for example
    # Mistral on Azure accepts only "max_tokens").
    token_param: str | None = None
    price_in_per_mtok: float = 0.0
    price_out_per_mtok: float = 0.0
    openrouter_id: str | None = None  # used when routing everything through OpenRouter
    openrouter_provider: dict | None = None  # OpenRouter provider-routing preferences
    notes: str = ""

    @model_validator(mode="after")
    def _check_provider(self):
        assert self.provider in PROVIDERS, f"{self.key}: unknown provider {self.provider}"
        return self

    def via_openrouter(self) -> "ModelSpec":
        if self.provider in ("openrouter", "ollama", "vllm"):
            return self
        assert self.openrouter_id, f"{self.key} has no openrouter_id"
        return self.model_copy(update={"provider": "openrouter", "model": self.openrouter_id, "params": {}})

    def cost(self, tokens_in: int, tokens_out: int) -> float:
        return (tokens_in * self.price_in_per_mtok + tokens_out * self.price_out_per_mtok) / 1e6


def load_models(path: Path | None = None) -> dict[str, ModelSpec]:
    path = path or CONFIGS_DIR / "models.yaml"
    raw = yaml.safe_load(path.read_text())
    return {k: ModelSpec(key=k, **v) for k, v in raw["models"].items()}


class CounterpartyConfig(BaseModel):
    kind: str = "scripted"  # scripted | llm
    llm_model: str | None = None
    # outcome target -> scripted parameters
    scripted: dict[str, dict] = Field(default_factory=dict)

    def params_for(self, target: str) -> ScriptedParams:
        d = dict(self.scripted[target])
        for key in ("probe_moves", "showcase_moves"):
            if key in d:
                d[key] = tuple(d[key])
        return ScriptedParams(**d)


class ExperimentConfig(BaseModel):
    name: str
    description: str = ""
    models: list[str]
    counterparty: CounterpartyConfig
    outcome_targets: list[str]
    audit_framing: list[bool] = [False]
    briefing_variants: list[str] = ["base"]
    phrasings: list[str] = ["plain"]
    report_variants: list[str] = ["open"]
    agent_roles: list[str] = ["buyer", "seller"]
    constraint_sets: list[list[str]] = [["floor", "secrecy"]]
    floor_issues: list[str] = ["delivery_days", "warranty_months", "payment_terms"]
    scenario_seeds: list[int]
    replicates: int = 1
    turn_cap: int = 16
    spend_ceiling_usd: float = 10.0
    provider_concurrency: dict[str, int] = Field(default_factory=lambda: {"default": 4})
    request_timeout_s: float = 300.0
    debug_isolation: bool = True
    via_openrouter: bool = False

    @classmethod
    def load(cls, path: str | Path) -> "ExperimentConfig":
        return cls(**yaml.safe_load(Path(path).read_text()))

    def config_hash(self) -> str:
        return hash_obj({"config": self.model_dump(), "prompts": prompt_template_hash(), "generator": GENERATOR_VERSION})

    def episode_specs(self) -> list["EpisodeSpec"]:
        specs = []
        grid = itertools.product(
            self.models,
            self.outcome_targets,
            self.audit_framing,
            self.briefing_variants,
            self.phrasings,
            self.report_variants,
            self.agent_roles,
            self.constraint_sets,
            self.scenario_seeds,
            range(self.replicates),
        )
        for model, target, audit, bvar, phr, rvar, role, cset, seed, rep in grid:
            specs.append(
                EpisodeSpec(
                    model=model,
                    outcome_target=target,
                    audit_framing=audit,
                    briefing_variant=bvar,
                    phrasing=phr,
                    report_variant=rvar,
                    agent_role=role,
                    constraint_set=list(cset),
                    scenario_seed=seed,
                    replicate=rep,
                    turn_cap=self.turn_cap,
                    counterparty_kind=self.counterparty.kind,
                    counterparty_model=self.counterparty.llm_model if self.counterparty.kind == "llm" else None,
                    counterparty_params=self.counterparty.params_for(target).to_dict()
                    if self.counterparty.kind == "scripted"
                    else {},
                    floor_issues=list(self.floor_issues),
                )
            )
        return specs


class EpisodeSpec(BaseModel):
    model: str
    outcome_target: str
    audit_framing: bool
    briefing_variant: str
    phrasing: str
    report_variant: str
    agent_role: str
    constraint_set: list[str]
    scenario_seed: int
    replicate: int
    turn_cap: int
    counterparty_kind: str
    counterparty_model: str | None
    counterparty_params: dict
    floor_issues: list[str]

    def episode_id(self) -> str:
        # Stable across unrelated config edits (adding models or seeds), so runs can resume and grow.
        from proxy.runner.episode import RUNNER_VERSION

        return hash_obj({"spec": self.model_dump(), "prompts": prompt_template_hash(), "generator": GENERATOR_VERSION, "runner": RUNNER_VERSION})[:16]

    def pairing_seed(self) -> int:
        """Seed for everything that must be identical across models and conditions: the briefing's
        constraint draws, who moves first, and the counterparty's message choices. Paired designs need
        these held fixed; replicates differ only in model sampling."""
        return derive_seed("pair", self.scenario_seed, self.agent_role, self.constraint_set)
