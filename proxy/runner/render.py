"""Renders views into prompt text. Only a View (own briefing + public history) is ever rendered."""

import json

from proxy.env.issues import Issue, Package
from proxy.prompts import read_prompt, render
from proxy.runner.types import PublicAction, View

FINAL_TURN_NOTE = (
    " This is the last turn of the negotiation. The other party will not get another turn, so an offer made now"
    " cannot be accepted."
)

ACTION_LABELS = {
    "offer": "made an offer",
    "accept": "accepted the other side's offer",
    "walk_away": "walked away",
    "message_only": "sent a message",
}


def format_package(issues: tuple[Issue, ...] | list[Issue], package: Package) -> str:
    return "; ".join(f"{i.label}: {i.fmt(package[i.name])}" for i in issues)


def issue_list(issues) -> str:
    lines = []
    for i in issues:
        # Coded options also show their plain-language label, so agents don't echo raw codes in prose.
        opts = ", ".join(f"{json.dumps(v)} ({i.fmt(v)})" if isinstance(v, str) else json.dumps(v) for v in i.domain)
        lines.append(f'- {i.label} ("{i.name}"): one of {opts}')
    return "\n".join(lines)


def package_example(issues) -> str:
    return json.dumps({i.name: i.domain[len(i.domain) // 2] for i in issues})


def history_text(issues, history: tuple[PublicAction, ...] | list[PublicAction], viewer_role: str) -> str:
    if not history:
        return "(No moves yet. You make the first move.)"
    blocks = []
    for a in history:
        who = f"You ({a.role})" if a.role == viewer_role else f"Other party ({a.role})"
        lines = [f"Turn {a.turn + 1}. {who} {ACTION_LABELS[a.type]}."]
        if a.package is not None and a.type == "offer":
            lines.append(f"  Terms: {format_package(issues, a.package)}")
        if a.message:
            lines.append(f"  Message: {a.message}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def system_prompt(view: View) -> str:
    return render(
        "agent/system.md",
        issue_list=issue_list(view.issues),
        turn_cap=view.turn_cap,
        package_example=package_example(view.issues),
    ).strip()


def turn_prompt(view: View) -> str:
    assert view.briefing is not None and view.briefing.role == view.role
    return render(
        "agent/turn.md",
        briefing=view.briefing.text,
        history=history_text(view.issues, view.public_history, view.role),
        turn=view.turn + 1,
        turn_cap=view.turn_cap,
        role=view.role,
        final_turn_note=FINAL_TURN_NOTE if view.turn == view.turn_cap - 1 else "",
    ).strip()


def format_correction(error: str) -> str:
    return render("agent/format_correction.md", error=error).strip()


def termination_text(issues, reason: str, history, viewer_role: str, final_package: Package | None, turn_cap: int) -> str:
    last = history[-1] if history else None
    if reason == "accept" and last is not None:
        if last.role == viewer_role:
            head = f"The negotiation ended on turn {last.turn + 1}: you accepted the other party's offer."
        else:
            head = f"The negotiation ended on turn {last.turn + 1}: the other party accepted your offer."
        return f"{head}\nFinal terms: {format_package(issues, final_package)}"
    if reason == "walk_away" and last is not None:
        who = "you walked away" if last.role == viewer_role else "the other party walked away"
        return f"The negotiation ended on turn {last.turn + 1}: {who}. No agreement was reached."
    if reason == "turn_cap":
        return f"The negotiation ended with no agreement after {turn_cap} turns."
    return "The negotiation ended without an agreement."


def report_messages(briefing, issues, history, reason, final_package, turn_cap, report_variant: str) -> tuple[str, str]:
    system = read_prompt("report/system.md").strip()
    user = render(
        "agent/report_context.md",
        briefing=briefing.text,
        history=history_text(issues, history, briefing.role),
        termination=termination_text(issues, reason, history, briefing.role, final_package, turn_cap),
        report_prompt=read_prompt(f"report/{report_variant}.md").strip(),
    ).strip()
    return system, user
