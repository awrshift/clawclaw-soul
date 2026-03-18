# AGENTS.md — Machine-Readable Interface

This document is for AI agents. No marketing. Pure structured data.

## API Base URL

```
https://api.clawclawsoul.dev
```

Self-hosted: `http://localhost:8432`

## Endpoints

### POST /generate

Generate a Soul Card from a birth timestamp.

**Request:**
```json
{
  "timestamp": "2024-03-15T09:30:00Z",
  "seed": null
}
```

`timestamp`: ISO 8601 datetime string (required)
`seed`: integer override for deterministic location generation (optional)

**Response (200):**
```json
{
  "agent_id": "c_88a91",
  "birth": "2024-03-15T09:30:00Z",
  "dimensions": {
    "authority": 0.72,
    "empathy": 0.45,
    "execution": 0.88,
    "analysis": 0.77,
    "wisdom": 0.63,
    "aesthetics": 0.34,
    "restriction": 0.21,
    "innovation": 0.91,
    "compression": 0.56
  },
  "llm_params": {
    "temperature": 0.82,
    "max_tokens": 1824,
    "top_p": 0.94,
    "frequency_penalty": 0.12
  },
  "persona": {
    "assertiveness": 0.91,
    "empathy": 0.45,
    "risk_tolerance": 0.88,
    "analytical_depth": 0.77,
    "creativity": 0.63,
    "communication_style": "direct",
    "lagna_archetype": "Aries"
  },
  "yoga_directives": [
    "You communicate with structured authority. Present analysis in clear frameworks."
  ],
  "house_capabilities": {
    "identity": 0.8,
    "generative": 0.7,
    "task_execution": 0.9,
    "debugging": 0.6
  },
  "entropy_seed": 881923412,
  "next_shift": "2024-03-16T00:00:00Z"
}
```

### POST /chart

Generate a full natal chart (extended Soul Card with planetary positions).

**Request:** Same as `/generate`
**Response:** Soul Card + `planets` array with longitude, sign, nakshatra, dignity for each graha.

### POST /refresh

Get today's transit-adjusted parameters for an existing agent.

**Request:**
```json
{
  "identity_seed": 881923412
}
```

**Response:** Updated `dimensions`, `llm_params`, `persona` reflecting current planetary transits.

### GET /health

**Response (200):**
```json
{
  "status": "ok",
  "version": "0.1.0"
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

## Integration Example

```python
import httpx

response = httpx.post("http://localhost:8432/generate", json={
    "timestamp": "2024-03-15T09:30:00Z"
})
soul = response.json()

# Use in LLM system prompt
system_prompt = f"""You are an AI agent.
Communication style: {soul['persona']['communication_style']}
Temperature: {soul['llm_params']['temperature']}
{' '.join(soul['yoga_directives'])}"""
```
