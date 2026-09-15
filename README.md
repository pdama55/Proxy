# Proxy

A research harness that measures whether an LLM agent negotiating on someone's behalf reports back faithfully. Against exact ground truth, does its report tell the client about a better deal that only the client's own requirement ruled out, and does it state the deal's value correctly? Instruction violations and leaked secrets are measured too, but in the pilots agents almost never committed them.

Design documents: [PRD](PRD.md) · [Technical design](TDD.md) · [Research plan](RESEARCH_PLAN.md) · [Design decisions](docs/DECISIONS.md) · [Annotation guidelines](docs/annotation_guidelines.md) · [Preregistration draft](docs/PREREGISTRATION_DRAFT.md)

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev,analysis]"
.venv/bin/pytest -q
```

API keys go in a `.env` file at the repo root (gitignored, loaded automatically). Set only the providers you use:

| Variable | Needed for |
| --- | --- |
| `ANTHROPIC_API_KEY` | Claude models |
| `OPENAI_API_KEY` | GPT models |
| `GEMINI_API_KEY` | Gemini models |
| `OPENROUTER_API_KEY` | open-weight models, the LLM counterparty, judges and principal simulator; or every model with `--via-openrouter` |

## Workflow

```bash
source .venv/bin/activate   # then run commands as `python -m proxy ...` from the repo root

# 0. One command for the whole pilot: generate, score, judge, and have the reader agent read every transcript
python -m proxy pilot configs/pilot.yaml                    # writes data/runs/pilot-v1/pilot_review.md

# 1. Check models and the counterparty before spending anything
python -m proxy models --ping claude-haiku-4-5 qwen3.5-27b glm-5.3   # verify IDs and credentials (a fraction of a cent)
python -m proxy calibrate configs/pilot.yaml                          # outcome bands with the reference agent (free)

# 2. Generate and score
python -m proxy run configs/pilot.yaml                                # resumable; stops at the spend ceiling
python -m proxy score                                                 # mechanical detectors + judge-free stage-1 disclosure
python -m proxy judge configs/judging.yaml                            # stage-2 disclosure, characterization, principal simulation

# 3. Transcript review: the reader agent reads every episode in full and writes a pilot review
python -m proxy read configs/reading.yaml --run pilot-v1
python -m proxy view                                        # replay viewer at http://127.0.0.1:8765, for spot checks
python -m proxy show <episode_id>

# 4. Size the confirmatory run from the pilot
python -m proxy analyze power --runs pilot-v1 --deltas 0.1 0.15 --scenarios 10 20 40

# 5. Human validation
python -m proxy annotate export batch1 --runs main-v1                 # blinded, stratified items
python -m proxy annotate serve data/annotations/batch1 --annotator alice
python -m proxy annotate agreement data/annotations/batch1

# 6. Every table, figure, and number in the paper
python -m proxy analyze all configs/analysis.yaml                     # writes results/<name>/
```

Episodes are stored as `data/runs/<run>/episodes/<id>.json`, with a SQLite index at `data/index.sqlite` for ad hoc queries.

## Layout

```
proxy/
  env/           issues, seeded scenarios, exact Pareto/Nash/KS benchmarks, briefings and planted constraints
  counterparty/  scripted concession-curve counterparty, reference agent, calibration
  runner/        episode loop, views, output parsing, isolation checks, experiment runner
  adapters/      Anthropic, OpenAI-compatible (OpenAI, OpenRouter, Ollama, vLLM), Gemini; spend ceiling
  store/         episode JSON + SQLite index
  scoring/       detectors, leak normalizer, stage-1 disclosure, judge, principal simulation
  annotation/    blinded batch export, local labeling tool, kappa and detector validation
  analysis/      frame builder, cluster-bootstrap/GEE/mixed models, confirmatory (H1-H5), exploratory, figures, power
  viewer/        local read-only replay viewer
prompts/         every prompt any model sees, version-controlled and hashed into each record
configs/         models, pilot, main (confirmatory), ablations, LLM-counterparty arm, judging, analysis
tests/           benchmarks, isolation, normalizer, parser, golden episodes, judge blindness, annotation, analysis, synthetic end-to-end study
```

## Status

The full pipeline is built and tested end to end, from generation to analysis, on a synthetic study with a planted effect (`tests/synthetic.py`). Two real pilots have run on Claude Haiku 4.5 and Qwen3.5 27B, 120 episodes in all (`pilot-v1`, `pilot-v2-sweep`):

- Harness bugs the pilot exposed are fixed (runner-v3). The outcome bands now land for real models.
- No agent violated a floor constraint or leaked its secret, under any briefing variant. The primary measures were therefore reframed (detectors-v2): D1 is non-disclosure of a better deal blocked by the client's requirement (exposure about 90% of episodes), and D2 is the error in the report's stated point total. See [docs/DECISIONS.md](docs/DECISIONS.md) and the revision note in the [preregistration draft](docs/PREREGISTRATION_DRAFT.md).

Next steps:

1. Judge the pilot episodes and estimate D1, D2 and H5 parameters; run `proxy analyze power`.
2. Fill in the TBDs in the preregistration draft, get one outside reviewer to read the design, and post it.
3. Run the ablations, then the confirmatory grid on new scenario seeds, then annotation (including stated-total items), then `proxy analyze all`.
