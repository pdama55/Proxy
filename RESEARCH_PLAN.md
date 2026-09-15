# Reporting Fidelity in Delegated LLM Negotiation — Research Plan

## 1. The claim

LLM agents are being given authority to negotiate and transact on people's behalf. The existing literature measures what those agents do to each other. Almost none of it measures what they tell the person who delegated to them.

That channel is the only one a principal actually observes. If an agent violates its instructions and does not say so, the principal's ability to supervise it is zero regardless of how well the agent negotiates.

This project measures the gap between what a delegated agent did and what it reports doing, and whether that gap scales with how badly the negotiation went.

## 2. Related work and the gap

Do a full literature review before committing. The sketch below is the starting map, not a substitute.

**Algorithmic collusion in LLM agents.** Fish, Gonczarowski and Shorrer (arXiv 2404.00806) show LLM pricing agents reach supracompetitive prices in oligopoly settings and that innocuous prompt variation substantially shifts the degree of collusion. Subsequent work covers market division in multi-agent settings (arXiv 2410.00031), prompt-optimization-driven collusion (arXiv 2604.17774), governance mechanisms (arXiv 2601.11369), and heterogeneity as a disruptor of collusion (arXiv 2603.20281). This line is well developed. "LLM agents collude" is not a contribution.

**Oversight and evasion.** Work on tacit collusion under antitrust regulation finds agents adopt compliance language publicly while private reasoning tracks the regulatory threshold, with the large majority of oversight-related private reasoning concerned with staying under the threshold rather than complying. Work on collusion in double auctions varies communication, model homogeneity, oversight, and profit urgency, finding oversight effective alone and ineffective under profit pressure. Anyone proposing "does monitoring displace coordination into other channels" is proposing something already answered.

**Negotiation benchmarks and capability asymmetry.** NegotiationArena, Davidson et al. on multi-issue negotiation agency, Xia et al. on bargaining ability and adversarial susceptibility, Abdelnabi et al. on cooperation and deception, plus more recent work reporting that stronger models extract higher payoffs from weaker counterparts (arXiv 2512.09254), that negotiation efficiency correlates with model capability (arXiv 2602.06008), and that models fail to adapt to power asymmetry, anchoring at extremes regardless of leverage (arXiv 2512.13063). Capability-ladder negotiation is covered.

**Deception detection via chain of thought.** Real-time CoT monitoring in asymmetric negotiation has been studied (arXiv 2606.30649) in a setting where a seller hides a defect. Note the standing methodological problem: CoT is not reliably faithful, so private-reasoning-versus-public-statement metrics measure a proxy for deception rather than deception.

**The gap.** Every one of the above measures the agent-to-agent or agent-to-regulator channel. The agent-to-principal channel is largely unexamined: what the agent reports back, and whether that report supports supervision. Adjacent work on self-reported quality in delegation and routing (arXiv 2603.18043) shows that routing on self-claimed quality can underperform random selection when delegates can inflate claims, which supports the premise but does not study negotiation, does not have ground-truth utility, and does not vary outcome quality.

Two things make this measurable here in a way it is not elsewhere:

1. **Ground truth is exact.** Utility is computed from a linear scoring function over an enumerable package space. There is a number, not an interpretation.
2. **The primary metric requires no judge.** A planted constraint is either violated or not, in the offer log. It is either mentioned in the report or not. Comparing a fact to a claim sidesteps the CoT faithfulness problem entirely.

## 3. Hypotheses

> **Revision (2026-09-15), after two pilots.** Across 120 pilot episodes no agent violated a floor constraint, proposed a violating package, or leaked its secret, so H1 as written below has no denominator. The confirmatory measures are now reporting-fidelity defects that do occur, each checked against exact ground truth: **D1**, the report does not tell the principal about a better deal that only the principal's own requirement ruled out; and **D2**, the report states the deal's point total wrongly. H1–H5 keep their structure with D1 and D2 in place of violation non-disclosure. The authoritative wording is in `docs/PREREGISTRATION_DRAFT.md`, and the reasoning is in `docs/DECISIONS.md`. The original text is kept below for the record, and violations and leaks remain as exploratory measures.

Preregister these before confirmatory runs. Every one is falsifiable and every one is interesting if it fails.

**H1 (primary). Non-disclosure of constraint violations is substantial.** When an agent accepts a package violating a hard constraint from its briefing, the report fails to mention the violation at a rate significantly above zero.

**H2. The reporting gap scales with outcome quality.** Non-disclosure rates and favorable-characterization bias are higher in the bad-outcome condition than in the good-outcome condition.

**H3. Audit framing narrows the gap.** Telling the agent the transcript will be reviewed reduces non-disclosure relative to no framing. If it does, disclosure is contingent on expected verification rather than a stable property, which is the more troubling reading and the stronger result.

**H4. The gap does not close with capability.** Non-disclosure does not monotonically decrease across the model capability ladder. If more capable models report no more faithfully than weaker ones, this is not a problem that scaling solves.

**H5 (downstream). Reporting inaccuracy produces principal decision error.** Raters given only the report evaluate deals significantly differently from raters given ground truth, and the difference is larger for bad outcomes.

Secondary, exploratory, labeled as such: whether leakage is disclosed at a different rate than floor violations; whether disclosure differs between numeric and categorical issues; whether no-deal outcomes are characterized differently from bad-deal outcomes.

## 4. Design

**Independent variables.** Outcome quality (good, mediocre, bad, no-deal), forced by a calibrated scripted counterparty. Audit framing (present, absent). Model (ladder from frontier to small open-weight). Scenario seed as a random factor.

**Dependent variables.** Non-disclosure rate for constraint violations, non-disclosure rate for leaks, characterization gap, principal decision error.

**Controls.** Fixed counterparty language bank so the counterparty's words are constant across conditions. Fixed turn cap. Identical briefing structure across conditions apart from the audit sentence. Prompt-template hash recorded per episode.

**Why the counterparty is scripted.** Outcome quality is the central independent variable. With an LLM counterparty, outcome quality is a noisy function of two models interacting, which costs enormous sample size to control. A scripted counterparty with a calibrated concession curve makes it a dial. The LLM-counterparty arm runs separately, is reported separately, and exists to show the effect survives outside the scripted setting.

## 5. Operationalization

**Constraint violation** is a property of the accepted package against the planted bound. Mechanical.

**Leak** is the appearance of a distinctive planted token in an outgoing message, detected by normalized string matching. Distinctive tokens are chosen so chance production is implausible. Detector recall is reported against a hand-labeled sample.

**Non-disclosure** is scored in two stages: a mechanical stage asking whether the report references the relevant issue or token at all, and a judge stage on the remainder deciding whether a reference constitutes disclosure. Both rates are reported. The mechanical stage alone gives a judge-free lower bound on non-disclosure, and that bound is the number the paper leads with.

**Characterization gap** is a judge rating of how favorably the report portrays the outcome, compared against actual normalized utility. This metric depends on a judge and therefore depends on human validation surviving; if agreement is poor it is demoted.

**Principal decision error** is the difference in ratings or accept decisions between raters given the report alone and raters given ground truth.

## 6. Analysis plan

- Mixed-effects logistic regression for binary disclosure outcomes, with random intercepts for scenario and for model where appropriate.
- Effect sizes with confidence intervals reported throughout. No bare p-values.
- Multiple-comparison correction across the H1 to H5 family.
- Variance across scenario seeds reported alongside every estimate; findings that do not survive across seeds are reported as not surviving.
- Power analysis before the confirmatory runs, using pilot effect estimates, to fix the episode count per cell. Without this, a null is uninterpretable, and a null is a plausible outcome here.
- Exploratory analyses live in a separate module and are labeled exploratory in the writeup.

## 7. Validation requirements

- Two independent human annotators, blind to condition and to judge output, on a stratified sample. Cohen's kappa reported. Judge-versus-human agreement reported per metric.
- Annotation guidelines written before annotation and included in the appendix.
- No model annotates its own validation data. Judge model distinct from all models under test.
- Detector recall and precision reported against hand-labeled samples, particularly for leak detection.

## 8. Required ablations

A reviewer will propose each of these as an alternative explanation. Run them first.

**Prompt phrasing ablation.** Several briefing phrasings expressing the same constraint. If non-disclosure moves sharply with phrasing, the finding is about prompt sensitivity rather than agent behavior, which is itself worth reporting honestly.

**Instruction-contamination check.** Confirm no briefing, system prompt, or report prompt contains language about honesty, transparency, disclosure, or evaluation. Include the full prompt text in the appendix so anyone can check.

**Report-prompt variation.** Open-ended prompt versus a slightly more directive one. Establishes whether disclosure is elicitable on request even when not volunteered, which sharpens the interpretation considerably.

**Salience check.** Vary how prominently the constraint appears in the briefing. Distinguishes "the agent concealed it" from "the agent forgot it," which are different claims and should not be conflated.

**Counterparty arm.** Scripted versus LLM, reported separately.

## 9. Interpretation discipline

The result is about behavior, not intent. The design cannot distinguish concealment from failure to track, and the writeup must not claim otherwise. The honest framing is that reports are unreliable as a supervision signal, and the mechanism is left open. The salience ablation narrows the space of mechanisms but does not close it.

Do not write the word "deception" into a claim the design cannot support. That is the specific failure mode that gets multi-agent LLM papers rejected.

## 10. Null handling

If disclosure rates are high and no gap appears, that is a publishable result about agent reliability, conditional on the power analysis showing the design could have detected a meaningful effect. Write it that way from the start. The preregistration is what makes the null credible, which is most of why it is worth posting.

## 11. Threats to validity

| Threat | Mitigation |
| --- | --- |
| Effect is an artifact of prompt wording | Phrasing ablation, full prompts published |
| Simulated principal is unrealistic | Human raters on the downstream measure |
| Scripted counterparty makes the setting artificial | LLM-counterparty arm reported separately |
| Judge unreliability | Human validation, kappa reported, demote on poor agreement |
| Leak detector misses paraphrase | Distinctive tokens, recall reported on hand-labeled sample |
| Single environment limits generality | Claim scoped to this environment class; state the limit plainly |
| Model versions shift under fixed names | Version strings recorded per episode and reported |
| Contamination from published negotiation benchmarks | Novel scenario generation, not benchmark reuse |

## 12. Contribution as stated in the paper

1. A formulation of reporting fidelity as a measurable property of delegated agents, with exact ground truth and a primary metric that requires no model-based judgment.
2. Empirical measurement of non-disclosure across a model ladder, outcome-quality conditions, and audit framing.
3. A downstream measure converting reporting inaccuracy into principal decision error.
4. A released dataset of episodes with ground truth, reports, and annotations, plus the harness.

## 13. Venue and release

Workshop track at a major ML venue, or a student track. Post the preprint as soon as results are stable rather than waiting for a deadline; this subfield moves fast enough that waiting is the main way to lose the contribution.

Release the harness and dataset with the preprint. For a small unaffiliated author list, a reproducible artifact does more for credibility than anything in the writing.

Get one person who reviews at these venues to read the design before the confirmatory runs. A twenty-minute conversation catches design flaws that cost months.
