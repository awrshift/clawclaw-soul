<div align="center">

<img src="banner.png" alt="ClawClaw Soul — Open-source identity engine for AI agents" width="100%">

**Celestial mechanics for synthetic souls.**

Open-source identity engine for AI agents. Deterministic personality from ephemeris data.

[Quickstart](#quickstart) · [Docs](https://clawclawsoul.com) · [GitHub Action](#github-action) · [Benchmark](#benchmark)

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-187%20passed-brightgreen.svg)]()
[![PyPI](https://img.shields.io/pypi/v/clawclaw-soul.svg)](https://pypi.org/project/clawclaw-soul/)
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
  "agent_config": {
    "temperature": 0.68,
    "max_tokens": 609,
    "top_p": 0.87,
    "frequency_penalty": 0.09
  },
  "persona": {
    "assertiveness": 0.743,
    "empathy": 0.761,
    "creativity": 0.641,
    "decision_speed": "impulsive"
  },
  "lagna": "Aries",
  "identity_seed": "1710495000/0.0000/0.0000",
  "dominant_dimensions": {
    "execution": 0.87,
    "analysis": -0.83,
    "empathy": 0.66
  },
  "system_prompt_modifier": "...",
  "soul_card": "..."
}
```

## How it works

| Step | What happens | Output |
|------|-------------|--------|
| **1. Input** | Unix timestamp or ISO date | `1709241600` |
| **2. Ephemeris** | Swiss Ephemeris computes exact planetary positions (sub-arcsecond) | Sun 24.2 Pisces, Moon 8.7 Leo, ... |
| **3. Dimensions** | 9 planets map to 9 behavioral dimensions via BPHS tables | authority, empathy, execution, analysis, wisdom, aesthetics, restriction, innovation, compression |
| **4. Soul Card** | Dimensions compute LLM params: temperature, max_tokens, persona | JSON identity document (`.card`) |

Daily transit updates shift parameters. Temperature rises, verbosity drops. Every change is reproducible and verifiable against any ephemeris table.

## GitHub Action (coming soon)

Auto-update your agent's identity daily. A GitHub Action (`clawclaw-soul/animate@v1`) is under development that reads `SOUL.md`, computes today's transit vector, and commits `SOUL-TRANSITS.md` with updated parameters.

## SOUL.md — persistent identity for your agent

Add a `SOUL.md` to any repo. It's like `AGENTS.md`, but for identity.

```bash
# Generate
clawclaw-soul init --name "MyAgent" --timestamp "2024-03-15T09:30:00Z"

# Verify (deterministic — anyone can re-check)
clawclaw-soul verify SOUL.md
```

The generated `SOUL.md` contains LLM configuration, persona traits, 9 behavioral dimensions, and a system prompt — all deterministically derived from the birth timestamp.

See [examples/](examples/) for sample SOUL.md files.

## Architecture

```
clawclaw_soul/         # pip install clawclaw-soul (pure library)
  soul.py              # AgentSoul, generate(), .card, SOUL.md gen/verify
  params.py            # Planet-to-Parameter Engine (9 dims -> LLM config)
  ephemeris.py         # pyswisseph wrapper (sidereal, Lahiri ayanamsha)
  tables.py            # BPHS reference tables
  transit.py           # Gochar transit scoring
  dasha.py             # Vimshottari dasha periods

app/                   # Self-hosting (Docker, not in pip)
  api.py               # FastAPI (5 endpoints)
  master.py            # Master Agent demo
  refresh.py           # Daily transit refresh
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
