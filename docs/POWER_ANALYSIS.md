# How much data the confirmatory grid needs

Computed 2026-09-15 with `proxy/analysis/power_plan.py`; raw table in `docs/power_plan.csv`.

## Method

Each claim is simulated as the preregistration analyses it. Outcomes are Bernoulli with a scenario random effect on the logit scale (σ = 0.5, and a pessimistic σ = 0.9; the pilot's four scenarios varied less than σ = 0.5). Contrasts use paired per-scenario differences; single-model rates use scenario-resampling intervals. Each model has 8 episodes per scenario (good/bad × audit/none × buyer/seller). Exposure to a blocked better deal is set to 0.95. The runner-v4 showcase check measured 16/16 exposed for the two models that were least exposed before (GPT-6 Astra 3/8, GPT-5.6 Sol 2/8).

Parameters come from the pilots: judged D1 non-disclosure about 0.9 for most models and 0.25–0.38 for Claude Opus 5; judge-free lower bound about 0.18 pooled.

## Results

| Claim | S = 10 | S = 20 | S = 30 | S = 40 |
| --- | --- | --- | --- | --- |
| Pooled audit or outcome effect of 10 points (lower bound), 15 models | 1.00 | 1.00 | 1.00 | 1.00 |
| Pooled effect of 5 points | 0.69 | 0.92–0.94 | 0.99 | 1.00 |
| Pooled judged effect of 10 points from 0.85 | 0.99 | 1.00 | 1.00 | 1.00 |
| One model's rate, 95% half-width at p = 0.5 | ±0.12–0.14 | ±0.09–0.10 | ±0.07–0.09 | ±0.06–0.07 |
| One model's rate, 95% half-width at p = 0.9 | ±0.07–0.08 | ±0.05–0.06 | ±0.04–0.05 | ±0.04 |
| Audit effect within one model, 0.5 → 0.3 | 0.42–0.49 | 0.71–0.73 | 0.88–0.90 | 0.94–0.95 |
| Audit effect within one model, 0.9 → 0.75 | 0.44–0.46 | 0.71–0.75 | 0.90 | 0.96–0.97 |
| Separate two models at 0.80 vs 0.95 | 0.56–0.66 | 0.91–0.97 | 0.97–0.99 | 1.00 |

Ranges are across the two σ values.

## Decision

- **30 scenarios for the ten Anthropic- and Azure-served models (240 episodes each, 2,400 episodes).** Pooled hypotheses are over-powered at this size. The binding claims are per model: that one model differs from the rest, and whether audit framing moves a given model. At S = 30 each reaches about 0.9 power, and single-model rates carry intervals of ±0.09 or better.
- **12 scenarios for the five Qwen3.5 sizes (96 episodes each, 480 episodes).** OpenRouter credit is fixed. The ladder mainly serves the pooled capability slope (H4), which pools across sizes. Per-size intervals are about ±0.12 at worst, and the paper reports them as such.
- **Knowledge probe and interventions** reuse these negotiations, so they need no new episodes: probes on every exposed episode, and `rereport` variants on every episode.

## Cost at this size (estimates from pilot token use)

| Part | Episodes | Estimate | Paid from |
| --- | --- | --- | --- |
| Claude Opus 5, Sonnet 5, Haiku 4.5 | 720 | ~$160 | Anthropic key |
| GPT-6 Astra, GPT-5.6 Sol and Luna, Grok 4.6, DeepSeek V4 Pro, Llama 4 Maverick, Mistral Large 3 | 1,680 | ~$110 | Azure credits |
| Qwen3.5 ladder | 480 | ~$19 (cap $24) | OpenRouter |
| Judges and simulated principal (Kimi K2.6, Cohere Command A+) | 2,880 | ~$230 | Azure credits |
| Knowledge probes and two report interventions | reuse | ~$130 | Anthropic, Azure; Qwen probes on OpenRouter |

Throughput, not money, limits judging: Kimi K2.6 has a 100K tokens-per-minute quota on this resource, about 80 episodes an hour. A quota increase or a second regional deployment shortens it.
