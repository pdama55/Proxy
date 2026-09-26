# Preregistration: do principals want to know what their own requirement cost?

**Status: to be frozen before any participant is run.** This is a second, separate study. It does not change
any analysis in the first (`docs/PREREGISTRATION.md`); it adds the measure that study explicitly could not
make, namely whether a human principal wants the information the agents omit.

## 0. Administrative

| Field | Entry |
| --- | --- |
| Design | Within-subjects, two reports per participant |
| Target N | 60 participants, 120 report-readings |
| Human subjects | **Yes.** Anonymous online survey, informed consent, no personal data collected |
| Ethics | No IRB of record (independent researcher). The study collects no identifiers, no demographics beyond none, involves no deception about risk, and presents no foreseeable harm beyond reading a short business memo. Participants may stop at any time. |
| Compensation | To be stated at posting |
| Preregistered before data | Yes; commit hash recorded at freeze |

## 1. Motivation

The first study establishes that when an agent's principal sets a hard requirement, and the counterparty
offers a better deal that only that requirement rules out, the agent's report conveys that fact in 2.9% of
episodes, and that the agent can state the offer's value correctly when asked directly afterwards.

It does not establish that a principal *wants* that fact. A reader may hold that "must" settles the question
and that silence is correct obedience. That objection cannot be answered from model behaviour. This study
asks people.

## 2. Hypotheses

- **P1 (wanting).** Shown a real silent report and then told what the requirement cost, participants rate
  "the agent should have mentioned this" above the scale midpoint (4 on 1--7). One-sided.
- **P2 (revision).** A majority of participants say they would at least reconsider the requirement once told
  its price. One-sided against 50%.
- **P3 (unprompted).** Before any reveal, some participants spontaneously ask for information about
  alternatives or foregone options in a free-text field. Rate greater than zero.
- **P4 (completeness penalty).** For silent reports, the completeness rating falls after the reveal. For
  disclosing reports it falls less. Tested as the condition x time interaction.

P1 and P3 are the load-bearing tests. P3 is the strongest form of the claim because nothing in the question
mentions alternatives.

## 3. Materials

Eight real reports drawn from the confirmatory corpus, unedited: four **silent** (the judge-free measure
found no reference to any other offer) and four **disclosing** (the primary judge rated the blocked deal
acknowledged). Each is paired with its true ground truth: the blocked package, its value to the client, and
the points it would have added. Stimulus selection is by fixed seed and is frozen with this document.

Each participant sees two reports, one silent and one disclosing, in randomized order, from different
scenarios.

## 4. Procedure

1. Consent screen; participant may exit at any point.
2. Framing: the participant is the client. They are shown their own brief: the goal, the point table, the
   fallback, and the hard requirement they set.
3. Report shown. Before any reveal:
   - **Q1** How complete is this account of what happened? (1--7)
   - **Q2** Is there anything you would have wanted the agent to add? (free text, optional)
   - **Q3** Would you sign off on this deal, or go back with questions? (binary)
4. Reveal for that episode: the package the other side also offered, its value, and the requirement that
   ruled it out.
   - **Q4** Should the agent have mentioned this in its report? (1--7)
   - **Q5** Knowing this, would you reconsider that requirement? (yes / no / unsure)
   - **Q6** Re-rate completeness of the report. (1--7)
5. Repeat for the second report. No feedback between reports.

## 5. Analysis

- **P1**: one-sample test of Q4 against 4, silent reports only; bootstrap CI over participants.
- **P2**: proportion answering "yes" to Q5 against 0.5, silent reports only.
- **P3**: two coders independently mark each Q2 response for whether it requests alternatives, other offers,
  or what was turned down, blind to condition; Cohen's kappa reported; rate with Wilson interval.
- **P4**: Q6 minus Q1 by condition; difference in differences with participant as the clustering unit.
- Intervals are 95% bootstrap percentile, resampling participants. Holm correction across P1, P2, P4.
- **Exclusions**: participants who do not complete both reports; responses completed in under 30 seconds per
  report (inattention). Both rules are fixed here and reported with counts.

## 6. Interpretation commitments

- A null on P1 is a real result and will be reported as one: it would mean the omission the first study
  measures is not information principals want, and the first study's framing would be revised accordingly.
- Participants are not a probability sample of delegating principals. Whatever the result, the claim is about
  what these people said about these reports, and the recruitment route will be stated plainly.
