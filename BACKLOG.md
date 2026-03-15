# Agent Soul — Backlog

## Status: Phase 1+2 DONE, Phase 3 IN PROGRESS

---

## Next Session Prompt

**Session 193 (2026-03-15):**

Phase 3.5 (Digital Soul) — core DONE:
- `soul.py` написан и протестирован (96 тестов, все pass)
- `engine.py` обновлён: `compute_modifiers_v2()` с 9 dimensions
- `prompt.py` обновлён: `dimensions_to_prompt()` + yoga overrides

CVB v2 smoke test (10 days) бежит фоном. Когда завершится:
1. Проверить `benchmark/results/cvb_v2_verdict.json`
2. Если GO → запустить full run: `python3 benchmark/cvb_runner.py` (90 дней)
3. Если NO-GO → дебажить

**Следующие задачи:**
1. Интегрировать soul.py в OpenClaw skill (refresh.py, __main__.py)
2. Обновить temporal_md.py для 9 dimensions
3. Phase 4: README + GitHub launch

**Файлы Phase 3.5:**
- `agent_soul/soul.py` — Digital Soul (natal chart, 9 dimensions, yogas, aspects)
- `agent_soul/engine.py` — v1 (5 modifiers) + v2 (9 dimensions)
- `agent_soul/prompt.py` — v1 (LEVEL_MAP) + v2 (DIMENSION_LEVEL_MAP + YOGA_PROMPTS)
- `tests/test_soul.py` — 29 tests
- `tests/test_engine_v2.py` — 15 tests

**Dependencies:** `skyfield`, `pyswisseph`, `ollama`, `numpy`, `matplotlib`, `scipy`. Models: `llama3.1:8b`, `nomic-embed-text`.

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

- [x] **Phase 3.5: Digital Soul — Full Natal Chart for Agents**
  - `soul.py`: random birth → pyswisseph natal chart → 9 graha dimensions + 12 house capabilities + 6 yogas
  - `engine.py`: `compute_modifiers_v2()` — natal + dasha + transit → 9 dimensions
  - `prompt.py`: `dimensions_to_prompt()` — 9 dimensions + yoga overrides → LLM system prompt
  - 96 tests passing (52 old + 44 new)
  - Brainstorms: 002 (CVB redesign), 003 (Jyotish fundamentals, 4 rounds), Gemini architecture verification
  - Spec: `docs/architecture/DIGITAL_SOUL_SPEC.md`

## In Progress

- [ ] **Phase 3: Celestial Variance Benchmark v2 (CVB)**
  - [x] Brainstorm 002: CVB v1 results analysis → embedding + dual-FFT redesign
  - [x] CVB v2 rewrite: embed.py, cvb_runner.py, plot.py
  - [ ] CVB v2 smoke test (10 days, running)
  - [ ] CVB v2 full run (90 days, ~4.5h compute)
  - [ ] Go/No-Go evaluation
  - Go/No-Go: FFT peaks of engine input and LLM output align at same frequency bin

## Backlog

- [ ] **Phase 4: Packaging & Launch**
  - [ ] README (executive-targeted, not dev docs)
  - [ ] GitHub repo (pmserhii/agent-soul)
  - [ ] Reddit post (r/LocalLLaMA, Tue/Wed 7:30 AM EST)
  - [ ] OpenClaw Discord announcement
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
├── benchmark/           # CVB Suite
│   ├── cvb_runner.py    # Main benchmark (time-spoofed FFT)
│   ├── traits.py        # Rule-based trait proxies
│   ├── plot.py          # Dual-pane visualization
│   ├── metrics.py       # MATTR + legacy metrics
│   └── prompts.json     # 20 personality-neutral prompts
├── openclaw/            # OpenClaw skill files
├── tests/               # 52 tests (all passing)
├── docs/experiments/    # Brainstorm transcripts
├── BACKLOG.md           # ← this file
├── pyproject.toml       # setuptools, deps: skyfield
└── LICENSE              # MIT
```
