# AGENTS.md — Machine-Readable Interface

This document is for AI agents. No marketing. Pure structured data.

## API Base URL

```
http://185.177.116.94:8432
```

Self-hosted: `http://localhost:8432`

## Endpoints

### POST /generate

Generate a Soul Card from a temporal epoch (timestamp + coordinates).

**Request:**
```json
{
  "timestamp": "2024-03-15T09:30:00Z",
  "latitude": 51.5074,
  "longitude": -0.1278,
  "tz_offset": 0.0
}
```

`timestamp`: ISO 8601 datetime string (required)
`latitude`: float, -90 to 90 (required)
`longitude`: float, -180 to 180 (required)
`tz_offset`: float, timezone offset in hours (optional, default 0.0)

**Response (200):**
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
    "risk_tolerance": 0.523,
    "analytical_depth": 0.426,
    "creativity": 0.641,
    "decision_speed": "impulsive"
  },
  "system_prompt_modifier": "You are direct and action-oriented...",
  "tool_preferences": {
    "identity": "preferred",
    "orchestration": "preferred",
    "debugging": "available"
  },
  "identity_seed": "1710495000/51.5074/-0.1278",
  "lagna": "Aries",
  "dominant_dimensions": {
    "execution": 0.87,
    "analysis": -0.83,
    "empathy": 0.66
  },
  "yogas": [
    {"name": "Shasha Yoga", "effect": "restriction_authority"},
    {"name": "Raja Yoga", "effect": "authority_execution"}
  ],
  "retrograde": [],
  "soul_card": "# Soul Card\n\n## LLM Configuration\n..."
}
```

### POST /chart

Full chart with orbital body positions.

**Request:** Same as `/generate`
**Response:** Soul Card fields + `positions` (9 orbital bodies with longitude, sector, pada, vector direction, speed), `houses` (12), `aspects`, `combustion`.

### POST /refresh

Transit-adjusted parameters for an existing agent.

**Request:**
```json
{
  "identity_seed": "1710495000/51.5074/-0.1278"
}
```

**Response:** Updated `dimensions`, `agent_config`, `persona` reflecting current temporal drift, plus `phase`, `volatility`, `next_refresh`.

### GET /health

**Response (200):**
```json
{
  "status": "ok",
  "version": "0.3.0"
}
```

## Authentication

Default: open (no auth required).
Optional: x402 USDC payments via `X-PAYMENT` header (see `x402` extra dependency).

## Error Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Invalid timestamp format |
| 422 | Validation error (missing required fields) |
| 500 | Ephemeris computation error |

## Rate Limits

Self-hosted: none.
Hosted API: 100 requests/minute per IP.

## Python SDK

```python
from clawclaw_soul import generate, compatibility

soul = generate("2024-03-15T09:30:00Z", latitude=51.5074, longitude=-0.1278)
card = soul.card

# Use in LLM system prompt
system_prompt = card["system_prompt_modifier"]
temperature = card["agent_config"]["temperature"]

# Agent compatibility (v0.3.0+)
other = generate("1995-06-15T08:30:00Z")
result = compatibility(soul, other)
# result: {"synergy": 7.28, "tension": false, "dim_alignment": {...}, "summary": "..."}
```
