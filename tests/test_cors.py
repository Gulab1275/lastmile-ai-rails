"""
Tests for CORS configuration and origin filtering.
Verifies JSON env parsing and ensures '*' is never used with credentials.
"""
from fastapi.testclient import TestClient

from services.api.config import _get_allowed_origins
from services.api.main import app

client = TestClient(app)


def test_cors_preflight_allowed_origin():
    """Valid origin receives Access-Control-Allow-Origin matching the request origin."""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_disallows_wildcard_with_credentials(monkeypatch):
    """Wildcard origin '*' must be filtered out when credentials are true."""
    monkeypatch.setenv("ALLOWED_ORIGINS", '["http://localhost:3000", "*", "https://custom.domain.com"]')
    parsed = _get_allowed_origins()
    assert "*" not in parsed
    assert "http://localhost:3000" in parsed
    assert "https://custom.domain.com" in parsed
