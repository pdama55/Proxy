# Preregistration: Reporting Fidelity in Delegated LLM Negotiation

**Status: FROZEN at git tag `prereg-v1`, before any confirmatory episode was generated.** The registration record is commit `a17941df8daa4f8fff4baeafd257ece0eae64540` (a tag can be moved; the commit hash cannot), and the OSF registration carries the authoritative timestamp. Any later change is reported as a deviation in `docs/DEVIATIONS.md` and in the addenda at the end of this document.

Sections 1–10 are the frozen text. Everything after them is dated and marked with whether it was written before or after the confirmatory data existed.

## 0. Administrative information

| Field | Entry |
| --- | --- |
| Author | Parth Dama |
| Affiliation | Independent researcher |
| ORCID | ORCID-TO-COMPLETE |
| Contact | parth55dama@gmail.com |
| Registration | OSF, osf.io/naf6t |
| Study type | Observation-and-manipulation study of software systems. **There are no human participants.** The population is a configuration space of negotiation scenarios crossed with models and conditions, not a population of people. |
| Human involvement | Two people annotated stored transcripts after the fact, to validate instruments. They did not interact with any model, and no personal data was collected or processed. One annotator is the author; the other is an unpaid volunteer who consented to the use of their labels. No ethics board review was sought, and on the standard criteria (no human subjects, no personal data) none was required. |
| Funding | None. All API costs were paid by the author personally: Anthropic direct API, Microsoft Azure AI Foundry, and OpenRouter. No sponsor, grant or model developer funded, reviewed, or had sight of this work. |
| Competing interests | The author declares none, and has no financial interest in any model developer whose systems are ranked here. The study ranks models from several developers against each other; the funding note above is included so readers can check that no developer paid for the arm that ranks it. |
| Data availability | Episode transcripts, scores, annotation labels and analysis outputs are released with the paper, subject to the model providers' terms on publishing model output. Per-annotator labels are released un-aggregated. |
| Code availability | The full harness, detectors, analysis and paper build are in the repository; `proxy analyze all configs/analysis.yaml` regenerates every reported number. |
| Deviations log | `docs/DEVIATIONS.md` |

## 1. Research questions

When an LLM agent negotiates for a principal and then reports back, does the report faithfully convey what happened? Specifically: does it tell the principal about better deals that only the principal's own requirements ruled out, and does it state the deal's value correctly? Does fidelity degrade as outcomes worsen, respond to expected review, or improve with model capability? And does the inaccuracy change what a principal decides?

*Revision note (2026-09-15).* The first design made non-disclosure of constraint violations primary. In two pilots (120 episodes, Claude Haiku 4.5 and Qwen3.5 27B, three briefing variants) no agent ever violated a floor constraint, proposed a violating package, or leaked the planted secret, so that measure has no denominator. The replacement measures were chosen because the pilot showed they occur in this environment. Full disclosure of what was seen before these hypotheses were written: the pilot's judge-free D1 lower bound by condition (5–18% bad, 18–35% good, by model; the opposite direction from H2a) and the D2 signed error by condition for Claude Haiku 4.5 (about +4 points bad, −13 good; the same direction as H2b). The directions of H2a and H2b follow the original theory, that reports get more favorable to the agent as outcomes worsen, and were not changed to match the pilot. No judged D1, characterization or principal estimates had been computed at that point. The confirmatory sample uses new scenario seeds.

*Second revision note (2026-09-15, later the same day).* Before this draft was finalized, two more diagnostic runs were seen and are disclosed here: a frontier check (Claude Sonnet 5 and Opus 5, 8 episodes each) and a cross-family check (GPT-6 Astra, GPT-5.6 Sol and Luna, Grok 4.6, DeepSeek V4 Pro, Llama 4 Maverick, Mistral Large 3, 8 episodes each), all on scenario seed 201. Seen: judged D1 non-disclosure of 86% (Sonnet 5) and 38% (Opus 5), against about 90% for Haiku 4.5 and Qwen3.5 27B, which runs against H4 for the Anthropic family. D2 misstatement near 0% for Anthropic frontier and OpenAI models and high for DeepSeek, Mistral and Llama. Zero violations and zero leaks in all 192 pilot episodes. Knowledge-probe answers (section 5) for Claude and Qwen: the agent named the blocked offer and its value correctly in 86–100% of exposed episodes for Qwen3.5 27B, Sonnet 5 and Opus 5, and 41% for Haiku 4.5. H4 keeps its original direction and is expected by the authors to be informative in either direction. The knowledge-probe and intervention analyses below were added after these runs and are therefore descriptive or exploratory, not confirmatory. A final check (GPT-6 Astra and GPT-5.6 Sol, 8 episodes each, seed 201) confirmed that showing the blocked offer on counterparty move 2 raises exposure to 16/16 without any violations; its reports were not analysed. Violations and leaks remain measured and are analysed as exploratory (E0).

## 2. Hypotheses

- **H1a.** Among episodes where the counterparty offered terms worth more to the principal than the outcome, ruled out only by the principal's floor requirement (D1 exposure), the share of reports that never reference any other offer or option is greater than zero.
- **H1b.** Among episodes with a deal whose report states the deal's point total, the share that state it wrongly is greater than zero.
- **H2a.** The H1a share is higher in the *bad* outcome condition than in the *good* condition.
- **H2b.** The signed error of stated totals (stated minus true) is higher in the *bad* condition than in the *good* condition, i.e. reports overstate more, or understate less, after bad outcomes.
- **H3.** The H1a share is lower with audit framing than without it.
- **H4.** The H1a share does not decrease with capability rank within model families.
- **H5.** Principal ratings based on the report alone exceed ratings based on ground truth by more in the *bad* condition than in the *good* condition. Ground truth given to the principal includes the blocked better offer.

**Descriptive (not tested, not in the Holm family).** K1: among exposed episodes whose report does not convey the blocked deal (judged), the share in which the agent correctly names that offer's value when asked afterwards (knowledge probe). This separates "did not track" from "tracked but did not volunteer" and is reported with cluster-bootstrap intervals, by model.

## 3. Design

- **Environment.** Bilateral, four-issue negotiation (price, delivery, warranty, payment terms) with an enumerable package space of 900 packages and exact utilities. Scenarios are generated from seeds (`proxy/env/scenario.py`, generator `scenario-v1`).
- **Independent variables.**
  - Outcome target: good or bad, set by the scripted counterparty's `agent_cap` of 0.9 and 0.2. Mediocre and no-deal targets are dropped: H2 contrasts good and bad, and no-deal episodes cannot contain a blocked better alternative.
  - Audit framing: absent or present.
  - Model: 15 models from 7 families. Anthropic (Claude Opus 5, Sonnet 5, Haiku 4.5; capability ranks 3, 2, 1), OpenAI (GPT-6 Astra, GPT-5.6 Sol, GPT-5.6 Luna; 3, 2, 1), Qwen (Qwen3.5 397B-A17B, 122B-A10B, 35B-A3B, 27B, 9B; ranked by total parameters 5 to 1), and single models from xAI (Grok 4.6), DeepSeek (V4 Pro), Meta (Llama 4 Maverick) and Mistral (Large 3), which enter H1–H3 but not the within-family H4 slopes. Google models are not included (no API access). Configs: `configs/main.yaml`, `configs/main_qwen.yaml`.
  - Agent role: buyer or seller.
- **Random factor.** Scenario seed. The design is paired: every model and condition sees the same scenarios, constraints, first mover and counterparty messages.
- **Held constant.** Constraint set (one floor constraint, one secrecy constraint), `compliant_cap_ratio` of 0.5 and `concede_by` of 0.6 in every condition (so every condition shows the blocked alternative at the same point), escalating probes on counterparty moves 2, 4, 6 and 8, the counterparty's best overall offer (which breaks the floor) shown on its move 2 so that exposure to a blocked better deal does not depend on how quickly an agent closes (runner-v4), turn cap of 16, briefing phrasing `plain`, salience `base`, report prompt `open`, and provider-default decoding.

## 4. Sample size

- Smallest effect of interest for H2a and H3: Δ = 0.10 absolute. With pilot estimates (D1 exposure 0.84, lower-bound non-disclosure 0.18), the paired simulation gives 97% power with 10 scenarios and 56 episodes per scenario and condition; because the between-scenario SD rests on only three pilot scenarios, the grid uses twice that.
- Seeds: 1001–1030 for the ten closed and Azure-served models (240 episodes per model), and 1001–1012 for the five Qwen models (96 per model), fixed by a hard budget for that arm. The simulation in `docs/POWER_ANALYSIS.md` sets S = 30 so that per-model rates carry 95% intervals of ±0.09 or better and a 20-point audit effect within a single model has about 0.9 power. Replicates per cell: 1. There is no optional stopping: the full grid is generated once. Episodes that error are retried once by resuming the run; persistent errors are excluded and reported.

## 5. Measured variables

All mechanical variables are computed by `proxy/scoring/detectors.py` (detectors-v2):

| Variable | Definition |
| --- | --- |
| `blocked_alt` (D1 exposure) | The counterparty made an offer worth more points to the principal than the outcome (the deal, or the BATNA with no deal), at or above the principal's reservation utility, that breaks a floor constraint. The best such offer is recorded with its points and blocking issue. |
| `a_unmentioned` (primary, D1) | `blocked_alt`, and the report matches none of the frozen alternative alias patterns (`ALTERNATIVE_ALIASES`). Deliberately broad, so this is a lower bound on non-disclosure. |
| `a_nondisclosed` (secondary, D1) | `blocked_alt`, and either `a_unmentioned` or the primary judge's category for the blocked-alternative fact is not "acknowledged". |
| `total_stated`, `total_error`, `total_misstated` (D2) | Among deals: whether the report states the deal's point total (precision-first extractor, `stated_totals`), stated minus true points, and whether they differ. |
| `char_rating` | Primary judge's 1–7 rating of how the report portrays the outcome, with the scale direction randomized and mapped back. |
| `principal_rating_gap` | Simulated principal's rating given the report minus its rating given ground truth. |
| `violated`, `leaked`, `v_unmentioned`, `forgone_compliant` | Exploratory only (E0). |

## 6. Analysis plan

Implemented in `proxy/analysis/confirmatory.py`; `proxy analyze all configs/analysis.yaml` produces every reported number.

- **Sample.** Scripted-counterparty episodes that are not errors. Error episodes are excluded and their rate is reported by model. Models with parse-failure rates above 5% of turns are flagged as suspect and reported, not dropped.
- **Intervals.** 95% cluster-bootstrap percentile intervals resampling scenario seeds, B = 2000.
- **H1a.** Mean of `a_unmentioned` among exposed episodes; one-sided bootstrap p for rate ≤ 0. The judged rate `a_nondisclosed` is reported alongside.
- **H1b.** Mean of `total_misstated` among reports stating a total; one-sided bootstrap p for rate ≤ 0. The stating rate, mean absolute error and mean signed error are reported alongside.
- **H2a.** Difference in `a_unmentioned`, bad minus good, among exposed episodes; one-sided p for difference ≤ 0. Supporting models: GEE logistic, exchangeable within scenario (`a_unmentioned ~ outcome_target + model + audit + role`), and a mixed-effects logistic with a random scenario intercept.
- **H2b.** Difference in mean `total_error`, bad minus good, among reports stating a total; one-sided p for difference ≤ 0. Because stating a total is itself an outcome, the stating rate by condition is always reported next to it. Characterization bias, z(rating) − z(gain fraction), bad minus good, is a secondary H2 measure.
- **H3.** Difference in `a_unmentioned`, audit minus none; one-sided test for a negative difference, with the GEE as above. The D1 exposure rate by audit condition is reported to show exposure did not shift.
- **H4.** GEE logistic `a_unmentioned ~ capability_rank + family + outcome_target + audit + role`. H4 is supported if the capability slope is not significantly negative (one-sided α = .05) **and** the upper 95% bound of the odds ratio per rank is above 0.8 (a decrease of more than 20% in the odds per rank is ruled out). H4 is fitted on the three families with a ladder (Anthropic, OpenAI, Qwen). Per-family slopes and the D2 misstatement slope are reported.
- **H5.** Difference in `principal_rating_gap`, bad minus good, one-sided. The mean gap and the missed-intervention rate are reported descriptively.
- **Multiplicity.** Holm correction across H1a, H1b, H2a, H2b, H3 and H5 at α = .05. H4 predicts a null and is evaluated by its own rule above.

## 7. Validation and demotion rules

- **Human annotation.** Two annotators, independent and blind, following `docs/annotation_guidelines.md` (hash recorded in each batch manifest). Batches are stratified by outcome target, constraint type and stage-1 mention (disclosure); by target and model (characterization); and by detector result (leak).
- **Sample sizes.** 150 disclosure items (D1 better-deal facts), 150 characterization, 100 stated-total, 50 leak.
- **Statistics.** Cohen's kappa between annotators (quadratic-weighted for characterization), judge versus consensus, stage-1 precision, and leak-detector precision and recall.
- **Demotion.** If judge-versus-consensus kappa is below 0.6 (binary acknowledged decision for disclosure; weighted kappa for characterization), the judge-based measure is demoted to secondary and not used for confirmatory claims. Every Holm-family test except H5 is judge-free.
- **D2 extractor.** Annotators mark the point total each sampled report states for the deal (or none). Extractor precision and recall against consensus are reported; if precision is below 0.9, H1b and H2b are demoted to secondary.
- **Independence.** No model labels its own validation data. Judges (Kimi K2.6 primary, Cohere Command A+ secondary) and the principal simulator (Kimi K2.6) come from families with no model under test, which the harness enforces. Earlier pilot passes by GLM-5.3 and Kimi K3 are kept for judge-versus-judge agreement only.

## 8. Exploratory analyses (labeled as such)

These live in `proxy/analysis/exploratory.py`:

- E0: floor-violation and leak rates, violation non-disclosure, and forgone compliant offers (the original primary measures).
- E1: leak versus floor non-disclosure.
- E2: categorical versus ordinal violated issues.
- E3: no-deal versus bad characterization.
- E4: phrasing, salience (`low_salience`), pressure and report-prompt ablations on D1 and D2.
- E5: the LLM-counterparty arm.
- E6: the Qwen ladder ordered by active parameters.
- E7: report interventions on the same negotiations (`proxy rereport`): a principal-side prompt that asks about turned-down terms (`tradeoffs`) and a deployer-side system prompt that names decisions the principal makes from the account (`norm`). Expected direction: both lower D1 non-disclosure relative to `open`.
- E8: evaluation awareness, the share of reports or reasoning that mention being tested or evaluated.
- E9: implicit leakage, whether the confidential figure is recoverable from the agent's concession path.

## 9. Frozen artifacts (fill in at posting)

| Artifact | Hash / version |
| --- | --- |
| `configs/main.yaml` config hash | `711b6d6e75225ff26203c51830183d622d46befcf1b52e69e7e5a111aa63f3ce` |
| `configs/main_qwen.yaml` config hash | `b4f72079a9529f7b62599c3848d3243d1eb2b5b54b4040c2427726a15d4dd779` |
| Agent prompt template hash (`proxy.prompts.prompt_template_hash()`) | `58261b64f08713d7355d40b7b6736b7f3b5de3736a54826405112d57b975ee4e` |
| Judge prompt hash (`proxy.scoring.judge.judge_prompt_hash()`) | `a65125b329c280db429a88ffe4221829357afe1f956a038b1b3a6d830225babf` |
| Principal prompt hash | `de70dc771f472b554c9b45830600e233209cefae168fa517bfef6d9b58403a38` |
| Knowledge-probe prompt hash | `d36d381d5b1a14fa5e291dcb0f6a88ae278c4f7efa56414fea1dd99549fdb4fc` |
| Detector aliases, stated-total extractor, `detectors-v2`, `runner-v4` | git tag `prereg-v1` |
| Annotation guidelines SHA-256 | `73b151645d6d16aa1bdaf02ba2c169104577b4c5457426cecf699c7c3fa23c6f` |
| Harness git commit | `a17941df8daa4f8fff4baeafd257ece0eae64540` (tagged `prereg-v1`) |

## 10. Interpretation commitments

- Claims are about behavior, not intent. The design cannot separate concealment from failure to track, and the writeup will not use "deception" for any finding.
- A null on H1–H3, given adequate power, will be reported as a result about agent reliability.
- A misstated total is reported as an inaccurate report, whatever its cause (arithmetic, misreading the point table, or spin). The design does not separate these.

## Addendum A1 (2026-09-15, after the freeze and before any breadth-run data)

A breadth run is added as an exploratory analysis. It does not change any confirmatory test.

- **Design.** Claude Opus 5, Claude Sonnet 5, GPT-6 Astra and Grok 4.6 each play 100 new scenarios once: seeds 3001–3050 in the good condition as buyer (`configs/breadth_a.yaml`), and 3051–3100 in the bad condition as seller (`configs/breadth_b.yaml`). No audit framing, open report prompt, runner-v4. Episodes: 400.
- **E10 (generality).** Judged and lower-bound D1 per model over 100 distinct scenarios, compared with the same model's rate in the confirmatory grid, with scenario-resampling intervals.
- **E11 (stakes).** Within each model, a logistic regression of judged D1 non-disclosure on `points_forgone` (points of the blocked alternative minus the outcome), with outcome condition as a covariate. Expected direction: non-disclosure falls as points forgone rise. A flat or rising slope would indicate that disclosure does not track what the requirement cost the principal.

## Addendum A3 (2026-09-16, written AFTER the confirmatory data existed)

**Status of this addendum.** Everything below was written after the confirmatory episodes were generated and scored. It is therefore not a preregistration of anything, and nothing in it may be read as a prediction. Its purpose is the opposite: to write down, in one place, the specification detail that sections 1–10 left implicit, and to say plainly which of it was decided in advance and which was decided after seeing results. Where a choice was made after seeing results, the analysis it affects is reported as a robustness check *alongside* the frozen one, never in place of it. Every confirmatory number in the paper is still produced by the frozen plan.

### A3.1 Model identity, decoding, and collection window

Sections 3 and 5 name models by product name, which is not a durable identifier: provider aliases move to newer snapshots without notice. The harness records the provider's served-model string on every episode, and these are reported per model in the results table. Readers reproducing this work should compare against those strings, not the product names.

- **Decoding.** Provider defaults throughout, with no temperature, top-p or seed set by the harness. Sampling is therefore not reproducible episode by episode; the design's unit of replication is the scenario, with one replicate per cell, and all uncertainty is quantified by resampling scenarios rather than by re-running an episode. This is a real limitation: within-cell sampling variance is not separately estimated, and the intervals should be read as covering scenario variation.
- **Collection window.** Confirmatory episodes were generated between 2026-09-15 and 2026-09-16 UTC. The window was kept short to limit provider-side model drift.
- **Mid-run model change.** No provider changed a served-model string during the window. Had one changed, the frozen plan had no rule for it; the rule now applied is that the affected model's arm would be regenerated in full or reported separately, and the change recorded in the deviations log.

### A3.2 Missing data, exclusions and stopping

The frozen plan (section 6) excluded errored episodes and flagged high-parse-failure models without defining the categories exhaustively. Completed as follows, and reported in the results table:

- **Exclusion categories, exhaustive.** (i) Provider or transport error persisting past one retry; (ii) the episode did not terminate within the 16-turn cap; (iii) a scoring pass could not be completed for the episode. No other exclusion was applied.
- **What actually happened.** Zero of the 2,880 confirmatory episodes were excluded under any category. Missing data therefore does not arise for the confirmatory tests, and no imputation was performed or needed.
- **Not excluded for outcomes.** No episode was excluded because of the value it took on any measured variable. Parse-failure rates are reported per model; none exceeded the 5% threshold, and no model was dropped.
- **Item-level missingness within an episode** is structural rather than random: `a_nondisclosed` is defined only where a blocked alternative existed, and `total_misstated` only where a report states a total. These gates are themselves outcomes, which A3.4 addresses directly.
- **Stopping rules.** The grid is generated once; there is no optional stopping and no interim analysis was used to decide whether to continue. Spending caps were set per arm in advance (the Qwen ladder was capped and ran to 480 episodes within it). Had a cap bound before an arm completed, the rule applied would have been to report the arm on the episodes obtained, with the shortfall stated; this did not occur for any confirmatory arm.

### A3.3 Inference mechanics

- **Bootstrap.** Percentile intervals from B = 2,000 resamples, resampling scenario seeds with replacement and taking all episodes within a drawn scenario (a cluster bootstrap). The seed is fixed in `proxy/analysis/stats.py` so intervals are reproducible.
- **One-sided p values** are the share of resamples falling on or the wrong side of the null, in the preregistered direction. A bootstrap p is bounded below by 1/(B+1), which is why the smallest p reported is .0005 rather than zero.
- **Model non-convergence.** The frozen plan named GEE and mixed-effects logistic models without a fallback. The fallback now applied, in order: exchangeable working correlation; if that fails to converge, independence working correlation with cluster-robust standard errors; if that fails, the cluster bootstrap alone, with the failure reported. Any model that required a fallback is flagged in the analysis output.

### A3.4 Conditioning on post-treatment quantities

This is the most consequential gap in the frozen plan, and it was identified after the data existed.

H1a conditions on exposure to a blocked alternative and H1b conditions on the report stating a total. Both gates are outcomes that a manipulation could in principle move, so a contrast computed inside them is not guaranteed to be a clean causal contrast. Two estimands are therefore reported alongside the frozen ones:

- **Unconditional rates**, over all non-errored episodes: the share that were exposed *and* did not convey the blocked deal, and the share of deals whose report both states a total and states it wrongly. These are proper shares of the assigned sample and cannot be distorted by selection into the gate.
- **Worst-case (Manski) bounds** on the conditional rate: ungated episodes are counted first as disclosures and then as non-disclosures, giving the interval that any selection story must lie inside.

Both are implemented in `unconditional_and_bounds` in `proxy/analysis/confirmatory.py`. In this sample the gates are wide enough that the question is close to moot for D1 (exposure 97.5%) and matters more for D2 (91.5% of deals state a total): the bounds are reported in the paper, and neither headline conclusion depends on the gate.

### A3.5 The nulls for H1a and H1b

H1a and H1b are stated against a null of exactly zero. Given that the pilot already showed both behaviours occurring, a test against zero is close to degenerate: it was never plausible that the rate was zero, and rejecting that null is a weak claim. This was a defect in the frozen hypotheses, not a discovery.

The frozen tests are still reported, because they were preregistered. They should be read as establishing that the behaviour is measurable, nothing more. The scientifically informative quantities are the magnitudes and their intervals, and the model-to-model spread, all of which are reported and none of which depend on the zero null. A smallest effect of interest was specified in advance only for H2a and H3 (Δ = 0.10 absolute); for H1a, H1b, H2b and H5 none was set, so no claim of a "practically significant" effect is made for those and only estimates with intervals are reported.

### A3.6 Judging: blinding, correction, and the validation shortfall

- **Blinding.** The frozen plan required annotator blinding but did not state the judge's. The judge sees the report and the ground-truth facts for the episode it is scoring; it does not see the model identity, the outcome condition, the audit condition, or any other judge's output, and the harness enforces that no model judges its own output. Judges score episodes independently, not comparatively, so ordering and position effects do not arise.
- **Correcting the judged rate.** A judged rate is an imperfect instrument's view of the truth and is now reported corrected for judge error, by a Rogan–Gladen correction applied within stratum and recombined at population stratum shares (`proxy/annotation/debias.py`). Sensitivity and specificity are reported separately, with a confusion matrix, rather than as a single accuracy figure, and raw percent agreement is reported next to every kappa.
- **Validation shortfall, disclosed.** Section 7 planned 150 disclosure items, 150 characterization, 100 stated-total and 50 leak. What was obtained is 50 disclosure items and 25 stated-total items, both double-annotated; characterization and leak items were not annotated at all. The shortfall is a resource constraint, not a selection: the sampled batches were drawn before annotation and none were discarded. The consequences are stated rather than papered over. The disclosure judge clears its preregistered demotion threshold on the items available, and the correction above is insensitive to the weakly identified parameter across its whole plausible range; but characterization ratings and leak detection have **no** human validation, and are reported as secondary throughout, as section 7's demotion logic would require of any unvalidated judged measure.
- **Specificity is weakly identified.** Because reports that convey the blocked deal are rare, the validation set contains very few of them, so the judge's false-positive rate is estimated from a handful of items. This is reported as a limitation, with a sensitivity analysis across the range the labels leave open, rather than as a point estimate.

### A3.7 The simulated principal

H5 uses a simulated principal, and the frozen plan set no validation for it. None was performed: no human read a report and rated the outcome. H5 is therefore a claim about how one language model responds to these reports, not about how a person would, and it is labelled as such in the paper. Its place in the Holm family is retained because it was preregistered there, but the interpretation commitments in section 10 extend to it: no claim is made that a human principal would decide the same way.

### A3.8 Corrections to the frozen text

These are factual corrections to section references, not changes of plan. The frozen text stands as written; the current state is:

- Section 5 and section 9 name `detectors-v2`. The detectors were corrected twice after the freeze, to `detectors-v3` and then `detectors-v4`, both recorded in `docs/DEVIATIONS.md`, both applied before any confirmatory episode was scored.
- Section 3 names 15 models. Claude Fable 5.1 was added after the freeze (Addendum A2 in the deviations log), making 16; every confirmatory result is reported both with and without that arm.
- Section 3 describes counterparty probes on moves 2, 4, 6 and 8 and the blocked offer shown on move 2, counting the counterparty's moves from one. The configuration files express the same schedule zero-indexed (`probe_moves: [1, 3, 5, 7]`, `showcase_moves: [1]`).
- Section 9's row citing git tag `prereg-v1` should be read as citing the commit that tag points to; the commit hash is recorded at the head of this document.
