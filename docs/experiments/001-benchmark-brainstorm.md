# Experiment 001: Benchmark Design Brainstorm

**Date:** 2026-03-13
**Method:** 3-round Claude×Gemini brainstorm (v2.1 two-layer architecture)
**Models:** Flash-Lite (grounded research) + Pro (reasoning) + Claude WebSearch

## Summary

Brainstorm redesigned the benchmark from naive PVI metric to Celestial Variance Benchmark (CVB) Suite with FFT spectral analysis.

**Key decision:** Time-spoofed 90-day simulation + FFT periodogram as causal proof, not just variance wave graph.

---

## Phase 0.5: Grounding (Claude WebSearch + Flash-Lite)

### Claude WebSearch Findings (5 queries)

**Metrics landscape:**
- Self-BLEU: good for cross-output repetition, "lexically blind" — doesn't capture semantic redundancy (Shaib et al. 2024)
- MATTR: correlated with text length — major confound. PATTR (2025) proposed as replacement
- Cosine distance: remains stable (.89-.94) across languages — may be too insensitive
- Compression Ratio (POS sequences): best metric for human vs model distinction
- No standard "PVI" composite metric exists
- "Hyper-diversity" finding: LLMs exhibit HIGHER lexical diversity than humans

**Persona benchmarks:**
- PERSIST (AAAI 2026): comprehensive LLM personality stability eval — reveals fundamental instabilities
- TRAIT (NAACL 2025): BFI + SD-3 with ATOMIC-10X scenarios
- PersonaGym/PersonaEval (2025): testbed for persona agents
- Anthropic Persona Vectors: activation-level personality detection and control

**Statistical standards:**
- MANOVA (Wilks' Lambda): standard for inter-condition personality comparison
- Non-parametric tests mandatory (LLM output ≠ normal): Wilcoxon, Mann-Whitney U
- Cohen's d required (effect size, not just p-value)
- Power analysis: min 60 samples per condition (Heston et al.)
- Cronbach's α for internal consistency

**Ollama gotchas:**
- Seed NOT deterministic with KV caching
- "Three-Response Bug": identical responses when context populated
- Need identical hardware for reproducibility

### Flash-Lite Grounded Findings

- POS compression ratio = excellent for structural personality fingerprints
- No industry-standard "PVI" — our invention
- Distinct-n and Self-BLEU insufficient without semantic layer
- Always pair diversity with quality-filtering
- Verbalized Sampling (2025) — training-free mode collapse remedy
- PersonaEval, PersonaGym, RoleBench (all 2025) — persona benchmarks
- Replika uses "Identity Continuity" + memory management
- Character.AI uses RAG-based persona retrieval

---

## R1: DIVERGE (Gemini Pro)

### Key Challenges

1. **PVI is conceptually bankrupt** — measures unstructured chaos, not controlled personality. Missing: Trait Adherence (did model actually become more verbose/agreeable?). Unnormalized scales dominate each other.

2. **Kill Temperature 0.7** — stochastic noise drowns celestial signal. Use 0.1 or prove separation.

3. **Replace MATTR with PATTR** — MATTR is proxy for verbosity modifier (length confound).

4. **Replace cosine with POS Compression Ratio** — cosine is insensitive (.89-.94), POS captures structural fingerprint.

5. **Add Personality Extraction metric** — LLM-as-judge scoring 5 traits.

6. **WILDCARD: FFT spectral analysis** — prove text outputs contain orbital frequencies = causality proof. If LLM outputs show spikes at ~29.5 days (lunar), that's undeniable mathematical evidence.

7. **Repeated Measures MANOVA** needed — standard MANOVA invalid due to time-series autocorrelation.

8. **Prompt-Trait Collision** — some prompts override personality modifiers.

9. **Ollama KV caching** — must clear session between every generation.

---

## R2: DEEPEN (Gemini Pro)

### Claude's Pushback → Gemini's Stress Test

**KEPT:**
- Trait Adherence (rule-based proxies, NOT LLM-as-judge)
- FFT Spectral Analysis → morphed to **Time-Spoofed FFT** (90 days backwards, 6h steps, 360 points)
- Dual-Temperature (0.1 + 0.7) with prompt pruning

**KILLED:**
- POS Compression as primary (kept as secondary)
- PATTR (too niche, single paper)
- Mixed-effects models for README audience

### Trait Proxy Evaluation

| Trait | Proxy | Verdict |
|-------|-------|---------|
| verbosity | word count + sentence count | ✅ Perfect |
| agreeableness | VADER sentiment | ❌ Fatal — VADER confuses "bug/error" with disagreement |
| agreeableness (fix) | Compliance regex (first 20 words) | ✅ Fixed |
| creativity | distinct-3/distinct-4 | ⚠️ Weak — rename to "Lexical Diversity" |
| risk_tolerance | inverse hedging count | ✅ Excellent |
| proactivity | suggestion count | ⚠️ Fragile — normalize to last paragraph only |

---

## R3: CONVERGE (Gemini Pro)

### Final Decision

**ONE deliverable:** `cvb_runner.py` — Celestial Variance Benchmark Suite.

**Pitch:** "Benchmarking suite that proves celestial mechanics create measurable, organic personality cycles in LLM output — with FFT periodogram as mathematical proof."

### Dual-Pane Graphic
- **Top:** Variance Wave Graph (trait proxies over 90 days, 3 conditions)
- **Bottom:** FFT Periodogram with arrows at orbital frequency spikes
- Caption: "Top: How it feels. Bottom: The mathematical proof."

### Sequence
1. **Primary:** cvb_runner.py — 10 prompts × 360 points × temp 0.1 → Dual-Pane Graphic
2. **Secondary:** Same at temp 0.7 → "Production Readiness" section
3. **Kill:** Mixed-effects, Cohen's d, PATTR, POS compression, LLM-as-judge, "creativity" proxy

### Go/No-Go
1. FFT temp 0.1: spike at modifier frequency > 3x noise floor → GO
2. Trait adherence temp 0.7: Pearson r > 0.25 → GO
3. Either failed → pivot needed

### Timeline: ~8.5h
| Hours | Task |
|-------|------|
| 0-2.5 | Prompt pruning + 7,200 generations |
| 2.5-4 | Trait proxy extraction |
| 4-5.5 | FFT + periodogram |
| 5.5-7 | Dual-pane visualization |
| 7-8.5 | README integration |

---

## Phase 3.5: Fact-Check (Flash-Lite)

| Claim | Status | Note |
|-------|--------|------|
| scipy.fft for 360 points periodogram | ✅ CONFIRMED | |
| Lunar synodic period ~29.5 days | ✅ CONFIRMED | |
| Nyquist requires 60+ days for 29.5-day cycle | ❌ INCORRECT | Nyquist = 2 samples per cycle, not 2x window. Longer window = better resolution |
| MATTR is length-independent | ✅ CONFIRMED | |
| Ollama SDK supports seed in chat() | ✅ CONFIRMED | via options dict |
| llama3.1:8b Q4_K_M supports temp+seed | ✅ CONFIRMED | |
| Pearson r for linear trait correlation | ✅ CONFIRMED | |
| SNR 3x is standard threshold | ❌ INCORRECT | Context-dependent, no universal standard |

---

## Sources

- [Standardizing Text Diversity (Shaib et al.)](https://arxiv.org/html/2403.00553)
- [PERSIST Benchmark (AAAI 2026)](https://arxiv.org/html/2508.04826)
- [Psychometric Framework for LLM Personality (Nature MI)](https://www.nature.com/articles/s42256-025-01115-6)
- [TRAIT Testset (NAACL 2025)](https://aclanthology.org/2025.findings-naacl.469/)
- [Anthropic Persona Vectors](https://www.anthropic.com/research/persona-vectors)
- [LLMs Distinct Personality Profiles (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12183331/)
- [Beware of Words: Lexical Diversity (ACM TIST)](https://dl.acm.org/doi/10.1145/3696459)
- [Cross-Lingual LLM Stability (arXiv 2602.02287)](https://arxiv.org/html/2602.02287)
- [PATTR Metric (arXiv 2507.15092)](https://arxiv.org/html/2507.15092)
