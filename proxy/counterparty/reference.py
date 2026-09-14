"""Rule-based reference agent, used to calibrate counterparty parameters and in tests.

It sees only a View (its own briefing and the public history), exactly like an LLM agent.
"""

import itertools

from proxy.env.issues import other_role
from proxy.runner.types import Action, View


class ReferenceAgent:
    kind = "reference"

    def __init__(
        self,
        concession_exponent: float = 1.0,
        respect_constraints: bool = True,
        leak_secret: bool = False,
        message: str = "Here is our proposal.",
        report_text: str = "We reached the end of the negotiation.",
    ):
        self.e = concession_exponent
        self.respect_constraints = respect_constraints
        self.leak_secret = leak_secret
        self.message = message
        self.report_text = report_text

    def _points(self, view: View, package) -> int:
        return sum(view.briefing.points[i.name][i.index(package[i.name])] for i in view.issues)

    def _compliant(self, view: View, package) -> bool:
        return not any(c.violated_by(package) for c in view.briefing.constraints)

    async def act(self, view: View) -> Action:
        b = view.briefing
        issues = view.issues
        packages = [dict(zip([i.name for i in issues], vals)) for vals in itertools.product(*[i.domain for i in issues])]
        max_pts = sum(max(b.points[i.name]) for i in issues)
        x = min(1.0, view.turn / max(0.75 * view.turn_cap, 1))
        tau = max_pts - (max_pts - b.reservation_utility) * x ** (1.0 / self.e)
        last_turn = view.turn >= view.turn_cap - 2

        their = view.last_offer_by(other_role(view.role))
        ok = (lambda p: True) if not self.respect_constraints else (lambda p: self._compliant(view, p))
        if their is not None:
            pts = self._points(view, their.package)
            if ok(their.package) and (pts >= tau or (last_turn and pts >= b.reservation_utility)):
                return self._action(view, "accept", None, "Agreed.")
        if last_turn:
            return self._action(view, "walk_away", None, "We can't reach terms that work for us.")

        cands = [p for p in packages if self._points(view, p) >= tau and ok(p)]
        if not cands:
            cands = [max(packages, key=lambda p: self._points(view, p))]
        if their is not None:
            idx = {i.name: i.index for i in issues}
            dist = lambda p: sum(abs(idx[n](p[n]) - idx[n](their.package[n])) for n in p)
            offer = min(cands, key=lambda p: (dist(p), -self._points(view, p)))
        else:
            offer = max(cands, key=lambda p: self._points(view, p))
        msg = self.message
        if self.leak_secret:
            secrets = [c for c in b.constraints if c.type == "secrecy"]
            if secrets:
                msg += f" Our number is ${secrets[0].secret_value:,}."
        return self._action(view, "offer", offer, msg)

    async def report(self, system: str, user: str) -> tuple[str, dict]:
        return self.report_text, {"tokens_out": 0}

    def _action(self, view: View, atype: str, package, message: str) -> Action:
        return Action(
            turn=view.turn,
            actor="agent",
            role=view.role,
            type=atype,
            package=package,
            message=message,
            raw_output="",
            parse_ok=True,
        )

    def describe(self) -> dict:
        return {
            "kind": self.kind,
            "concession_exponent": self.e,
            "respect_constraints": self.respect_constraints,
            "leak_secret": self.leak_secret,
        }
