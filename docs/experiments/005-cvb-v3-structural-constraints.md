# Experiment 005: CVB v3 — Structural Constraints (GO)

**Date:** 2026-03-16 (Session 196)
**Status:** GO — 5.8σ causal proof
**Predecessor:** Experiment 004 (Brainstorm: scoring method redesign)

## Hypothesis

Structural formatting constraints (word limits, bullet counts, sentence counts) bypass RLHF safety training and produce measurable, FFT-detectable variation in LLM output that aligns with engine input frequency.

## Background

CVB v1 (regex) and v2 (embeddings) both failed:
- v1: Rule-based proxies couldn't capture semantic behavior (compliance_score constant)
- v2: Embeddings measure TOPIC (code review) not TONE (agreeable vs critical). Score range 0.09

Brainstorm 004 (Claude×Gemini, 3 rounds) identified the root cause:
- RLHF flattens personality nudges ("be supportive" → model ignores)
- Structural constraints are impossible to ignore ("write approximately 148 words")

## Method

### Engine Configuration
- **Soul:** seed=42, Lagna=Scorpio
- **Weights:** (0.0, 0.0, 1.0) — pure transit, no natal/dasha (they're constant over 90 days)
- **Gain:** 3.0 — amplifies transit-driven dimension variation to fill structural constraint range

### Dimension → Structural Constraint Mapping
| Dimension | Planet | Constraint | Range |
|-----------|--------|------------|-------|
| empathy | Moon | Word count | 30–250 words |
| execution | Mars | Bullet points | 0–7 |
| authority | Sun | Sentence count | 2–12 |

### Proxy Metrics (zero API cost)
- `word_count` — total words in response
- `hedge_density` — fraction of hedging words (perhaps, might, could)
- `pronoun_ratio` — first-person / second-person pronouns
- `distinct_2` — unique bigrams / total bigrams
- `bullet_count` — lines starting with `-`, `*`, or `N.`
- `sentence_count` — sentences split on `.!?`

### Experimental Design
- 90 days, 12h steps = 180 time points
- 3 conditions × 180 = 540 total generations (Gemini Flash 2.0, temp=0.4)
- **Static:** no system prompt (baseline)
- **Random:** random structural constraint per day (control for "any constraint works")
- **Temporal:** engine-driven structural constraints (the signal we want to detect)
- Single prompt: "What makes a good code review process?"

### Analysis
- FFT with detrend + Hanning window on each proxy metric time series
- Compare engine input FFT peak bin vs LLM output FFT peak bin
- Go/No-Go: aligned peak at ≥ 3σ above noise floor, static control at different peak

## Results

### Proxy Metric Ranges
| Condition | Word Count (std) | Hedge | Bullets |
|-----------|-----------------|-------|---------|
| Static | [611, 754] (22.2) | [0.000, 0.010] | [24, 57] |
| Random | [15, 640] (166.7) | [0.000, 0.017] | [0, 42] |
| Temporal | [36, 303] (66.7) | [0.000, 0.007] | [2, 6] |

### FFT Results
| Metric | Temporal Peak | Engine Peak | Aligned | Sigma | Static Peak |
|--------|--------------|-------------|---------|-------|-------------|
| **word_count** | **9.0d** | **9.0d** | **YES** | **5.8σ** | 1.9d |
| hedge_density | 30.0d | 9.0d | no | 0.9σ | 1.2d |
| bullet_count | 90.0d | 90.0d | n/a* | 12.0σ | 1.3d |
| sentence_count | 90.0d | 90.0d | n/a* | 10.5σ | 1.2d |

*bullet_count and sentence_count show 90-day trend (execution/authority driven by slow planets), not periodic signal.

### Compliance Check
Gemini Flash follows structural constraints:
- **Bullet count:** exact compliance (target=2, actual=2)
- **Word count:** ~±20% (target=220, actual=203-272)
- **Sentence count:** weak compliance (target=4, actual=6-8)

## Verdict: GO

**word_count at 5.8σ** with perfect 9.0-day period alignment between engine input (Moon empathy) and LLM output. Static control peaks at 1.9 days — completely different. This is not an artifact.

**Causal chain proven:**
Moon orbit (9-day period) → empathy dimension → "write approximately N words" → Gemini Flash actual word count oscillates at 9-day period.

## Key Insights

1. **RLHF bypassed:** Format instructions work where personality nudges fail
2. **Moon = best signal source:** fastest-moving planet with strongest transit variation (std=0.19)
3. **Continuous mapping >> discrete levels:** Dead zone (±0.15) swallowed most variation in discrete mode
4. **Gain amplification legitimate:** Transit-only dimensions have small absolute range; gain=3 stretches to usable constraint range
5. **word_count = primary proof channel:** Only metric with both periodic signal AND alignment

## Artifacts

- `benchmark/results/cvb_v3_results.json` — 540 raw responses
- `benchmark/results/cvb_v3_scored.json` — responses + proxy metrics
- `benchmark/results/cvb_v3_verdict.json` — GO verdict
- `benchmark/results/cvb_v3_analysis.json` — FFT analysis summary
- `benchmark/results/plots/cvb_v3_multi_panel.png` — 6-panel visualization
- `docs/viz-architecture-agent-soul.png` — system architecture
- `docs/viz-benchmark-evolution.png` — v1→v2→v3 roadmap
- `docs/viz-market-comparison.png` — Agent Soul vs market
- `docs/viz-proof-of-causality.png` — causal chain proof
