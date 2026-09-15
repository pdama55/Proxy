"""Loads versioned prompt files and records a hash of every file a render used."""

from functools import lru_cache
from string import Template

import yaml

from proxy import PROMPTS_DIR
from proxy.util import sha256


@lru_cache(maxsize=None)
def read_prompt(rel_path: str) -> str:
    return (PROMPTS_DIR / rel_path).read_text(encoding="utf-8")


@lru_cache(maxsize=None)
def read_yaml(rel_path: str) -> dict:
    return yaml.safe_load(read_prompt(rel_path))


def render(rel_path: str, **kwargs) -> str:
    return Template(read_prompt(rel_path)).substitute(**kwargs)


def files_hash(rel_paths: list[str]) -> str:
    parts = [f"{p}\n{sha256(read_prompt(p))}" for p in sorted(set(rel_paths))]
    return sha256("\n".join(parts))


# Every prompt file an agent-side episode can touch. Hashing the whole set, rather than the subset a
# given episode used, means any edit to any prompt changes the recorded hash.
AGENT_PROMPT_FILES = [
    "agent/system.md",
    "agent/turn.md",
    "agent/format_correction.md",
    "agent/report_context.md",
    "report/system.md",
    "report/open.md",
    "report/directive.md",
    "briefing/base.md",
    "briefing/low_salience.md",
    "briefing/pressure.md",
    "briefing/roles.yaml",
    "fragments/audit.md",
    "constraints.yaml",
    "counterparty/messages.yaml",
]


def prompt_template_hash() -> str:
    return files_hash(AGENT_PROMPT_FILES)
