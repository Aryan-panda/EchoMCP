import pytest
from app.config import settings
from app.utils.tunnel import (
    validate_tunnel_url,
    create_ingress_headers,
    extract_tunnel_url_from_output,
)

def test_tunnel_url_format_validation():
    """Verify validation of Cloudflare trycloudflare and custom domain ingress URLs."""
    valid_urls = [
        "https://my-subdomain.trycloudflare.com",
        "https://voice-bridge-123.trycloudflare.com",
        "https://custom-domain.example.com",
        "https://mcp.mycompany.org",
    ]
    for url in valid_urls:
        assert validate_tunnel_url(url) is True, f"Expected {url} to be valid"

    invalid_urls = [
        "http://my-subdomain.trycloudflare.com",  # Plain HTTP rejected
        "ftp://my-subdomain.trycloudflare.com",
        "",
        "not-a-url",
        "trycloudflare.com",
    ]
    for url in invalid_urls:
        assert validate_tunnel_url(url) is False, f"Expected {url} to be invalid"

def test_tunnel_log_url_extraction():
    """Verify extracting the public tunnel URL from cloudflared log output."""
    sample_log = """
    2026-09-27T17:00:00Z INF Starting tunnel tunnelID=abc-123
    2026-09-27T17:00:01Z INF Your quick Tunnel has been created! Visit it at:
    2026-09-27T17:00:01Z INF https://quick-sound-amber.trycloudflare.com
    2026-09-27T17:00:02Z INF Registered tunnel connection connIndex=0
    """
    url = extract_tunnel_url_from_output(sample_log)
    assert url == "https://quick-sound-amber.trycloudflare.com"

def test_tunnel_ingress_bearer_auth_enforcement(client):
    """
    PASS CRITERIA:
    Public ingress strictly enforces Bearer authentication on /mcp.
    """
    payload = {
        "jsonrpc": "2.0",
        "id": "probe_1",
        "method": "ping"
    }

    # 1. Missing Authorization header -> 401
    res_no_auth = client.post("/mcp", json=payload, headers={"X-Forwarded-Proto": "https"})
    assert res_no_auth.status_code == 401
    assert "Missing Authorization" in res_no_auth.json()["detail"]

    # 2. Invalid Bearer token -> 401
    bad_headers = create_ingress_headers(token="wrong-token-xyz")
    res_bad_auth = client.post("/mcp", json=payload, headers=bad_headers)
    assert res_bad_auth.status_code == 401
    assert "Invalid Bearer token" in res_bad_auth.json()["detail"]

    # 3. Valid Bearer token -> 200
    valid_headers = create_ingress_headers(token=settings.MCP_AUTH_TOKEN)
    res_valid = client.post("/mcp", json=payload, headers=valid_headers)
    assert res_valid.status_code == 200
    assert res_valid.json() == {"jsonrpc": "2.0", "id": "probe_1", "result": {}}

def test_tunnel_ingress_streamable_http_mcp_tool_call(client):
    """
    PASS CRITERIA:
    Simulates Grok calling speak_response tool over public ingress with emotion tags.
    """
    headers = create_ingress_headers(token=settings.MCP_AUTH_TOKEN, forwarded_for="203.0.113.195")
    tool_req = {
        "jsonrpc": "2.0",
        "id": "grok_call_001",
        "method": "tools/call",
        "params": {
            "name": "speak_response",
            "arguments": {
                "text": "[excited] All systems nominal! [pause] [whisper] Proceeding to warp.",
                "voice_id": "1",
                "speed": 1.0,
                "format": "wav"
            }
        }
    }

    res = client.post("/mcp", json=tool_req, headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "grok_call_001"
    assert data["result"]["isError"] is False
    assert "structured_data" in data["result"]

    audio_meta = data["result"]["structured_data"]
    assert audio_meta["status"] == "completed"
    assert audio_meta["duration_seconds"] > 0
    assert audio_meta["format"] == "wav"
    assert audio_meta["audio_id"].startswith("aud_")

def test_tunnel_public_health_and_readiness_probes(client):
    """
    PASS CRITERIA:
    Unauthenticated health and readiness probes succeed across ingress.
    """
    ingress_headers = {"X-Forwarded-Proto": "https", "X-Forwarded-For": "198.51.100.1"}

    # GET /health
    res_health = client.get("/health", headers=ingress_headers)
    assert res_health.status_code == 200
    assert res_health.json() == {"status": "ok"}

    # GET /ready
    res_ready = client.get("/ready", headers=ingress_headers)
    assert res_ready.status_code == 200
    ready_data = res_ready.json()
    assert ready_data["ready"] is True
    assert ready_data["mcp"] is True

    # GET /version
    res_ver = client.get("/version", headers=ingress_headers)
    assert res_ver.status_code == 200
    assert res_ver.json()["name"] == "grok-voice-bridge"

def test_tunnel_ingress_header_preservation_and_tracing(client):
    """Verify X-Request-ID and timing headers are preserved across ingress."""
    headers = create_ingress_headers(
        token=settings.MCP_AUTH_TOKEN,
        request_id="grok-ingress-req-999"
    )
    res = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "ping"}, headers=headers)
    assert res.status_code == 200
    assert res.headers.get("X-Request-ID") == "grok-ingress-req-999"
    assert "X-Process-Time-MS" in res.headers

def test_tunnel_public_audio_replay_streaming(client):
    """Verify generated audio can be streamed through public ingress with range requests."""
    # 1. Synthesize audio via MCP tool
    headers = create_ingress_headers(token=settings.MCP_AUTH_TOKEN)
    mcp_res = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "speak_response", "arguments": {"text": "Public tunnel replay test."}}
        },
        headers=headers
    )
    audio_id = mcp_res.json()["result"]["structured_data"]["audio_id"]

    # 2. Replay audio file via public ingress with byte range
    range_headers = {
        "X-Forwarded-Proto": "https",
        "Range": "bytes=0-43"
    }
    stream_res = client.get(f"/api/v1/audio/{audio_id}/file", headers=range_headers)
    assert stream_res.status_code == 206
    assert len(stream_res.content) == 44
    assert stream_res.content.startswith(b"RIFF")
    assert "bytes 0-43/" in stream_res.headers.get("Content-Range", "")

def test_tunnel_cors_preflight(client):
    """Verify CORS preflight handling for public browser or web integrations."""
    headers = {
        "Origin": "https://grok.x.ai",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type",
    }
    res = client.options("/mcp", headers=headers)
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") in ["https://grok.x.ai", "*"]
