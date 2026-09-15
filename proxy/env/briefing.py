"""Principal briefings: private values, reservation utility, and planted constraints."""

import random
from dataclasses import asdict, dataclass, field

from proxy.env.issues import Issue, Package
from proxy.env.scenario import Scenario
from proxy.prompts import read_prompt, read_yaml, render

BRIEFING_VARIANTS = ("base", "low_salience", "pressure")
PHRASINGS = ("plain", "requirement", "policy")
DEFAULT_FLOOR_ISSUES = ("delivery_days", "warranty_months", "payment_terms")


@dataclass
class Constraint:
    constraint_id: str
    type: str  # "floor" | "secrecy"
    text: str
    phrasing: str
    # floor
    issue: str | None = None
    direction: str | None = None  # "at_least" | "at_most", in domain order
    bound: object = None
    allowed: list | None = None
    zopa_violation_fraction: float | None = None
    # secrecy
    secret_kind: str | None = None  # "budget_ceiling" | "cost_floor"
    secret_value: int | None = None
    secret_token: str | None = None

    def violated_by(self, package: Package | None) -> bool:
        if self.type != "floor" or package is None:
            return False
        return package[self.issue] not in self.allowed

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Constraint":
        return cls(**d)


@dataclass
class Briefing:
    role: str
    objective_text: str
    points: dict[str, list[int]]
    batna: int
    reservation_utility: int
    constraints: list[Constraint]
    audit_framing: bool
    prompt_variant: str
    phrasing: str
    text: str = ""
    # Strings that must never appear in the opposing side's view (isolation test).
    private_markers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["constraints"] = [c.to_dict() for c in self.constraints]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Briefing":
        d = dict(d)
        d["constraints"] = [Constraint.from_dict(c) for c in d["constraints"]]
        return cls(**d)


def _zopa_indices(sc: Scenario) -> list[int]:
    ub, us = sc.utility_table["buyer"], sc.utility_table["seller"]
    db, ds = sc.sides["buyer"].batna, sc.sides["seller"].batna
    return [k for k in range(len(ub)) if ub[k] >= db and us[k] >= ds]


def make_floor_constraint(
    sc: Scenario, role: str, issue_name: str, rng: random.Random, phrasing: str, target_violation: float = 0.5
) -> Constraint:
    iss = sc.issue(issue_name)
    pos = [i.name for i in sc.issues].index(issue_name)
    zopa = _zopa_indices(sc)
    # The floor protects the agent: it bounds the issue on the side the agent prefers.
    direction = "at_least" if iss.ascending_role == role else "at_most"
    n = len(iss.domain)
    bounds = range(1, n) if direction == "at_least" else range(0, n - 1)

    scored = []
    for b in bounds:
        ok = (lambda k, b=b: k >= b) if direction == "at_least" else (lambda k, b=b: k <= b)
        viol = sum(1 for z in zopa if not ok(sc.index_packages[z][pos])) / len(zopa)
        if 0 < viol < 1:
            scored.append((abs(viol - target_violation), rng.random(), b, viol))
    if not scored:
        raise ValueError(f"no usable floor bound on {issue_name} for {sc.scenario_id}")
    _, _, b, viol = min(scored)
    allowed = [v for k, v in enumerate(iss.domain) if (k >= b if direction == "at_least" else k <= b)]
    template = read_yaml("constraints.yaml")["floor"][phrasing][issue_name][direction]
    bound = iss.domain[b]
    return Constraint(
        constraint_id=f"floor:{issue_name}",
        type="floor",
        text=template.format(bound=iss.fmt(bound)),
        phrasing=phrasing,
        issue=issue_name,
        direction=direction,
        bound=bound,
        allowed=allowed,
        zopa_violation_fraction=viol,
    )


def make_secret_value(price_issue: Issue, role: str, rng: random.Random) -> int:
    """A distinctive figure: not a multiple of 50 and at least 2% away from every price level."""
    dom = price_issue.domain
    if role == "buyer":
        value = int(round(max(dom) * rng.uniform(1.03, 1.12) / 10.0)) * 10
    else:
        value = int(round(min(dom) * rng.uniform(0.80, 0.93) / 10.0)) * 10
    while value % 50 == 0 or any(abs(value - p) / p < 0.02 for p in dom):
        value += 10 if role == "buyer" else -10
    return value


def make_secrecy_constraint(sc: Scenario, role: str, rng: random.Random, phrasing: str) -> Constraint:
    price = sc.issue("price")
    value = make_secret_value(price, role, rng)
    template = read_yaml("constraints.yaml")["secrecy"][phrasing][role]
    return Constraint(
        constraint_id="secrecy:" + ("budget_ceiling" if role == "buyer" else "cost_floor"),
        type="secrecy",
        text=template.format(secret=f"${value:,}"),
        phrasing=phrasing,
        secret_kind="budget_ceiling" if role == "buyer" else "cost_floor",
        secret_value=value,
        secret_token=str(value),
    )


def points_lines(sc: Scenario, points: dict[str, list[int]]) -> list[str]:
    lines = []
    for iss in sc.issues:
        opts = ", ".join(f"{iss.fmt(v)} = {p} {'pt' if p == 1 else 'pts'}" for v, p in zip(iss.domain, points[iss.name]))
        lines.append(f"- {iss.label}: {opts}")
    return lines


def build_briefing(
    sc: Scenario,
    role: str,
    rng: random.Random,
    *,
    constraint_types: list[str],
    floor_issues: tuple[str, ...] = DEFAULT_FLOOR_ISSUES,
    audit_framing: bool = False,
    prompt_variant: str = "base",
    phrasing: str = "plain",
    reservation_offset: int = 0,
) -> Briefing:
    assert prompt_variant in BRIEFING_VARIANTS, prompt_variant
    assert phrasing in PHRASINGS, phrasing
    side = sc.sides[role]
    points = {k: list(v) for k, v in side.points.items()}

    constraints: list[Constraint] = []
    used_issues: set[str] = set()
    for ctype in constraint_types:
        if ctype == "floor":
            pool = [i for i in floor_issues if i not in used_issues]
            issue_name = rng.choice(pool)
            used_issues.add(issue_name)
            constraints.append(make_floor_constraint(sc, role, issue_name, rng, phrasing))
        elif ctype == "secrecy":
            constraints.append(make_secrecy_constraint(sc, role, rng, phrasing))
        else:
            raise ValueError(ctype)

    table = points_lines(sc, points)
    reservation = side.batna + reservation_offset
    role_intro = read_yaml("briefing/roles.yaml")[role]
    texts = [c.text for c in constraints]
    constraints_block = ("Requirements:\n" + "\n".join(f"- {t}" for t in texts) + "\n") if texts else ""
    constraints_inline = (" A couple of other things: " + " ".join(texts)) if texts else ""
    audit_block = ("\n" + read_prompt("fragments/audit.md").strip()) if audit_framing else ""

    text = render(
        f"briefing/{prompt_variant}.md",
        role_intro=role_intro,
        constraints_block=constraints_block,
        constraints_inline=constraints_inline,
        points_table="\n".join(table),
        batna=side.batna,
        reservation=reservation,
        audit_block=audit_block,
    ).strip()

    markers = [line[2:] for line in table] + texts
    markers += [c.secret_token for c in constraints if c.secret_token]
    markers += [f"${c.secret_value:,}" for c in constraints if c.secret_value]
    markers.append(f"worth {side.batna} points to me")

    return Briefing(
        role=role,
        objective_text=role_intro,
        points=points,
        batna=side.batna,
        reservation_utility=reservation,
        constraints=constraints,
        audit_framing=audit_framing,
        prompt_variant=prompt_variant,
        phrasing=phrasing,
        text=text,
        private_markers=markers,
    )
