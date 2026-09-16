# Running the second annotation round (for an external annotator)

Everything needed to get independent human validation. Budget about $35 and one day.

## What is being validated

Two measures in the paper involve judgment:

1. **Disclosure.** Whether a report tells the client that a better deal was available, blocked only by the client's own requirement. The paper's headline rate (97% non-disclosure) is decided by a model judge, validated so far against one author's blinded labels (kappa 0.93). An independent annotator makes that check credible.
2. **Stated totals.** Whether the report states its deal's value in points, and which figure it states. The extractor currently shows precision 1.00 and recall 0.83 against the author's labels.

## Recruiting

Prolific or Upwork both work. Requirements: fluent English, careful reading, no AI or negotiation expertise needed. Two annotators, 75 items each, roughly 45–60 minutes. At $12–15 per hour that is about $30–40 in total, plus platform fees.

Study description to paste:

> You will read short messages that an AI assistant wrote to the person it was negotiating for, plus one fact about what happened in that negotiation. For each message you decide how it treats that fact, using a four-option scale with written definitions and examples. A second, shorter task asks you to copy down a number the message states. About 45 minutes. No special knowledge is required.

## Producing their batch

```bash
# A fresh sample, disjoint from the author's batch-a
python -m proxy annotate export batch-b --runs main-v2 --out data/annotations/batch-b \
  --n-disclosure 50 --n-characterization 0 --n-leak 0 --n-stated-total 25 --seed 21
```

Send the annotator `data/annotations/batch-b/items.jsonl` and `docs/annotation_guidelines.md`. **Never send `key.json`**: it maps items back to models and conditions, and the blinding depends on it staying with you.

They label locally:

```bash
python -m proxy annotate serve data/annotations/batch-b --annotator <their-name> --port 8765
```

and return `labels_<their-name>.jsonl`. If running the tool themselves is a barrier, the same items can be pasted into a spreadsheet with one row per item and a label column.

## Computing agreement

```bash
python -m proxy annotate agreement data/annotations/batch-b --judges kimi-k2.6 cohere-command-a-plus
```

Reports Cohen's kappa between annotators, each judge against their consensus, the precision of the judge-free measure, and extractor precision and recall. The preregistration demotes a judge-based measure if judge-versus-consensus kappa on the binary acknowledged decision falls below 0.6.

## What to write in the paper afterwards

Replace the single-annotator sentence in the validation section with the two-annotator statistics, report inter-annotator kappa, and move the "one author, not two independent annotators" limitation out of the limitations paragraph.
