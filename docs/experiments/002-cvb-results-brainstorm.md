# Experiment 002: CVB Results Analysis — Brainstorm Transcript

**Date:** 2026-03-15
**Participants:** Claude (orchestrator) x Gemini 3.1 Pro (adversarial)
**Trigger:** CVB smoke test results — partial FFT pass, full adherence fail

## Round 1: DIVERGE (Gemini challenges)

Key findings:
1. **FFT 30-day peak is a WINDOWING ARTIFACT** — fundamental frequency = 1/total_time. Not a real signal.
2. **Trait adherence is what actually matters** — FFT without adherence = "RNG seeded by planets"
3. **Rule-based proxies are dead** — regex too crude for modern LLMs
4. **8B Q4 model has non-linear response** — activation cliffs, not smooth steering
5. **Wildcard: feed raw celestial state** to LLM instead of abstract floats

## Round 2: DEEPEN (Claude pushes back, Gemini stress-tests)

Survivors:
- **A: Embedding-based measurement** — nomic-embed-text cosine distance to semantic anchors
- **B: Proper DSP pipeline** — 90 days + detrend + Hanning window + FFT

New idea: Multi-frequency cross-trait isolation (inject 2 cycles into 2 traits, prove no bleed)

## Round 3: CONVERGE

**KILL:** Multi-frequency (too complex for v1), embeddings for structural traits like verbosity (mathematically invalid), searching for "any" peak (P-hacking)

**WINNER: Single-Trait Dual-FFT Pipeline**
- Run 90-day engine as-is (blended planets)
- Score outputs with nomic-embed-text against ONE semantic trait anchors
- FFT both the engine input modifiers AND the embedding scores
- Proof = their frequency peaks align at the same bin

**Go/No-Go:** FFT of embedding scores peaks at the SAME frequency bin as FFT of engine input modifiers

**Timeline:** 4 hours (gen → embed → DSP → visual)

**Pitch:** "We prove LLMs predictably adopt cyclical system prompts by demonstrating that the dominant frequencies of their semantic embedding trajectories perfectly match the mathematical frequencies of the injected prompt modifiers."

## Key Decision

The original CVB approach (rule-based trait proxies) is abandoned. New approach:
1. Replace regex proxies with embedding cosine distance
2. Add proper DSP (detrend + Hanning window)
3. Compare FFT of ENGINE INPUT vs FFT of LLM OUTPUT
4. Single semantic trait (agreeableness/optimism), not 5
5. Visual: dual-pane (time domain + frequency domain overlay)
