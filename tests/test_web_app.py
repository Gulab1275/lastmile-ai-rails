"""
Tests for Rahbar Interactive PWA Web Application and Static Asset Serving.
"""
from fastapi.testclient import TestClient


def test_root_contains_app_link(client: TestClient):
    """Test that GET / returns the /app link in the response."""
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "app" in data
    assert data["app"] == "/app"


def test_app_endpoint_serves_html(client: TestClient):
    """Test that GET /app serves the interactive HTML dashboard."""
    resp = client.get("/app")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    content = resp.text
    # Check essential UI components
    assert "رہبر" in content
    assert "Rahbar" in content
    assert "Widow Intake" in content
    assert "Digital Twin" in content
    assert "Audit Ledger" in content


def test_manifest_and_sw_accessible(client: TestClient):
    """Test that PWA manifest.json and sw.js are accessible via /static."""
    manifest_resp = client.get("/static/manifest.json")
    assert manifest_resp.status_code == 200
    manifest_data = manifest_resp.json()
    assert manifest_data["short_name"] == "Rahbar"

    sw_resp = client.get("/static/sw.js")
    assert sw_resp.status_code == 200
    assert "CACHE_NAME" in sw_resp.text


def test_sample_audio_assets_accessible(client: TestClient):
    """Test that pre-generated demo audio files are accessible via /static/audio."""
    audio_clean_resp = client.get("/static/audio/sample_parveen_clean.mp3")
    assert audio_clean_resp.status_code == 200
    assert len(audio_clean_resp.content) > 10000

    audio_blurry_resp = client.get("/static/audio/sample_sakina_blurry.mp3")
    assert audio_blurry_resp.status_code == 200
    assert len(audio_blurry_resp.content) > 10000
