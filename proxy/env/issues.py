from dataclasses import dataclass
from typing import Any

ROLES = ("buyer", "seller")

# A package maps issue name -> a value from that issue's domain.
Package = dict[str, Any]


def other_role(role: str) -> str:
    return "seller" if role == "buyer" else "buyer"


@dataclass(frozen=True)
class Issue:
    name: str
    kind: str  # "ordinal" | "categorical" | "numeric"
    domain: tuple
    label: str
    # Which role prefers higher-index domain values. The other role prefers lower-index values.
    ascending_role: str

    def index(self, value: Any) -> int:
        return self.domain.index(value)

    def fmt(self, value: Any) -> str:
        if self.name == "price":
            return f"${value:,}"
        if self.name == "delivery_days":
            return f"{value} days"
        if self.name == "warranty_months":
            return f"{value} months"
        if self.name == "payment_terms":
            return PAYMENT_LABELS[value]
        return str(value)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "kind": self.kind,
            "domain": list(self.domain),
            "label": self.label,
            "ascending_role": self.ascending_role,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Issue":
        return cls(d["name"], d["kind"], tuple(d["domain"]), d["label"], d["ascending_role"])


PAYMENT_LABELS = {
    "upfront": "payment upfront",
    "net_30": "net 30",
    "net_60": "net 60",
    "net_90": "net 90",
}

DELIVERY_DOMAIN = (14, 30, 45, 60, 90)
WARRANTY_DOMAIN = (6, 12, 18, 24, 36)
PAYMENT_DOMAIN = ("upfront", "net_30", "net_60", "net_90")


def price_domain(base: int, levels: int = 9, step: float = 0.05) -> tuple:
    """Levels centred on base, rounded to $500, strictly increasing."""
    half = levels // 2
    vals = []
    for k in range(-half, levels - half):
        v = int(round(base * (1 + step * k) / 500.0)) * 500
        vals.append(v)
    out = sorted(set(vals))
    assert len(out) == levels, f"price levels collided for base {base}"
    return tuple(out)


def make_issues(base_price: int) -> list[Issue]:
    return [
        Issue("price", "numeric", price_domain(base_price), "Price", ascending_role="seller"),
        Issue("delivery_days", "ordinal", DELIVERY_DOMAIN, "Delivery time", ascending_role="seller"),
        Issue("warranty_months", "ordinal", WARRANTY_DOMAIN, "Warranty length", ascending_role="buyer"),
        Issue("payment_terms", "categorical", PAYMENT_DOMAIN, "Payment terms", ascending_role="buyer"),
    ]
