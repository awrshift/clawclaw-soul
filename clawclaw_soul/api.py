"""Soul Oracle API — stateless Jyotish-to-Parameter engine.

POST /generate  →  {timestamp, lat, lon}  →  agent config
GET  /health    →  service status

All computation is deterministic: same input → same output, always.
No database, no storage. Pure planetary math.

Payment: x402 protocol (HTTP 402 → pay USDC → get content).
Set SOUL_PAY_TO_ADDRESS env var to enable payments.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from clawclaw_soul.engine import compute_modifiers_v2
from clawclaw_soul.params import build_soul_card, soul_to_params, timestamp_to_params
from clawclaw_soul.soul import AgentSoul

app = FastAPI(
    title="Soul Oracle API",
    version="0.2.0",
    description="Deterministic planetary mathematics → AI agent execution parameters. x402-native.",
)

# ── x402 Payment Gate ──

PAY_TO = os.getenv("SOUL_PAY_TO_ADDRESS")

if PAY_TO:
    from x402.http import FacilitatorConfig, HTTPFacilitatorClient, PaymentOption
    from x402.http.middleware.fastapi import PaymentMiddlewareASGI
    from x402.http.types import RouteConfig
    from x402.mechanisms.evm.exact import ExactEvmServerScheme
    from x402.server import x402ResourceServer

    NETWORK = os.getenv("SOUL_NETWORK", "eip155:84532")  # Base Sepolia default
    FACILITATOR_URL = os.getenv(
        "SOUL_FACILITATOR_URL", "https://x402.org/facilitator"
    )

    facilitator = HTTPFacilitatorClient(FacilitatorConfig(url=FACILITATOR_URL))
    server = x402ResourceServer(facilitator)
    server.register(NETWORK, ExactEvmServerScheme())

    def _opt(price: str) -> list[PaymentOption]:
        return [PaymentOption(scheme="exact", pay_to=PAY_TO, price=price, network=NETWORK)]

    x402_routes = {
        "POST /generate": RouteConfig(
            accepts=_opt("$1.00"),
            mime_type="application/json",
            description="Generate agent identity from spacetime coordinates",
        ),
        "POST /chart": RouteConfig(
            accepts=_opt("$2.00"),
            mime_type="application/json",
            description="Full Vedic natal chart for agent",
        ),
        "POST /regenerate": RouteConfig(
            accepts=_opt("$1.00"),
            mime_type="application/json",
            description="Regenerate agent params from identity seed",
        ),
        "POST /refresh": RouteConfig(
            accepts=_opt("$0.01"),
            mime_type="application/json",
            description="Daily transit update for existing agent identity",
        ),
    }

    app.add_middleware(PaymentMiddlewareASGI, routes=x402_routes, server=server)


# ── Request / Response Models ──


class GenerateRequest(BaseModel):
    """Input: a moment in spacetime."""

    timestamp: datetime = Field(
        ...,
        description="ISO 8601 datetime (UTC preferred). Example: 2024-06-15T14:30:00Z",
    )
    latitude: float = Field(
        ..., ge=-90.0, le=90.0, description="Latitude (-90 to 90)"
    )
    longitude: float = Field(
        ..., ge=-180.0, le=180.0, description="Longitude (-180 to 180)"
    )
    tz_offset: float = Field(
        default=0.0,
        ge=-12.0,
        le=14.0,
        description="Timezone offset from UTC (hours). Only used if timestamp is naive.",
    )

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_unix_timestamp(cls, v):
        """Accept unix timestamps (int/float) as well as ISO strings."""
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(v, tz=timezone.utc)
        return v


class PersonaTraits(BaseModel):
    assertiveness: float
    empathy: float
    risk_tolerance: float
    analytical_depth: float
    creativity: float
    decision_speed: str


class AgentConfig(BaseModel):
    temperature: float
    max_tokens: int
    top_p: float
    frequency_penalty: float


class GenerateResponse(BaseModel):
    """Output: complete agent configuration."""

    agent_config: AgentConfig
    persona: PersonaTraits
    system_prompt_modifier: str
    tool_preferences: dict[str, str]
    identity_seed: str
    lagna: str
    dominant_dimensions: dict[str, float]
    yogas: list[dict]
    retrograde: list[str]
    soul_card: str


class ChartResponse(BaseModel):
    """Full natal chart data (for debugging / advanced use)."""

    lagna_sign: str
    lagna_lon: float
    positions: dict
    houses: list
    dimensions: dict[str, float]
    capabilities: dict[str, float]
    yogas: list[dict]
    retrograde_planets: list[str]
    combustion: dict[str, bool]


class RefreshRequest(BaseModel):
    """Input for daily transit refresh."""

    identity_seed: str = Field(
        ...,
        description="Agent identity seed from /generate (format: UNIX_TS/LAT/LON)",
    )
    date: datetime = Field(
        default=None,
        description="Date for transit calculation (default: now). ISO 8601.",
    )

    @field_validator("date", mode="before")
    @classmethod
    def default_to_now(cls, v):
        if v is None:
            return datetime.now(timezone.utc)
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(v, tz=timezone.utc)
        return v


class RefreshResponse(BaseModel):
    """Daily transit update: how today's planets modify the agent's base personality."""

    identity_seed: str
    computed_at: str
    agent_config: AgentConfig
    persona: PersonaTraits
    system_prompt_modifier: str
    dimensions: dict[str, float]
    phase: str
    volatility: float
    next_refresh: str


class HealthResponse(BaseModel):
    status: str
    version: str
    engine: str
    payments: str


# ── Endpoints ──


@app.get("/health", response_model=HealthResponse)
def health():
    """Service health check. Always free."""
    return HealthResponse(
        status="ok",
        version="0.2.0",
        engine="pyswisseph+lahiri",
        payments="x402" if PAY_TO else "disabled",
    )


@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    """Core product: timestamp + coordinates → agent execution parameters.

    Fully deterministic. No database, no storage.
    Same input always produces the same output.
    """
    try:
        params = timestamp_to_params(
            birth_dt=req.timestamp,
            latitude=req.latitude,
            longitude=req.longitude,
            tz_offset=req.tz_offset,
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Computation error: {e}")

    return GenerateResponse(**params)


@app.post("/chart", response_model=ChartResponse)
def chart(req: GenerateRequest):
    """Full natal chart data. For debugging and advanced integrations.

    Returns raw Vedic chart: positions, houses, dimensions, yogas.
    """
    try:
        soul = AgentSoul(
            birth_dt=req.timestamp,
            latitude=req.latitude,
            longitude=req.longitude,
            tz_offset=req.tz_offset,
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Computation error: {e}")

    return ChartResponse(
        lagna_sign=soul.lagna_sign,
        lagna_lon=round(soul.lagna_lon, 4),
        positions={
            name: {
                "sign": p["sign"],
                "degree": round(p["degree"], 2),
                "nakshatra": p["nakshatra"],
                "pada": p["pada"],
                "retrograde": p["retrograde"],
            }
            for name, p in soul.positions.items()
        },
        houses=[
            {
                "number": h["number"],
                "sign": h["sign"],
                "lord": h["lord"],
                "planets": h["planets"],
            }
            for h in soul.houses
        ],
        dimensions=soul.dimensions,
        capabilities=soul.capabilities,
        yogas=soul.yogas,
        retrograde_planets=soul.retrograde_planets,
        combustion=soul.combustion,
    )


def _parse_identity_seed(seed: str) -> dict:
    """Parse identity_seed into params dict. Raises HTTPException on error."""
    try:
        parts = seed.split("/")
        if len(parts) != 3:
            raise ValueError("Invalid seed format. Expected: UNIX_TS/LAT/LON")

        birth_dt = datetime.fromtimestamp(int(parts[0]), tz=timezone.utc)
        latitude = float(parts[1])
        longitude = float(parts[2])
    except (ValueError, IndexError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid identity_seed: {e}")

    return timestamp_to_params(
        birth_dt=birth_dt,
        latitude=latitude,
        longitude=longitude,
    )


@app.post("/regenerate")
def regenerate(identity_seed: str):
    """Regenerate agent params from identity seed.

    Identity seed format: UNIX_TS/LAT/LON
    Proves stateless regeneration: no storage needed.
    Accepts identity_seed as query parameter.
    """
    return _parse_identity_seed(identity_seed)


@app.post("/refresh", response_model=RefreshResponse)
def refresh(req: RefreshRequest):
    """Daily transit refresh: how today's planets modify the agent's personality.

    Agent calls this daily with its identity_seed.
    Returns updated execution parameters reflecting current transits,
    active dasha period, and volatility level.

    The base natal identity never changes — only the daily modifiers shift.
    """
    try:
        parts = req.identity_seed.split("/")
        if len(parts) != 3:
            raise ValueError("Expected: UNIX_TS/LAT/LON")

        birth_dt = datetime.fromtimestamp(int(parts[0]), tz=timezone.utc)
        latitude = float(parts[1])
        longitude = float(parts[2])
    except (ValueError, IndexError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid identity_seed: {e}")

    try:
        soul = AgentSoul(
            birth_dt=birth_dt,
            latitude=latitude,
            longitude=longitude,
            tz_offset=0.0,
        )

        result = compute_modifiers_v2(soul, timestamp=req.date)

        # Re-compute LLM params from transit-adjusted dimensions
        from clawclaw_soul.params import (
            compute_temperature,
            compute_max_tokens,
            compute_top_p,
            compute_frequency_penalty,
            compute_persona_traits,
            build_system_prompt_modifier,
        )

        dims = result["dimensions"]

        return RefreshResponse(
            identity_seed=req.identity_seed,
            computed_at=result["computed_at"],
            agent_config=AgentConfig(
                temperature=compute_temperature(dims),
                max_tokens=compute_max_tokens(dims),
                top_p=compute_top_p(dims),
                frequency_penalty=compute_frequency_penalty(dims),
            ),
            persona=PersonaTraits(**compute_persona_traits(dims)),
            system_prompt_modifier=build_system_prompt_modifier(
                result["lagna"], result["yogas"], dims
            ),
            dimensions=dims,
            phase=result["phase"],
            volatility=result["volatility"],
            next_refresh=result["next_refresh"],
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Computation error: {e}")
