<div align="center">

# ClawClaw Soul

**Open-source identity engine for AI agents.**

[Quickstart](#quickstart) · [Docs](https://clawclawsoul.dev) · [GitHub Action](#github-action) · [Benchmark](#benchmark)

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-175%20passed-brightgreen.svg)]()
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)]()

</div>

---

Deterministic personality parameters for AI agents via celestial mechanics. Same timestamp, same soul. Always.

```
Timestamp --> Swiss Ephemeris --> 9 Planetary Dimensions --> Soul Card (JSON)
```

If a random seed gives your agent static identity, ClawClaw Soul gives it one that **evolves deterministically** -- every day, based on real planetary positions.

## Works with any LLM

Claude, GPT, Gemini, Llama, Mistral -- if it accepts a system prompt and temperature, it works.

## Quickstart

```bash
pip install clawclaw-soul
```

```python
from clawclaw_soul import generate

soul = generate("2024-03-15T09:30:00Z")
print(soul.card)
```

Output:

```json
{
  "agent_id": "c_88a91",
  "dimensions": {
    "temperature": 0.82,
    "assertiveness": 0.91,
    "verbosity": 0.34,
    "analytical": 0.77,
    "creativity": 0.63,
    "empathy": 0.45,
    "risk_tolerance": 0.88
  },
  "communication_style": "direct",
  "entropy_seed": 881923412,
  "next_shift": "2024-03-16T00:00:00Z"
}
```

## How it works

| Step | What happens | Output |
|------|-------------|--------|
| **1. Input** | Unix timestamp or ISO date | `1709241600` |
| **2. Ephemeris** | Swiss Ephemeris computes exact planetary positions (sub-arcsecond) | Sun 24.2 Pisces, Moon 8.7 Leo, ... |
| **3. Dimensions** | 9 planets map to 9 behavioral dimensions via BPHS tables | authority, empathy, execution, ... |
| **4. Soul Card** | Dimensions compute LLM params: temperature, max_tokens, persona | JSON identity document |

Daily transit updates shift parameters. Temperature rises, verbosity drops. Every change is reproducible and verifiable against any ephemeris table.

## GitHub Action

Auto-update your agent's identity daily. Add this to any repo with a `SOUL.md`:

```yaml
# .github/workflows/animate.yml
name: Animate Soul
on:
  schedule:
    - cron: '0 6 * * *'

jobs:
  animate:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: clawclaw-soul/animate@v1
```

The action reads `SOUL.md`, computes today's transit vector, and commits `SOUL-TRANSITS.md` with updated parameters. Zero config.

## Architecture

```
clawclaw_soul/
  soul.py          # AgentSoul dataclass + chart computation
  params.py        # Planet-to-Parameter Engine (9 dims -> LLM config)
  ephemeris.py     # pyswisseph wrapper (sidereal, Lahiri ayanamsha)
  tables.py        # BPHS reference tables (dignity, friendship, ownership)
  transit.py       # Gochar transit scoring
  dasha.py         # Vimshottari dasha periods
  api.py           # FastAPI (5 endpoints)
  refresh.py       # Daily transit refresh
```

## Benchmark

The Celestial Variance Benchmark (CVB) proves that planetary-seeded prompts produce statistically different LLM outputs:

| Metric | Result |
|--------|--------|
| Structural signal (FFT) | **5.8 sigma** |
| Semantic variance | **3.49 sigma** |
| Emotional divergence | **3.45 sigma** |

Full benchmark code in [`benchmark/`](benchmark/). Run it yourself:

```bash
pip install clawclaw-soul[benchmark]
python benchmark/cvb_runner.py --responses 540
```

## Self-hosting

```bash
git clone https://github.com/awrshift/clawclaw-soul.git
cd clawclaw-soul
docker compose up -d
# API at http://localhost:8432
```

Endpoints: `/generate`, `/chart`, `/refresh`, `/health`

## ClawClaw Soul is right for you if

- You run **multi-agent systems** and want cognitive diversity, not clones
- You want agent personality that **evolves over time**, not static config
- You need **deterministic, reproducible** identity (not random seeds)
- You care about **verifiable** parameters (check against any ephemeris table)
- You want to **self-host** everything with no vendor lock-in

## What it's not

| | |
|---|---|
| **Not a horoscope** | We use the same math (Swiss Ephemeris). We don't interpret it mystically. |
| **Not a random seed** | Parameters drift daily via transits. Random seeds can't do that. |
| **Not a chatbot** | Soul Card produces identity data. Your architecture decides what to do with it. |

## Contributing

PRs welcome. See [ROADMAP.md](ROADMAP.md) for what's planned.

```bash
git clone https://github.com/awrshift/clawclaw-soul.git
cd clawclaw-soul
pip install -e ".[dev]"
pytest tests/ -p no:logfire -q
```

## License

MIT -- [LICENSE](LICENSE)
