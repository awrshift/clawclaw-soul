"""Tests for Soul Oracle API endpoints."""

from fastapi.testclient import TestClient

from app.api import app

client = TestClient(app)


class TestHealth:
    def test_health_returns_ok(self):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["engine"] == "pyswisseph+lahiri"

    def test_health_has_version(self):
        r = client.get("/health")
        assert "version" in r.json()


class TestGenerate:
    """POST /generate — core product endpoint."""

    VALID_PAYLOAD = {
        "timestamp": "1990-01-15T10:30:00Z",
        "latitude": 51.5074,
        "longitude": -0.1278,
    }

    def test_generate_returns_200(self):
        r = client.post("/generate", json=self.VALID_PAYLOAD)
        assert r.status_code == 200

    def test_generate_has_agent_config(self):
        r = client.post("/generate", json=self.VALID_PAYLOAD)
        data = r.json()
        cfg = data["agent_config"]
        assert "temperature" in cfg
        assert "max_tokens" in cfg
        assert "top_p" in cfg
        assert "frequency_penalty" in cfg

    def test_generate_has_persona(self):
        r = client.post("/generate", json=self.VALID_PAYLOAD)
        data = r.json()
        persona = data["persona"]
        assert "assertiveness" in persona
        assert "empathy" in persona
        assert "decision_speed" in persona

    def test_generate_has_system_prompt(self):
        r = client.post("/generate", json=self.VALID_PAYLOAD)
        data = r.json()
        assert isinstance(data["system_prompt_modifier"], str)
        assert len(data["system_prompt_modifier"]) > 10

    def test_generate_has_identity_seed(self):
        r = client.post("/generate", json=self.VALID_PAYLOAD)
        data = r.json()
        assert "/" in data["identity_seed"]

    def test_generate_deterministic(self):
        """Same input must always produce same output."""
        r1 = client.post("/generate", json=self.VALID_PAYLOAD)
        r2 = client.post("/generate", json=self.VALID_PAYLOAD)
        assert r1.json() == r2.json()

    def test_generate_different_timestamps_differ(self):
        """Different timestamps must produce different configs."""
        payload2 = {
            "timestamp": "2003-08-20T06:00:00Z",
            "latitude": 40.7128,
            "longitude": -74.0060,
        }
        r1 = client.post("/generate", json=self.VALID_PAYLOAD)
        r2 = client.post("/generate", json=payload2)
        assert r1.json()["agent_config"] != r2.json()["agent_config"]

    def test_generate_accepts_unix_timestamp(self):
        payload = {
            "timestamp": 631882200,  # 1990-01-09 some time
            "latitude": 55.0,
            "longitude": 37.0,
        }
        r = client.post("/generate", json=payload)
        assert r.status_code == 200

    def test_generate_temperature_in_range(self):
        r = client.post("/generate", json=self.VALID_PAYLOAD)
        temp = r.json()["agent_config"]["temperature"]
        assert 0.3 <= temp <= 1.3

    def test_generate_max_tokens_in_range(self):
        r = client.post("/generate", json=self.VALID_PAYLOAD)
        mt = r.json()["agent_config"]["max_tokens"]
        assert 256 <= mt <= 4096

    def test_generate_top_p_in_range(self):
        r = client.post("/generate", json=self.VALID_PAYLOAD)
        tp = r.json()["agent_config"]["top_p"]
        assert 0.7 <= tp <= 1.0

    def test_generate_has_yogas(self):
        r = client.post("/generate", json=self.VALID_PAYLOAD)
        data = r.json()
        assert isinstance(data["yogas"], list)

    def test_generate_has_dominant_dimensions(self):
        r = client.post("/generate", json=self.VALID_PAYLOAD)
        data = r.json()
        dims = data["dominant_dimensions"]
        assert len(dims) == 3  # top 3

    def test_generate_has_tool_preferences(self):
        r = client.post("/generate", json=self.VALID_PAYLOAD)
        data = r.json()
        prefs = data["tool_preferences"]
        assert isinstance(prefs, dict)
        for v in prefs.values():
            assert v in ("preferred", "available", "restricted")


class TestGenerateValidation:
    """Input validation for /generate."""

    def test_missing_timestamp(self):
        r = client.post("/generate", json={"latitude": 55.0, "longitude": 37.0})
        assert r.status_code == 422

    def test_missing_latitude(self):
        r = client.post(
            "/generate",
            json={"timestamp": "2024-01-01T00:00:00Z", "longitude": 37.0},
        )
        assert r.status_code == 422

    def test_latitude_out_of_range(self):
        r = client.post(
            "/generate",
            json={
                "timestamp": "2024-01-01T00:00:00Z",
                "latitude": 91.0,
                "longitude": 37.0,
            },
        )
        assert r.status_code == 422

    def test_longitude_out_of_range(self):
        r = client.post(
            "/generate",
            json={
                "timestamp": "2024-01-01T00:00:00Z",
                "latitude": 55.0,
                "longitude": 181.0,
            },
        )
        assert r.status_code == 422


class TestChart:
    """POST /chart — full natal chart endpoint."""

    PAYLOAD = {
        "timestamp": "2014-03-21T08:15:00Z",
        "latitude": 25.3176,
        "longitude": 83.0107,
    }

    def test_chart_returns_200(self):
        r = client.post("/chart", json=self.PAYLOAD)
        assert r.status_code == 200

    def test_chart_has_positions(self):
        r = client.post("/chart", json=self.PAYLOAD)
        data = r.json()
        positions = data["positions"]
        assert "Sun" in positions
        assert "Moon" in positions
        assert "Rahu" in positions
        assert "Ketu" in positions
        assert len(positions) == 9

    def test_chart_has_12_houses(self):
        r = client.post("/chart", json=self.PAYLOAD)
        data = r.json()
        assert len(data["houses"]) == 12

    def test_chart_has_dimensions(self):
        r = client.post("/chart", json=self.PAYLOAD)
        data = r.json()
        assert len(data["dimensions"]) == 9

    def test_chart_has_capabilities(self):
        r = client.post("/chart", json=self.PAYLOAD)
        data = r.json()
        assert len(data["capabilities"]) == 12

    def test_chart_deterministic(self):
        r1 = client.post("/chart", json=self.PAYLOAD)
        r2 = client.post("/chart", json=self.PAYLOAD)
        assert r1.json() == r2.json()


class TestRegenerate:
    """POST /regenerate — stateless identity regeneration."""

    def test_regenerate_matches_generate(self):
        """Regenerate from identity_seed must produce identical params."""
        payload = {
            "timestamp": "1990-01-15T10:30:00+00:00",
            "latitude": 51.5074,
            "longitude": -0.1278,
        }
        r1 = client.post("/generate", json=payload)
        seed = r1.json()["identity_seed"]

        r2 = client.post(f"/regenerate?identity_seed={seed}")
        assert r2.status_code == 200

        # Core params must match
        assert r1.json()["agent_config"] == r2.json()["agent_config"]
        assert r1.json()["persona"] == r2.json()["persona"]

    def test_regenerate_invalid_seed(self):
        r = client.post("/regenerate?identity_seed=garbage")
        assert r.status_code == 400
