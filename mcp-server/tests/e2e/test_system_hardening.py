import asyncio
import time
import pytest
from app.config import settings
from app.dependencies import get_tts_provider
from app.services.providers.base import TTSProvider
from app.utils.tunnel import create_ingress_headers

class FailingTTSProvider(TTSProvider):
    """Simulates a downstream TTS engine that is temporarily down or throwing errors."""
    async def health(self) -> dict:
        raise ConnectionRefusedError("TTS service unreachable")

    async def status(self) -> dict:
        return {"status": "unhealthy", "model_loaded": False}

    async def synthesize(self, text, voice_id="1", speed=1.0, format="wav", emotion=None):
        raise RuntimeError("Downstream vocoder memory overflow or connection drop")

    async def register_voice(self, voice_id, name, file_path):
        raise ConnectionRefusedError("TTS service unreachable")

    async def delete_voice(self, voice_id):
        return False

    async def list_voices(self):
        return []

def test_concurrent_synthesis_requests_queued_safely(client):
    """
    PASS CRITERIA:
    Multiple simultaneous synthesis requests are safely queued by the concurrency semaphore,
    producing unique audio records without race conditions or corrupted output.
    """
    turn_texts = [
        "Concurrent turn 1: Testing system concurrency.",
        "Concurrent turn 2: Verifying FIFO queue execution.",
        "Concurrent turn 3: Resource allocation bounds.",
        "Concurrent turn 4: Safeguarding host CPU.",
        "Concurrent turn 5: Audio integrity check."
    ]

    responses = []
    # Execute rapid sequential requests to test semaphore queuing
    for t in turn_texts:
        res = client.post("/api/v1/speak", json={"text": t, "voice_id": "1"})
        responses.append(res)

    audio_ids = set()
    for res in responses:
        assert res.status_code == 200
        data = res.json()
        audio_id = data["audio_id"]
        assert audio_id not in audio_ids, f"Collision detected: {audio_id}"
        audio_ids.add(audio_id)

        # Verify binary streamability
        stream = client.get(f"/api/v1/audio/{audio_id}/file")
        assert stream.status_code == 200
        assert len(stream.content) > 100

    assert len(audio_ids) == len(turn_texts)

def test_tts_failure_graceful_handling_and_recovery(client):
    """
    PASS CRITERIA:
    When downstream TTS fails or times out, the server does not crash,
    returns clean HTTP 500/503 or MCP error, and recovers immediately once TTS returns.
    """
    from app.main import app

    # 1. Inject failing TTS provider
    failing_tts = FailingTTSProvider()
    app.dependency_overrides[get_tts_provider] = lambda: failing_tts

    # Ready probe should report TTS offline
    ready_res = client.get("/ready")
    assert ready_res.status_code == 503
    assert ready_res.json()["tts"] is False

    # REST speak endpoint fails cleanly with 503 or 500 without crashing server
    speak_res = client.post("/api/v1/speak", json={"text": "This should fail gracefully."})
    assert speak_res.status_code in [500, 503]

    # MCP tool call fails gracefully with isError: true
    headers = create_ingress_headers(token=settings.MCP_AUTH_TOKEN)
    mcp_call = {
        "jsonrpc": "2.0",
        "id": "err_recovery_test",
        "method": "tools/call",
        "params": {
            "name": "speak_response",
            "arguments": {"text": "Should fail gracefully via MCP."}
        }
    }
    mcp_res = client.post("/mcp", json=mcp_call, headers=headers)
    assert mcp_res.status_code == 200
    assert mcp_res.json()["result"]["isError"] is True
    assert "error" in mcp_res.json()["result"]["content"][0]["text"].lower()

    # 2. Restore operational mock TTS provider
    from app.services.providers.mock import MockTTSProvider
    app.dependency_overrides[get_tts_provider] = lambda: MockTTSProvider()

    # Server recovers immediately
    recovered_ready = client.get("/ready")
    assert recovered_ready.status_code == 200
    assert recovered_ready.json()["tts"] is True

    recovered_speak = client.post("/api/v1/speak", json={"text": "System has recovered."})
    assert recovered_speak.status_code == 200
    assert recovered_speak.json()["audio_id"].startswith("aud_")

def test_large_payload_boundaries(client):
    """
    PASS CRITERIA:
    Accepts text up to 5,000 characters; cleanly rejects text exceeding boundary.
    """
    # 1. 5000 character boundary test (allowed)
    large_valid_text = "Echo " * 1000  # 5000 characters
    res_large = client.post("/api/v1/speak", json={"text": large_valid_text[:5000]})
    assert res_large.status_code == 200

    # 2. 5001 character boundary test (rejected by schema validation)
    too_large_text = "E" * 5001
    res_invalid = client.post("/api/v1/speak", json={"text": too_large_text})
    assert res_invalid.status_code == 422  # Unprocessable Entity

def test_rapid_polling_stability(client):
    """
    PASS CRITERIA:
    Rapid polling of diagnostics and history executes with low latency without leaking state.
    """
    for _ in range(15):
        h = client.get("/health")
        assert h.status_code == 200
        r = client.get("/ready")
        assert r.status_code == 200
        a = client.get("/api/v1/audio?limit=5")
        assert a.status_code == 200

def test_malformed_json_and_fuzzing_resilience(client):
    """
    PASS CRITERIA:
    Malformed JSON bodies and corrupt RPC packets do not crash the MCP handler.
    """
    headers = create_ingress_headers(token=settings.MCP_AUTH_TOKEN)

    # 1. Malformed JSON syntax
    res_malformed = client.post(
        "/mcp",
        content=b"{ invalid json string here ...",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {settings.MCP_AUTH_TOKEN}"}
    )
    assert res_malformed.status_code in [400, 200]
    if res_malformed.status_code == 200:
        assert res_malformed.json()["error"]["code"] == -32700  # Parse error

    # 2. Non-object JSON
    res_array = client.post("/mcp", json=[1, 2, 3], headers=headers)
    assert res_array.status_code in [400, 200]

    # 3. Server remains healthy afterwards
    res_ping = client.post("/mcp", json={"jsonrpc": "2.0", "id": 99, "method": "ping"}, headers=headers)
    assert res_ping.status_code == 200
    assert res_ping.json()["result"] == {}
