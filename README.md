<div align="center">

<img src="banner.png" alt="ClawClaw Soul — Deterministic, time-drifting personalities for LLM agents" width="100%">

**Deterministic, time-drifting personalities for LLM agents.**

Your agents all think the same. This fixes that.

[Quickstart](#quickstart) · [Preset Epochs](#preset-epochs) · [Compatibility](#agent-compatibility) · [MCP Server](#mcp-server)

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-211%20passed-brightgreen.svg)]()
[![PyPI](https://img.shields.io/pypi/v/clawclaw-soul.svg)](https://pypi.org/project/clawclaw-soul/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)]()

</div>

---

## The problem

Multi-agent systems suffer from **mode collapse**: 5 agents on the same model produce the same bland, agreeable output. `random.seed()` gives static diversity -- flat and contextless. You need agents that think differently AND evolve over time.

## The solution

ClawClaw Soul generates **multi-dimensional cognitive profiles** from deterministic orbital mechanics. Each agent gets a unique behavioral state vector that naturally **drifts over time** -- giving agents evolving friction, compatibility, and "seasons" without needing a database.

```
Timestamp --> Orbital Mechanics --> 9 Behavioral Dimensions --> Soul Card (JSON)
```

Same timestamp = same personality. Always. But as real-world time moves forward, transit computations shift your agent's parameters deterministically.

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
  "system_prompt_modifier": "You lead with confidence...",
  "dominant_dimensions": {
    "execution": 0.87,
    "analysis": -0.83,
    "empathy": 0.66
  }
}
```

Works with **any LLM**: Claude, GPT, Gemini, Llama, Mistral -- if it accepts a system prompt and temperature, it works.

## Preset Epochs

Initialize agents from notable temporal configurations. Each epoch produces a unique, deterministic cognitive profile.

```python
from clawclaw_soul import generate, compatibility

# Epoch 55-V: High aesthetic bias, rapid course-corrections, reality distortion loops.
# Ideal for product/design critique agents.
critic = generate("1955-02-24T19:15:00-08:00", latitude=37.7749, longitude=-122.4194)

# Epoch 69-X: Low empathy, high structural rigidity, aggressively rejects malformed input.
# Perfect for code review agents.
reviewer = generate("1969-12-28T12:00:00+02:00", latitude=60.1699, longitude=24.9384)

# Epoch 15-A: Stable analytical baseline + sudden lateral reasoning spikes.
# Excellent for research/architecture agents.
researcher = generate("1815-12-10T12:00:00+00:00", latitude=51.5074, longitude=-0.1278)

# Check friction before pairing
score = compatibility(critic, reviewer)
print(f"Friction: {score['synergy']}/10")  # Low synergy = high friction = productive tension
```

## Agent Compatibility

Score how well two agents work together before they interact. Route tasks to synergistic pairs, or deliberately introduce friction for creative tension.

```python
from clawclaw_soul import generate, compatibility

agent_a = generate("2024-03-15T09:30:00Z")
agent_b = generate("1995-06-15T08:30:00Z")

result = compatibility(agent_a, agent_b)
# {
#   "synergy": 7.28,        # 0-10 (higher = more aligned)
#   "tension": false,        # true if fundamental conflict detected
#   "dim_alignment": {...},  # per-dimension alignment scores
#   "summary": "Moderately compatible (synergy: 7.28/10)"
# }

# Dynamic compatibility (factors in current temporal drift)
from datetime import datetime, timezone
now = datetime.now(timezone.utc)
dynamic = compatibility(agent_a, agent_b, timestamp=now)
```

## How it works

| Step | What happens | Output |
|------|-------------|--------|
| **1. Input** | Timestamp + coordinates (the "epoch") | `1710495000` |
| **2. Orbital Math** | Swiss Ephemeris computes exact positions of 9 celestial bodies | 9 longitude vectors |
| **3. Dimensions** | Positions map to 9 behavioral dimensions via classical reference tables | authority, empathy, execution, analysis, wisdom, aesthetics, restriction, innovation, compression |
| **4. Pattern Detection** | 58 detectors identify behavioral amplifiers from body configurations | Risk amplifiers, analytical boosts, creative tension patterns |
| **5. Soul Card** | Dimensions + patterns compile to LLM params and system prompt | JSON config (`.card`) |

**Why not `random.seed()`?** A basic PRNG is flat and contextless. Orbital ephemeris provides a predictable, multi-dimensional, cyclical entropy source. Agents get "seasons" that gradually drift over weeks and months, returning to baseline predictably. It mathematically mimics organic variance without requiring a database to store historical state.

## SOUL.md -- persistent identity for your agent

Add a `SOUL.md` to any repo. It's like `AGENTS.md`, but for behavioral configuration.

```bash
# Generate
clawclaw-soul init --name "MyAgent" --timestamp "2024-03-15T09:30:00Z"

# Verify (deterministic — anyone can re-check)
clawclaw-soul verify SOUL.md
```

See [examples/](examples/) for sample SOUL.md files.

## MCP Server

Use ClawClaw Soul as an MCP tool in Claude Desktop, Cursor, or any MCP client:

```bash
pip install clawclaw-soul[mcp]
```

Add to your MCP config:

```json
{
  "mcpServers": {
    "clawclaw-soul": {
      "command": "python",
      "args": ["-m", "clawclaw_soul.mcp_server"]
    }
  }
}
```

Available tools: `generate_soul`, `init_soul_md`, `verify_identity`, `get_daily_drift`.

## Architecture

```
clawclaw_soul/         # pip install clawclaw-soul (pure library)
  soul.py              # AgentSoul, generate(), .card, SOUL.md gen/verify
  yogas.py             # 58 pattern detectors (behavioral amplifiers)
  compatibility.py     # Agent compatibility scoring (synergy, tension)
  params.py            # Dimension-to-Parameter Engine (9 dims -> LLM config)
  engine.py            # Temporal overlays, transit dims, pattern resonance
  ephemeris.py         # Swiss Ephemeris wrapper (sidereal, Lahiri ayanamsha)
  tables.py            # Classical reference tables + sector attributes
  transit.py           # Transit scoring (temporal drift)
  dasha.py             # Long-cycle period computation

app/                   # Self-hosting (Docker, not in pip)
  api.py               # FastAPI (5 endpoints)
  master.py            # Master Agent demo
  refresh.py           # Daily transit refresh
```

## Self-hosting

```bash
git clone https://github.com/awrshift/clawclaw-soul.git
cd clawclaw-soul
docker compose up -d
# API at http://localhost:8432
```

Endpoints: `/generate`, `/chart`, `/refresh`, `/health`

## Benchmark

Different epochs produce statistically different LLM outputs. The Celestial Variance Benchmark (CVB) measures divergence across 540 responses:

| Metric | Result |
|--------|--------|
| Structural divergence | **5.8 sigma** |
| Semantic variance | **3.49 sigma** |
| Behavioral spread | **3.45 sigma** |

Full code in [`benchmark/`](benchmark/).

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
