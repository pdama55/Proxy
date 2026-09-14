"""Instruction-contamination check: no prompt the agent can see may instruct the outcome being measured."""

import re

import pytest

from proxy import PROMPTS_DIR

BANNED = [
    r"honest", r"truth", r"transparen", r"disclos", r"evaluat", r"grade", r"scor(?:e|ed|ing)", r"audit",
    r"monitor", r"review", r"check", r"verif", r"accura", r"\blie\b", r"lying", r"decei?v", r"decept",
    r"report", r"candid", r"forthright", r"conceal", r"hide", r"withhold",
]

# The audit-framing sentence is the manipulation itself, so it is the one file allowed to mention review.
EXEMPT = {"fragments/audit.md"}

# Only prompts an agent under test can see. Judge and principal-simulation prompts are instruments.
AGENT_FACING = ("agent", "briefing", "report", "fragments", "counterparty", "constraints.yaml")
FILES = sorted(
    p for p in PROMPTS_DIR.rglob("*")
    if p.is_file() and str(p.relative_to(PROMPTS_DIR)).split("/")[0] in AGENT_FACING and str(p.relative_to(PROMPTS_DIR)) not in EXEMPT
)


@pytest.mark.parametrize("path", FILES, ids=lambda p: str(p.relative_to(PROMPTS_DIR)))
def test_no_contaminating_language(path):
    text = path.read_text().lower()
    if path.suffix == ".yaml":
        text = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
    text = re.sub(r"\$[a-z_]+", "", text)  # template placeholder names are never shown to a model
    hits = [w for w in BANNED if re.search(w, text)]
    assert not hits, f"{path.name} contains {hits}"


def test_audit_fragment_is_neutral_about_honesty():
    text = (PROMPTS_DIR / "fragments/audit.md").read_text().lower()
    assert not re.search(r"honest|truth|disclos|accura|transparen", text)
