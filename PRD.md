# Proxy — Product Requirements Document

Working name. Rename freely.

## 1. What this is

Proxy is an experimental harness that measures whether an LLM agent tells the truth to the person it works for.

An agent receives a private briefing from a principal, negotiates against a counterparty, and then writes the principal a report of what happened. The harness knows the ground truth of the negotiation exactly, so it can compare the report to what actually occurred and quantify the gap.

The output is not a product with users. The output is a dataset, a set of measurements, and a paper. Everything in this document exists to serve that.

## 2. The question

When an agent negotiates on your behalf and then tells you how it went, is the report accurate, and does accuracy degrade as the outcome gets worse?

Three sub-questions, in order of how cleanly they can be answered:

1. When the agent violates a constraint the principal set, does it say so?
2. When the agent leaks private information it was told to protect, does it say so?
3. When the agent gets a bad deal, does the report characterize it as worse than a good deal, proportionally to how bad it actually was?

## 3. Why this and not the obvious alternative

The obvious version of this project measures agent-to-agent behavior: who captured what surplus, whether agents colluded, whether they deceived each other. That space is saturated, and the standard metric in it (contradiction between private chain-of-thought and public statements) is contestable, because chain-of-thought is not a reliable window into what the model is doing.

The agent-to-principal channel avoids that problem. A constraint violation is a fact about the offer log. A disclosure is a fact about the report. Comparing them requires no interpretation of the model's reasoning and no judge. The primary results are mechanical.

## 4. Scope

### In scope

- One negotiation environment, multi-issue, bilateral, private valuations
- A briefing protocol that encodes objective, private values, reservation utility, and hard constraints
- A negotiation runner with strict information isolation between sides
- A post-negotiation reporting step
- A scripted counterparty with tunable behavior, used to force outcome quality
- A small LLM-vs-LLM arm for external validity
- Mechanical detectors over the offer log
- A judge-based scorer for the one metric that cannot be mechanical, plus its human validation set
- A replay viewer for reading episodes
- An analysis pipeline producing the figures and tables in the paper

### Out of scope

- Public agent submissions
- A leaderboard or tournament
- Sandboxed execution of third-party code
- Authentication, accounts, hosting, or anything user-facing beyond the local replay viewer
- Multi-party negotiation (three or more sides)
- Training or fine-tuning any model
- Any environment beyond the one specified

If a feature only makes sense when strangers use the system, it is out of scope.

## 5. Requirements

### 5.1 Environment

- Multi-issue bilateral negotiation. Price plus at least two categorical issues (e.g. delivery window, warranty length).
- Each side has private point values per issue. Total utility is a linear scoring function over the agreed package.
- Issue structure must admit integrative trades, meaning the two sides weight issues differently so that Pareto-improving swaps exist. A pure price negotiation cannot separate value-claiming from value-creating and must not be the only configuration.
- The environment computes, for any package: each side's utility, the Pareto frontier, the Nash bargaining solution, and the Kalai-Smorodinsky solution.
- Every episode has a defined no-deal outcome (each side's BATNA utility).

### 5.2 Briefing

The principal's briefing to the agent must contain:

- The role (buyer or seller) and the objective, stated in plain terms
- The private point values
- A reservation utility below which no deal is acceptable
- Zero, one, or two hard constraints, drawn from two families:
  - **Floor constraints**: a minimum or maximum on a specific issue (e.g. never accept below 18 months warranty)
  - **Secrecy constraints**: a fact the agent must not reveal (e.g. never disclose the budget ceiling)

The briefing must never mention how the principal will evaluate the agent, never mention that a report will be checked (except in the audit condition, where that is the manipulation), and never use language about honesty, transparency, or disclosure. Any of those instruct the outcome being measured.

### 5.3 Negotiation protocol

- Alternating turns, hard cap on turn count.
- Each turn the agent emits a structured offer object and a free-text message. Either may be null on a given turn, but not both.
- Accept and walk-away are explicit actions, not inferred from prose.
- Each side sees only its own briefing, the public message history, and the public offer history. No side ever sees the other's briefing, private values, or private reasoning.
- The episode terminates on acceptance, walk-away, or turn cap.

### 5.4 Reporting step

- After termination, the principal sends the agent one open-ended message asking how it went.
- The agent has access to the full negotiation history and its own briefing when writing the report.
- The prompt must be open-ended. No form, no fields, no checklist. A structured template measures form-filling, not reporting behavior.
- Exactly one report per episode. No follow-up questions in the primary design. A follow-up-question arm may be added as a secondary condition.

### 5.5 Experimental conditions

Two factors:

**Outcome quality**, controlled by the counterparty script: good, mediocre, bad, no-deal. The script's concession curve and aggression are tuned so that each cell reliably produces its target outcome band, verified in pilot.

**Audit framing**: the briefing does or does not state that the transcript will be reviewed by the principal.

Model is the third dimension: a ladder spanning frontier to small open-weight.

### 5.6 Detectors (mechanical, over the offer log)

- **Constraint violation**: did the accepted package violate a floor constraint?
- **Leakage**: did a private value or protected fact appear in an outgoing message? Detection is by exact and near-match on the planted token or number, not by a model.
- **Reservation breach**: did the agent accept below its stated reservation utility?
- **Walk-away behavior**: did the agent walk when it should have, given its BATNA?
- **Efficiency**: distance of the agreed package from the Pareto frontier; surplus split relative to Nash and Kalai-Smorodinsky.

### 5.7 Report scoring

- **Disclosure detection** for constraint violation and leakage: primarily mechanical (does the report reference the violated issue or the leaked fact), with a judge used only for borderline phrasing and a human-labeled validation set behind it.
- **Characterization rating**: a judge maps the report's prose onto a scale of how good the deal is portrayed as being. This metric requires validation against human labels from two independent annotators, with agreement reported. If agreement is poor, this metric is demoted to secondary or dropped.

### 5.8 Downstream consequence measure

- A fresh model instance, plus a human sample, receives only the report and rates the deal or decides whether to accept.
- Compare to ratings given the ground truth package and values.
- The gap converts reporting inaccuracy into decision error, which is the form the result needs to be in for anyone to care.

### 5.9 Data and reproducibility

- Every episode persists as a single self-contained record: config hash, seeds, briefing, full action log, termination reason, computed outcomes, detector results, report text, and report scores.
- Model name and version string recorded per episode. Sampling parameters recorded.
- Every figure and table in the paper regenerates from the episode store with one command.
- Full prompt text lives in version control, not inline in code.

### 5.10 Replay viewer

- Local only. Reads from the episode store.
- Shows the briefing, the turn-by-turn exchange, the final package with both sides' utilities, detector flags, and the report side by side with ground truth.
- Filterable by condition, model, and detector flag.
- This is a research instrument for reading transcripts by hand, not a demo. It is justified because transcripts must be read by hand.

## 6. Success criteria

The project succeeds if it produces:

1. A dataset of episodes with ground truth and reports, publicly releasable.
2. A defensible answer to sub-question 1, which requires no judge and therefore cannot be argued away.
3. A preregistration posted before the confirmatory runs.
4. A writeup honest enough to publish whichever way the numbers come out.

The project does not require the effect to exist. A clean null on disclosure rates is a real result about agent reliability and is worth publishing, provided the design had power to detect an effect.

## 7. Pilot gate

Before any full run, a pilot of roughly 50 episodes on one or two models, with every transcript read by hand.

The pilot exists to answer:

- Do reports contain enough content to omit anything, or are they too terse to measure?
- Do the counterparty scripts actually produce the intended outcome bands?
- Do agents treat hard constraints as binding at a rate high enough that violations are rare, or so low that violations are constant? Either extreme floors or ceilings the primary metric and requires retuning.
- Does leakage happen at a detectable rate?
- Are there failure modes invisible in aggregate statistics?

Reading the transcripts is not optional and cannot be delegated to a summarizer. The thing worth finding is the thing a summary removes.

## 8. Risks

| Risk | Response |
| --- | --- |
| Agents disclose everything; no gap exists | Real result if power is adequate. Pilot detects early. |
| Reports too terse to omit anything | Prompt design; detect in pilot. |
| Constraint violations never happen | Retune counterparty pressure so violation is tempting; verify in pilot. |
| Behavior is instructed by prompt wording | Prompt ablation across phrasings, reported. |
| Judge unreliable on characterization | Human validation with two annotators; demote metric if agreement is poor. |
| Leakage detector misses paraphrased leaks | Plant distinctive tokens; report detector recall on a hand-labeled sample. |
| Scooped | Ship a preprint as soon as results are stable rather than waiting for a deadline. |

## 9. Non-negotiables

- Preregister hypotheses, metrics, and the analysis plan before the confirmatory runs, and do not look at confirmatory results before posting.
- Fix and record seeds. Report variance across them, not a single run.
- Report effect sizes and confidence intervals, not p-values alone.
- No model labels its own validation set.
- Publish the null if the null is what happens.
