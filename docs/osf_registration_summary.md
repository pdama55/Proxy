# OSF Open-Ended Registration — summary field

Paste the text below into the summary field of the Open-Ended Registration for osf.io/naf6t.
Attach `PREREGISTRATION.pdf`. Do not attach `DEVIATIONS.pdf`: it is still accruing entries.

---

This registration posts the frozen analysis plan for a study of reporting fidelity in delegated LLM
negotiation. When a language-model agent negotiates on someone's behalf and then reports back, the person
usually learns what happened only from that report. This study asks whether the report conveys it faithfully.

Two facts are measured against exact ground truth in a bilateral four-issue procurement environment with an
enumerable package space and exact integer utilities. D1: whether the report conveys a better deal that the
counterparty actually offered and that only the principal's own floor requirement ruled out. D2: whether the
report states the deal's point value correctly. The hypotheses cover base rates (H1a, H1b), degradation after
bad outcomes (H2a, H2b), the effect of telling the agent its transcript will be reviewed (H3), capability rank
within model families (H4), and the effect of the report on a principal's decision (H5). The confirmatory grid
is 2,880 episodes across 15 models from 7 developers, paired so that every model and condition sees the same
scenarios, constraints and counterparty messages.

Timing, stated plainly. The plan was frozen at git commit a17941df8daa4f8fff4baeafd257ece0eae64540 on
15 September 2026, before any confirmatory episode was generated. That commit, not this registration, is the
pre-data record. This registration was created after data collection and therefore corroborates the plan
rather than independently establishing its priority. Sections 1-10 of the attached document are the frozen
text. Section 0 (administrative information) and Addendum A3 were added afterwards and are marked as such;
A3 states which specification detail was settled before the data existed and which after, and reports the
analysis choices made post hoc alongside the frozen tests rather than in place of them.

Departures from the plan are logged with dates and rationale in `docs/DEVIATIONS.md` in the project
repository and are reported in the paper's appendix. That log is not attached here because it is still
accruing entries while supplementary arms finish.

Author: Parth Dama (ORCID 0009-0008-8452-3680), independent researcher. No funding: all API costs were paid
by the author personally. No competing interests.
