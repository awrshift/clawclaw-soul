"""Tests for x402 payment gate.

Tests that paid endpoints return 402 without payment,
and /health remains free. Uses a separate app instance
with SOUL_PAY_TO_ADDRESS set to enable x402 middleware.

x402 returns payment info in base64-encoded `payment-required` header.
"""

import base64
import importlib
import json
import os

import pytest
from fastapi.testclient import TestClient

WALLET = "0x2E37839a9c3d3082FBf02d0b9D1AF0AEDa7e9C34"
NETWORK = "eip155:84532"


def _decode_payment_header(response) -> dict:
    """Decode base64 payment-required header from 402 response."""
    raw = response.headers.get("payment-required", "")
    return json.loads(base64.b64decode(raw))


@pytest.fixture(scope="module")
def paid_client():
    """Create a test client with x402 middleware enabled."""
    os.environ["SOUL_PAY_TO_ADDRESS"] = WALLET
    os.environ["SOUL_NETWORK"] = NETWORK

    import app.api as api_module

    importlib.reload(api_module)
    client = TestClient(api_module.app, raise_server_exceptions=False)
    yield client

    del os.environ["SOUL_PAY_TO_ADDRESS"]
    del os.environ["SOUL_NETWORK"]
    importlib.reload(api_module)


GENERATE_PAYLOAD = {
    "timestamp": "1990-01-15T10:30:00Z",
    "latitude": 52.5200,
    "longitude": 13.4050,
}

CHART_PAYLOAD = {
    "timestamp": "2014-03-21T08:15:00Z",
    "latitude": 25.3176,
    "longitude": 83.0107,
}


class TestHealthAlwaysFree:
    """GET /health must never require payment."""

    def test_health_returns_200(self, paid_client):
        r = paid_client.get("/health")
        assert r.status_code == 200

    def test_health_shows_x402_enabled(self, paid_client):
        r = paid_client.get("/health")
        assert r.json()["payments"] == "x402"


class TestPaidEndpointsRequirePayment:
    """Paid endpoints must return 402 without X-PAYMENT header."""

    def test_generate_returns_402(self, paid_client):
        r = paid_client.post("/generate", json=GENERATE_PAYLOAD)
        assert r.status_code == 402

    def test_chart_returns_402(self, paid_client):
        r = paid_client.post("/chart", json=CHART_PAYLOAD)
        assert r.status_code == 402

    def test_regenerate_returns_402(self, paid_client):
        r = paid_client.post("/regenerate?identity_seed=632399400/52.5200/13.4050")
        assert r.status_code == 402


class TestPaymentResponseFormat:
    """402 response must include payment instructions in payment-required header."""

    def test_402_has_payment_required_header(self, paid_client):
        r = paid_client.post("/generate", json=GENERATE_PAYLOAD)
        assert r.status_code == 402
        assert "payment-required" in r.headers

    def test_402_header_is_valid_base64_json(self, paid_client):
        r = paid_client.post("/generate", json=GENERATE_PAYLOAD)
        data = _decode_payment_header(r)
        assert "accepts" in data
        assert len(data["accepts"]) > 0

    def test_402_has_correct_network(self, paid_client):
        r = paid_client.post("/generate", json=GENERATE_PAYLOAD)
        data = _decode_payment_header(r)
        assert data["accepts"][0]["network"] == NETWORK

    def test_402_has_pay_to_address(self, paid_client):
        r = paid_client.post("/generate", json=GENERATE_PAYLOAD)
        data = _decode_payment_header(r)
        assert data["accepts"][0]["payTo"] == WALLET

    def test_402_has_usdc_asset(self, paid_client):
        r = paid_client.post("/generate", json=GENERATE_PAYLOAD)
        data = _decode_payment_header(r)
        assert data["accepts"][0]["extra"]["name"] == "USDC"

    def test_402_generate_price_1_dollar(self, paid_client):
        """$1.00 = 1000000 (USDC has 6 decimals)."""
        r = paid_client.post("/generate", json=GENERATE_PAYLOAD)
        data = _decode_payment_header(r)
        assert data["accepts"][0]["amount"] == "1000000"

    def test_402_chart_price_2_dollars(self, paid_client):
        """$2.00 = 2000000 units."""
        r = paid_client.post("/chart", json=CHART_PAYLOAD)
        data = _decode_payment_header(r)
        assert data["accepts"][0]["amount"] == "2000000"

    def test_402_chart_costs_more_than_generate(self, paid_client):
        r_gen = paid_client.post("/generate", json=GENERATE_PAYLOAD)
        r_chart = paid_client.post("/chart", json=CHART_PAYLOAD)
        gen_price = int(_decode_payment_header(r_gen)["accepts"][0]["amount"])
        chart_price = int(_decode_payment_header(r_chart)["accepts"][0]["amount"])
        assert chart_price > gen_price

    def test_402_has_resource_description(self, paid_client):
        r = paid_client.post("/generate", json=GENERATE_PAYLOAD)
        data = _decode_payment_header(r)
        assert "resource" in data
        assert data["resource"]["mimeType"] == "application/json"
