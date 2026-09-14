"""Seeded scenario generation.

Utilities are integer points in [0, 100]: each side's per-issue maximum points sum to 100 and every
per-level value is an integer. Normalized utility is points / 100, so all benchmarks are exact.
"""

import itertools
import random
from dataclasses import dataclass, field
from functools import cached_property

from proxy.env.issues import ROLES, Issue, Package, make_issues, other_role

GENERATOR_VERSION = "scenario-v1"


@dataclass(frozen=True)
class SideValues:
    weights: dict[str, int]  # issue -> max points; sums to 100
    points: dict[str, tuple[int, ...]]  # issue -> points per domain level, aligned to issue.domain
    batna: int  # no-deal utility in points

    def to_dict(self) -> dict:
        return {"weights": self.weights, "points": {k: list(v) for k, v in self.points.items()}, "batna": self.batna}

    @classmethod
    def from_dict(cls, d: dict) -> "SideValues":
        return cls(d["weights"], {k: tuple(v) for k, v in d["points"].items()}, d["batna"])


@dataclass
class Scenario:
    scenario_id: str
    seed: int
    issues: list[Issue]
    sides: dict[str, SideValues]
    generator_version: str = GENERATOR_VERSION
    _derived: dict | None = field(default=None, repr=False)

    # ---- package space -------------------------------------------------
    @cached_property
    def index_packages(self) -> list[tuple[int, ...]]:
        return list(itertools.product(*[range(len(i.domain)) for i in self.issues]))

    def to_package(self, idx: tuple[int, ...]) -> Package:
        return {iss.name: iss.domain[k] for iss, k in zip(self.issues, idx)}

    def to_index(self, package: Package) -> tuple[int, ...]:
        return tuple(iss.index(package[iss.name]) for iss in self.issues)

    def issue(self, name: str) -> Issue:
        for i in self.issues:
            if i.name == name:
                return i
        raise KeyError(name)

    # ---- utility ----------------------------------------------------------
    def points_idx(self, role: str, idx: tuple[int, ...]) -> int:
        sv = self.sides[role]
        return sum(sv.points[iss.name][k] for iss, k in zip(self.issues, idx))

    def points(self, role: str, package: Package) -> int:
        return self.points_idx(role, self.to_index(package))

    def utility(self, role: str, package: Package | None) -> float:
        if package is None:
            return self.sides[role].batna / 100.0
        return self.points(role, package) / 100.0

    @cached_property
    def utility_table(self) -> dict[str, list[int]]:
        return {r: [self.points_idx(r, idx) for idx in self.index_packages] for r in ROLES}

    # ---- derived benchmarks ----------------------------------------------
    @property
    def derived(self) -> dict:
        if self._derived is None:
            from proxy.env.benchmarks import compute_derived

            self._derived = compute_derived(self)
        return self._derived

    def to_dict(self) -> dict:
        return {
            "scenario_id": self.scenario_id,
            "seed": self.seed,
            "generator_version": self.generator_version,
            "issues": [i.to_dict() for i in self.issues],
            "sides": {r: self.sides[r].to_dict() for r in ROLES},
            "derived": self.derived,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Scenario":
        return cls(
            scenario_id=d["scenario_id"],
            seed=d["seed"],
            issues=[Issue.from_dict(i) for i in d["issues"]],
            sides={r: SideValues.from_dict(d["sides"][r]) for r in ROLES},
            generator_version=d.get("generator_version", GENERATOR_VERSION),
            _derived=d.get("derived"),
        )


# ---------------------------------------------------------------------------
# generation


def _random_weights(rng: random.Random, names: list[str], min_w: int = 10) -> dict[str, int]:
    while True:
        cuts = sorted(rng.sample(range(1, 100), len(names) - 1))
        parts = [b - a for a, b in zip([0] + cuts, cuts + [100])]
        if min(parts) >= min_w:
            return dict(zip(names, parts))


def _monotone_points(rng: random.Random, n_levels: int, max_pts: int) -> list[int]:
    """Non-decreasing integers from 0 to max_pts across n_levels (in preferred order).

    Shape is a power curve with a random exponent (concave through convex) plus small jitter, so
    value functions vary across scenarios without jagged jumps between adjacent levels.
    """
    exponent = rng.uniform(0.6, 1.6)
    raw = []
    for k in range(n_levels):
        x = (k / (n_levels - 1)) ** exponent
        if 0 < k < n_levels - 1:
            x = min(1.0, max(0.0, x + rng.uniform(-0.05, 0.05)))
        raw.append(x)
    pts = [int(round(x * max_pts)) for x in raw]
    for k in range(1, len(pts)):
        pts[k] = max(pts[k], pts[k - 1])
    pts[0], pts[-1] = 0, max_pts
    return pts


def _side_values(rng: random.Random, issues: list[Issue], role: str) -> tuple[dict, dict]:
    weights = _random_weights(rng, [i.name for i in issues])
    points = {}
    for iss in issues:
        pts = _monotone_points(rng, len(iss.domain), weights[iss.name])
        # pts is in preferred order; ascending_role prefers higher indices.
        points[iss.name] = tuple(pts if iss.ascending_role == role else list(reversed(pts)))
    return weights, points


def is_integrative(issues: list[Issue], weights: dict[str, dict[str, int]], min_ratio: float = 1.5) -> bool:
    """True when some pair of opposed issues is weighted in different proportions by the two sides,
    so that trading one for the other is Pareto-improving."""
    names = [i.name for i in issues]
    b, s = weights["buyer"], weights["seller"]
    for x, y in itertools.permutations(names, 2):
        if (b[x] / b[y]) >= min_ratio * (s[x] / s[y]):
            return True
    return False


def generate_scenario(
    seed: int,
    *,
    base_price_range: tuple[int, int] = (20_000, 90_000),
    batna_range: tuple[int, int] = (25, 45),
    zopa_fraction_range: tuple[float, float] = (0.08, 0.45),
    min_integrative_gain: int = 8,
    max_attempts: int = 500,
) -> Scenario:
    rng = random.Random(seed)
    for _ in range(max_attempts):
        base = rng.randrange(base_price_range[0], base_price_range[1] + 1, 1000)
        issues = make_issues(base)
        w, p = {}, {}
        for role in ROLES:
            w[role], p[role] = _side_values(rng, issues, role)
        if not is_integrative(issues, w):
            continue
        batnas = {r: rng.randint(*batna_range) for r in ROLES}
        sc = Scenario(
            scenario_id=f"s{seed}",
            seed=seed,
            issues=issues,
            sides={r: SideValues(w[r], p[r], batnas[r]) for r in ROLES},
        )
        table = sc.utility_table
        joint = [a + b for a, b in zip(table["buyer"], table["seller"])]
        mid_idx = tuple(len(i.domain) // 2 for i in issues)
        mid_joint = sc.points_idx("buyer", mid_idx) + sc.points_idx("seller", mid_idx)
        if max(joint) - mid_joint < min_integrative_gain:
            continue
        in_zopa = sum(1 for a, b in zip(table["buyer"], table["seller"]) if a >= batnas["buyer"] and b >= batnas["seller"])
        frac = in_zopa / len(table["buyer"])
        if not (zopa_fraction_range[0] <= frac <= zopa_fraction_range[1]):
            continue
        assert_integrative(sc)
        return sc
    raise RuntimeError(f"could not generate a valid scenario for seed {seed}")


def assert_integrative(sc: Scenario) -> None:
    w = {r: sc.sides[r].weights for r in ROLES}
    assert is_integrative(sc.issues, w), f"{sc.scenario_id} is not integrative"
    for iss in sc.issues:
        b, s = sc.sides["buyer"].points[iss.name], sc.sides["seller"].points[iss.name]
        # opposed orderings on every issue
        assert (b[0] - b[-1]) * (s[0] - s[-1]) < 0, f"{iss.name} is not opposed"
    assert other_role("buyer") == "seller"
