"""State isolation checks. One leak between sides invalidates every episode in a run."""

from proxy.env.briefing import Briefing, points_lines
from proxy.env.scenario import Scenario
from proxy.runner import render
from proxy.runner.types import PublicAction, View


class IsolationViolation(AssertionError):
    pass


def side_markers(sc: Scenario, role: str, briefing: Briefing | None) -> set[str]:
    """Strings derived from one side's private information. Includes the scenario's private values even
    when that side has no rendered briefing (the scripted counterparty)."""
    markers = set(briefing.private_markers) if briefing else set()
    markers.update(line[2:] for line in points_lines(sc, {k: list(v) for k, v in sc.sides[role].points.items()}))
    markers.add(f"worth {sc.sides[role].batna} points to me")
    return {m for m in markers if m}


def check_public_history(history: tuple[PublicAction, ...]) -> None:
    for a in history:
        if type(a) is not PublicAction:
            raise IsolationViolation(f"non-public object in public history: {type(a).__name__}")


def check_view(view: View, other_markers: set[str], own_markers: set[str]) -> None:
    """The view's rendered prompt, excluding the public history (which legitimately carries whatever the
    other side chose to say), must contain no private marker of the other side. A marker both sides
    share by coincidence (e.g. equal BATNAs) is exempt; one that merely appears in this side's text is not."""
    check_public_history(view.public_history)
    if view.briefing is None:
        return
    history = render.history_text(view.issues, view.public_history, view.role)
    text = (render.system_prompt(view) + "\n" + render.turn_prompt(view)).replace(history, "")
    for m in other_markers - own_markers:
        if m in text:
            raise IsolationViolation(f"private marker of the other side found in {view.role}'s view: {m!r}")
