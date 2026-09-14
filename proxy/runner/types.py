from dataclasses import asdict, dataclass, field

from proxy.env.briefing import Briefing
from proxy.env.issues import Issue, Package

ACTION_TYPES = ("offer", "accept", "walk_away", "message_only")


@dataclass(frozen=True)
class PublicAction:
    """The only part of an action the other side ever sees."""

    turn: int
    role: str
    type: str
    package: Package | None
    message: str | None


@dataclass
class Action:
    turn: int
    actor: str  # "agent" | "counterparty"
    role: str
    type: str
    package: Package | None
    message: str | None
    raw_output: str  # exactly what the model emitted on the first attempt
    parse_ok: bool
    raw_retry_output: str | None = None  # the format-corrected attempt, if one was needed
    latency_ms: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    reasoning_tokens: int = 0
    cost_usd: float = 0.0
    attempts: int = 1
    parse_errors: list[str] = field(default_factory=list)
    finish_reason: str | None = None
    model_version: str | None = None
    move: str | None = None  # scripted counterparty move label (anchor, concede, hold, ...)

    def public(self) -> PublicAction:
        return PublicAction(self.turn, self.role, self.type, self.package, self.message)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class View:
    """Everything a side may condition on for one turn: its own briefing plus public history."""

    role: str
    briefing: Briefing | None  # None for a scripted counterparty, which holds its parameters itself
    issues: tuple[Issue, ...]
    public_history: tuple[PublicAction, ...]
    turn: int  # 0-indexed
    turn_cap: int

    def last_offer_by(self, role: str) -> PublicAction | None:
        for a in reversed(self.public_history):
            if a.role == role and a.type == "offer":
                return a
        return None


@dataclass
class Completion:
    text: str
    tokens_in: int = 0
    tokens_out: int = 0
    reasoning_tokens: int = 0
    latency_ms: int = 0
    finish_reason: str | None = None
    model_version: str | None = None
    cost_usd: float = 0.0
    raw_meta: dict = field(default_factory=dict)
