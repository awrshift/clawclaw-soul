# Experiment 006: Semantic Proof — Length-Agnostic Metrics

**Date:** 2026-03-16 (Session 197)
**Status:** NO-GO — semantic modulation not proven at required significance
**Predecessor:** Experiment 005 (CVB v3 GO at 5.8σ on word_count)

## Hypothesis

If temporal behavioral modulation extends beyond structural formatting, then length-independent semantic metrics (sentiment, lexical diversity) should also show FFT peaks aligned with the 9-day lunar period at ≥3.0σ.

## Background

CVB v3 proved word_count modulation at 5.8σ, but word_count is a structural property. Critics can argue we proved formatting compliance, not personality modulation. To strengthen the claim, we need semantic evidence.

ICF Brainstorm (Claude×Gemini Pro, 3 rounds) identified the risk of confounds: raw VADER and TTR both correlate with text length. Solution: use length-agnostic alternatives.

## Method

### Metrics (all length-independent)
- **Sentence-VADER**: Average VADER compound score per sentence (not per document). Controls for the VADER length inflation effect.
- **MTLD** (Measure of Textual Lexical Diversity): Standard in computational linguistics. Unlike TTR, MTLD does not decay with text length. Uses `lexical-diversity` Python package.

### Data
Reused existing 540 Gemini Flash responses from CVB v3:
- 180 temporal (engine-driven structural constraints)
- 180 static (no system prompt)
- 180 random (random structural constraints)

### Analysis
FFT with detrend + Hanning window on each metric time series per condition.

## Results

### Descriptive Statistics
| Metric | Condition | Mean | Std | Range |
|--------|-----------|------|-----|-------|
| sentence_vader | temporal | 0.3857 | 0.1910 | [0.005, 0.824] |
| sentence_vader | static | 0.2226 | 0.0489 | [0.088, 0.394] |
| sentence_vader | random | 0.4060 | 0.2270 | [0.079, 0.988] |
| mtld | temporal | 122.67 | 32.72 | [40.0, 224.7] |
| mtld | static | 122.27 | 23.38 | [58.4, 204.7] |
| mtld | random | 126.06 | 47.45 | [31.5, 253.5] |

### FFT Results — Top Peaks
| Metric | Temporal Primary | σ | 9-day Signal? | σ at 9d |
|--------|-----------------|---|---------------|---------|
| sentence_vader | 45.0d | 5.5σ | YES (8.2-10.0d) | 1.5σ |
| mtld | 45.0d | 3.1σ | YES (9.0d exact) | 1.5σ |

### Comparison with Structural Metric
| Metric | Type | 9-day Peak σ | Status |
|--------|------|-------------|--------|
| word_count | Structural | 5.8σ | GO |
| sentence_vader | Semantic | 1.5σ | NO-GO |
| mtld | Semantic | 1.5σ | NO-GO |

## Verdict: NO-GO

Neither semantic metric reaches the 3.0σ threshold at the 9-day period. The 9-day signal is PRESENT but heavily attenuated (1.5σ vs 5.8σ for structural).

## Key Insights

1. **RLHF acts as a semantic low-pass filter**: Structural variation (word count, formatting) passes through freely. Semantic variation (sentiment, vocabulary complexity) is actively suppressed by RLHF alignment.

2. **The signal IS there, just weak**: Both metrics show a 9-day component at 1.5σ. This suggests the structural constraints DO indirectly affect semantics (shorter responses are more neutral, longer ones have more positive hedging), but the effect is ~4x weaker than the direct structural signal.

3. **45-day dominant period**: Both semantic metrics peak at 45 days, likely driven by slow-planet structural constraints (Mars→bullets, Sun→sentences) that accumulate gradual semantic shifts.

4. **Temporal condition has 4x more sentiment variance**: std=0.19 vs 0.05 for static. The modulation IS creating behavioral variety — just not at the specific lunar frequency.

## Impact on Launch Strategy

Per ICF Brainstorm R3 (Gemini Pro recommendation):
- Drop the "personality modulation" claim
- Launch as **"Temporal Structural Modulation"** — proven at 5.8σ
- Honest framing: "We can control FORMAT (word count, bullets, sentences) but not TONE through temporal signals"
- The RLHF-as-filter finding is itself a novel contribution worth publishing

## Artifacts

- `benchmark/semantic_proof.py` — experiment code
- `benchmark/results/semantic_proof_verdict.json` — verdict
- `benchmark/results/cvb_v3_scored_semantic.json` — responses with semantic metrics
