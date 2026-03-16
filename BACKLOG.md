# Agent Soul — Backlog

## Status: Phase 1-3 DONE, ICF + Semantic Proof DONE. Phase 4 (Launch) next.

---

## Next Session Prompt

**For Session 198:**

### Done in Session 197:
1. **ICF Research** (3-round Claude×Gemini brainstorm): Agent Soul is **genuinely novel**
   - No existing system combines orbital mechanics + LLM behavior modulation + FFT proof
   - Closest: SoulSpec/SOUL.md (static), PersonaLLM (static), Character.AI (memory-based), Dynamic Personality ACL 2025 (emergent, not engine-driven)
   - Key rebranding: "Temporal Behavioral Modulation (TBM)" not "personality modulation"
   - Product name stays "Agent Soul", tech framework = "TBM"
2. **Semantic Proof (Experiment 006)**: NO-GO — sentence-VADER and MTLD show 9-day signal at 1.5σ (below 3σ threshold)
   - Key finding: RLHF acts as semantic low-pass filter — structural variation passes (5.8σ), semantic is attenuated (1.5σ)
   - Launch claim: "Temporal Structural Modulation" (honest, proven at 5.8σ)
3. **Kill list confirmed**: "Astrology for AI" framing, adversarial applications, anti-bot bypass

### Next session plan (Phase 4: Launch):

**Timeline: 8 days**

1. **Swarm De-correlation Demo** (Days 1-3, ~15h):
   - `SwarmTBM` class: N agents with distinct orbital seeds
   - Jupyter notebook: `preventing_swarm_collapse.ipynb`
   - Show diversity metrics vs un-modulated control group

2. **README + TBM Framework Docs** (Days 4-6, ~12h):
   - Executive-targeted README (not dev docs)
   - Frame as TBM framework, not "astrology for AI"
   - Include 5.8σ result + RLHF-as-filter insight
   - 1-sentence pitch: "Agent Soul uses temporal orbital mechanics to deterministically modulate LLM behavior, providing a mathematical framework to eliminate homogenization in AI swarms."

3. **Open Source Launch** (Days 7-8):
   - GitHub repo: pmserhii/agent-soul
   - Reddit: r/LocalLLaMA, r/MachineLearning (Tue/Wed 7:30 AM EST)
   - Keep Steganography/Provenance as future blog post (needs own proof)

**Tests:** 124 passing. **Commits:** `87d381f` (CVB v3), TBD (semantic proof)
**Dependencies:** `pyswisseph`, `google-genai`, `numpy`, `scipy`, `matplotlib`, `nltk`, `lexical-diversity`

---

## Completed

- [x] **Phase 1: Core Engine** — 8 modules, 52 tests passing
  - tables.py, ephemeris.py, dasha.py, transit.py, engine.py, prompt.py, temporal_md.py, refresh.py
  - Commit: `14cad75`

- [x] **Phase 2: OpenClaw Skill + Prompt Translation**
  - SKILL.md, openclaw.json, install.py, __main__.py
  - Caching (4h buckets, JSON at ~/.agent-soul/cache.json)

- [x] **Benchmark Brainstorm** (Experiment 001)
  - 3-round Claude×Gemini, full transcript: `docs/experiments/001-benchmark-brainstorm.md`
  - Decision: redesign benchmark from naive PVI to CVB Suite with FFT

- [x] **CVB Code Written** (benchmark rewrite per brainstorm)
  - `benchmark/cvb_runner.py` — time-spoofed generation + FFT + adherence
  - `benchmark/traits.py` — 5 rule-based trait proxies
  - `benchmark/plot.py` — dual-pane (variance wave + FFT periodogram)
  - Smoke test running

- [x] **Phase 3: Celestial Variance Benchmark — GO (5.8σ)**
  - CVB v1 (regex proxies): FAIL — compliance_score constant, agreeableness r=0.0
  - CVB v2 (embeddings): FAIL — cosine distance measures TOPIC not TONE, range 0.09
  - **CVB v3 (structural constraints): GO** — word_count FFT peak at 9.0d, 5.8σ
  - Brainstorms: 001 (PVI→CVB), 002 (v1→v2 redesign), 004 (v2→v3 structural pivot)
  - Key insight: bypass RLHF by shifting signal from personality nudges to formatting rules
  - Engine: pure transit weights (0,0,1), gain=3, continuous mapping (not discrete levels)
  - Verification: 540 Gemini Flash responses, static control different peak (1.9d)
  - 124 tests, commit TBD

- [x] **Phase 3.5: Digital Soul — Full Natal Chart for Agents**
  - `soul.py`: random birth → pyswisseph natal chart → 9 graha dimensions + 12 house capabilities + 6 yogas
  - `engine.py`: `compute_modifiers_v2()` — natal + dasha + transit → 9 dimensions
  - `prompt.py`: `dimensions_to_prompt()` — 9 dimensions + yoga overrides → LLM system prompt
  - 96 tests passing (52 old + 44 new)
  - Brainstorms: 002 (CVB redesign), 003 (Jyotish fundamentals, 4 rounds), Gemini architecture verification
  - Spec: `docs/architecture/DIGITAL_SOUL_SPEC.md`

- [x] **ICF Research Brainstorm (Session 197)**
  - 3-round Claude×Gemini (Pro), Phase 0.5 + 3.5 (Flash-Lite grounded)
  - Result: Agent Soul is genuinely novel — no existing temporal behavioral modulation with FFT proof
  - Competitive landscape: SoulSpec (static), PersonaLLM (static), Character.AI (memory), Dynamic Personality ACL'25 (emergent)
  - Rebranding: "Temporal Behavioral Modulation (TBM)" framework
  - Kill list: "Astrology for AI" framing, adversarial apps, anti-bot

- [x] **Experiment 006: Semantic Proof (Session 197)**
  - Sentence-VADER + MTLD on existing 540 responses
  - Result: NO-GO — 9-day signal at 1.5σ (threshold: 3.0σ)
  - Key insight: RLHF = semantic low-pass filter (structural passes at 5.8σ, semantic attenuated to 1.5σ)
  - Decision: launch as "Temporal Structural Modulation" (honest claim)
  - Report: `docs/experiments/006-semantic-proof.md`

## In Progress

- [ ] **Phase 4: Packaging & Open Source Launch**
  - [x] ICF research: validate uniqueness (Claude×Gemini brainstorm)
  - [x] Competitive landscape map
  - [x] Semantic proof experiment (NO-GO → honest claim)
  - [ ] Swarm De-correlation demo (Jupyter notebook)
  - [ ] README (executive-targeted, TBM framing)
  - [ ] GitHub repo (pmserhii/agent-soul)
  - [ ] Reddit post (r/LocalLLaMA, Tue/Wed 7:30 AM EST)
  - [ ] OpenClaw Discord announcement

## Backlog

- [ ] **Phase 5: Autonomous Agent Testing**
  - [ ] Create 3-5 Claude Code agents with unique Agent Soul seeds
  - [ ] Deploy on real tasks (code review, research, writing)
  - [ ] A/B test: with Agent Soul vs without
  - [ ] Track personality evolution over 2+ weeks
  - [ ] Collect qualitative feedback: do personalities feel distinct?
  - [ ] TEP-1 draft (SoulSpec Temporal Extension)

## Key Decisions

**2026-03-13 — Benchmark redesign (Brainstorm 001):**
Original PVI (cosine+selfBLEU+MATTR) killed — measures chaos, not controlled variance.
New approach: Time-spoofed FFT + trait adherence proxies + dual temperature.
Rationale: FFT proves causality (orbital frequencies in output), not just "looks wavy."

**2026-03-13 — Trait proxies over LLM-as-judge:**
Rule-based proxies (word count, compliance regex, MATTR, hedging count, suggestion count)
chosen over LLM-as-judge. Reproducible, no extra model bias, zero compute cost.

**2026-03-13 — CVB design (from brainstorm R3):**
- Time-spoofed 90 days (not real-time), 6h step = 360 data points
- 10 prompts pruned from 20 (lowest baseline variance)
- Dual temp (0.1 + 0.7) for signal isolation
- FFT periodogram to prove orbital frequencies in output
- Dual-pane graphic: top=wave, bottom=periodogram
- Benchmark weights (0.20, 0.25, 0.55) — transit-heavy to show signal. Production: (0.60, 0.25, 0.15)

**2026-03-14 — Benchmark weights fix:**
Default weights (natal 60%, transit 15%) produce std=0.02 over 90 days — too flat for benchmark.
Boosted transit to 55% for benchmark mode → std=0.10, range crosses zero. Production weights unchanged.
`compute_modifiers()` now accepts `weights=(natal, dasha, transit)` parameter.

**2026-03-15 — CVB v1 results → v2 redesign (Brainstorm 002):**
CVB v1 results: FFT 30-day peak was windowing artifact (bin 1 = 1/total_time). Rule-based
trait proxies broken (compliance_score constant, agreeableness r=0.0). Redesigned:
- Embedding-based scoring via nomic-embed-text (replaces regex proxies)
- Proper DSP: detrend + Hanning window before FFT
- Dual-FFT proof: compare engine input FFT vs LLM output FFT (peaks must align)
- Go/No-Go: same peak frequency bin in both FFTs

**2026-03-15 — Full Natal Chart for Agents (Brainstorm 003, 4 rounds):**
Agents get full Jyotish natal charts like humans. Birth = random coords + random time
(for max uniqueness in tests). Classical basis: Muhurta/Mundane astrology for Yantras.
9 Grahas → 9 LLM parameters. 12 Bhavas → capability domains. Yogas → archetypes.
Hierarchy: Natal (ceiling) > Dasha (throttle) > Transit (trigger).
Anti-patterns: no malicious behavior from malefics, no caste/gender encoding,
no hard override of user prompts. Full details: docs/experiments/003-*.md

**2026-03-16 — CVB v3 GO (Brainstorm 004 implemented):**
Structural constraints replace personality nudges. Continuous mapping (not discrete levels)
with gain=3 amplification. Pure transit weights (0,0,1) for benchmark. empathy→word_count
is the causal channel: FFT peak at 9.0d in both engine input and LLM output (5.8σ).
Static control peaks at 1.9d (different) → not an artifact.

**2026-03-16 — ICF Research + Semantic Proof (Brainstorm 005, Session 197):**
3-round Claude×Gemini brainstorm confirmed Agent Soul is novel. No existing system combines
orbital mechanics + LLM modulation + FFT proof. Rebranded: "Temporal Behavioral Modulation (TBM)."
Semantic proof (Experiment 006) ran sentence-VADER + MTLD on existing 540 responses.
Result: 9-day signal present at 1.5σ but below 3σ threshold → NO-GO on semantic claim.
Key insight: RLHF acts as semantic low-pass filter — structural constraints bypass it (5.8σ),
semantic properties are attenuated (1.5σ). Launch with honest claim: "Temporal Structural Modulation."
Swarm De-correlation identified as strongest application angle.

## Project Structure

```
~/Desktop/agent-soul/
├── agent_soul/          # Core library (8 modules)
│   ├── engine.py        # compute_modifiers() — main API
│   ├── ephemeris.py     # Skyfield wrapper
│   ├── tables.py        # BPHS reference tables
│   ├── dasha.py         # Vimshottari computation
│   ├── transit.py       # Gochar scoring
│   ├── prompt.py        # Modifier → LLM prompt (7 levels)
│   ├── temporal_md.py   # TEMPORAL.md generator
│   └── refresh.py       # CLI + OpenClaw heartbeat
├── benchmark/           # CVB Suite v3
│   ├── cvb_runner.py    # Main benchmark (structural constraints + FFT)
│   ├── proxy_metrics.py # Zero-cost proxy metrics (word_count, hedge, etc.)
│   ├── semantic_proof.py # Experiment 006: VADER + MTLD + FFT
│   ├── embed.py         # Gemini embedding-001 (v2, deprecated)
│   ├── traits.py        # Rule-based trait proxies (v1, deprecated)
│   ├── plot.py          # Multi-panel visualization
│   ├── metrics.py       # MATTR + legacy metrics
│   └── prompts.json     # 20 personality-neutral prompts
├── openclaw/            # OpenClaw skill files
├── tests/               # 124 tests (all passing)
├── docs/experiments/    # Brainstorm transcripts
├── BACKLOG.md           # ← this file
├── pyproject.toml       # setuptools, deps: skyfield
└── LICENSE              # MIT
```
