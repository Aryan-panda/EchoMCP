import io
import wave
import pytest
from app.config import settings
from app.utils.tunnel import create_ingress_headers

def test_grok_e2e_connector_handshake_and_capabilities(client):
    """
    PASS CRITERIA:
    Grok consumer connector performs full MCP initialization handshake and discovery.
    """
    headers = create_ingress_headers(token=settings.MCP_AUTH_TOKEN)

    # 1. Initialize Request from Grok consumer connector
    init_payload = {
        "jsonrpc": "2.0",
        "id": "grok_init_001",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "grok-consumer-agent",
                "version": "2.0"
            }
        }
    }
    init_res = client.post("/mcp", json=init_payload, headers=headers)
    assert init_res.status_code == 200
    init_data = init_res.json()
    assert init_data["jsonrpc"] == "2.0"
    assert init_data["id"] == "grok_init_001"
    assert init_data["result"]["protocolVersion"] == "2024-11-05"
    assert "tools" in init_data["result"]["capabilities"]
    assert init_data["result"]["serverInfo"]["name"] == "grok-voice-bridge"

    # 2. Client acknowledges with notifications/initialized
    notify_payload = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    }
    notify_res = client.post("/mcp", json=notify_payload, headers=headers)
    assert notify_res.status_code in [200, 204]

    # 3. Ping probe
    ping_res = client.post("/mcp", json={"jsonrpc": "2.0", "id": "p1", "method": "ping"}, headers=headers)
    assert ping_res.status_code == 200
    assert ping_res.json() == {"jsonrpc": "2.0", "id": "p1", "result": {}}

def test_grok_e2e_tool_discovery(client):
    """
    PASS CRITERIA:
    Grok discovers speak_response tool with complete schema and parameters.
    """
    headers = create_ingress_headers(token=settings.MCP_AUTH_TOKEN)
    list_payload = {
        "jsonrpc": "2.0",
        "id": "grok_tools_001",
        "method": "tools/list"
    }
    res = client.post("/mcp", json=list_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    tools = data["result"]["tools"]

    speak_tool = next((t for t in tools if t["name"] == "speak_response"), None)
    assert speak_tool is not None
    assert "convert" in speak_tool["description"].lower() or "speech" in speak_tool["description"].lower()

    schema = speak_tool["inputSchema"]
    assert "text" in schema["properties"]
    assert "voice_id" in schema["properties"]
    assert "speed" in schema["properties"]
    assert "format" in schema["properties"]
    assert "text" in schema["required"]

def test_grok_e2e_single_turn_with_emotion_tags(client):
    """
    PASS CRITERIA:
    Grok invokes speak_response with emotion tags.
    Tags are stripped from spoken content, audio is persisted and playable.
    """
    headers = create_ingress_headers(token=settings.MCP_AUTH_TOKEN)
    call_payload = {
        "jsonrpc": "2.0",
        "id": "grok_call_001",
        "method": "tools/call",
        "params": {
            "name": "speak_response",
            "arguments": {
                "text": "[amused] Oh, come on. Did you really think that would work? [laughing] That is hilarious.",
                "voice_id": "1",
                "speed": 1.0,
                "format": "wav"
            }
        }
    }

    res = client.post("/mcp", json=call_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["result"]["isError"] is False
    structured = data["result"]["structured_data"]
    audio_id = structured["audio_id"]
    assert audio_id.startswith("aud_")
    assert structured["status"] == "completed"
    assert structured["format"] == "wav"
    assert structured["duration_seconds"] > 0

    # Verify content message contains success info
    content_text = data["result"]["content"][0]["text"]
    assert audio_id in content_text
    assert "generated successfully" in content_text.lower()

    # Verify generated audio file is playable via streaming endpoint
    audio_res = client.get(f"/api/v1/audio/{audio_id}/file")
    assert audio_res.status_code == 200
    assert audio_res.headers["content-type"] == "audio/wav"
    assert len(audio_res.content) > 100

    # Verify metadata record contains clean text without emotion tags
    meta_res = client.get(f"/api/v1/audio/{audio_id}")
    assert meta_res.status_code == 200
    meta = meta_res.json()
    assert "[amused]" not in meta["text"]
    assert "[laughing]" not in meta["text"]
    assert "Oh, come on. Did you really think that would work? That is hilarious." in meta["text"]

def test_grok_e2e_multi_turn_dialogue_flow(client):
    """
    PASS CRITERIA:
    Simulates a multi-turn conversation between user and Grok.
    Each turn generates distinct, sequential, persisted audio turns that can be replayed.
    """
    headers = create_ingress_headers(token=settings.MCP_AUTH_TOKEN)

    dialogue_turns = [
        # Turn 1
        {
            "user_prompt": "What is quantum entanglement?",
            "grok_speech": "[excited] Imagine two coins flipped across the galaxy that always land on the same side! [pause] That's entanglement.",
        },
        # Turn 2
        {
            "user_prompt": "Can it transmit information faster than light?",
            "grok_speech": "[whisper] Here's the catch... [pause:600] No, it strictly respects relativistic causality.",
        },
        # Turn 3
        {
            "user_prompt": "That is mind-bending!",
            "grok_speech": "[laughing] Physics has a wonderful way of surprising us! [happy] Glad you enjoyed exploring it.",
        },
    ]

    audio_turn_ids = []
    for i, turn in enumerate(dialogue_turns, 1):
        call_req = {
            "jsonrpc": "2.0",
            "id": f"turn_{i}",
            "method": "tools/call",
            "params": {
                "name": "speak_response",
                "arguments": {
                    "text": turn["grok_speech"],
                    "voice_id": "1",
                    "speed": 1.0,
                    "format": "wav",
                },
            },
        }
        res = client.post("/mcp", json=call_req, headers=headers)
        assert res.status_code == 200
        result = res.json()["result"]
        assert result["isError"] is False
        audio_id = result["structured_data"]["audio_id"]
        audio_turn_ids.append(audio_id)

    # Verify all turns exist and are sequentially playable
    for audio_id in audio_turn_ids:
        play_res = client.get(f"/api/v1/audio/{audio_id}/file")
        assert play_res.status_code == 200
        assert play_res.headers["content-type"] == "audio/wav"
        assert len(play_res.content) > 200

    # Verify history lists all turns in reverse chronological order
    hist_res = client.get("/api/v1/audio?limit=10")
    assert hist_res.status_code == 200
    history_items = hist_res.json()["items"]
    history_ids = [item["audio_id"] for item in history_items]

    for a_id in audio_turn_ids:
        assert a_id in history_ids

    # Turn 3 (latest) must precede Turn 1 in history
    assert history_ids.index(audio_turn_ids[2]) < history_ids.index(audio_turn_ids[0])

def test_grok_e2e_error_handling_empty_after_tags(client):
    """
    PASS CRITERIA:
    If Grok provides only emotion/pause tags, tool execution fails gracefully
    with isError: true and clean diagnostic message without crashing the server.
    """
    headers = create_ingress_headers(token=settings.MCP_AUTH_TOKEN)
    call_req = {
        "jsonrpc": "2.0",
        "id": "err_001",
        "method": "tools/call",
        "params": {
            "name": "speak_response",
            "arguments": {
                "text": "[happy] [whisper] [pause]",
                "voice_id": "1"
            }
        }
    }
    res = client.post("/mcp", json=call_req, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["result"]["isError"] is True
    assert "no pronounceable content" in data["result"]["content"][0]["text"].lower()

def test_grok_e2e_error_handling_invalid_parameters(client):
    """
    PASS CRITERIA:
    Invalid parameter validation (e.g. out-of-bounds speed, invalid format)
    returns clean MCP error response.
    """
    headers = create_ingress_headers(token=settings.MCP_AUTH_TOKEN)

    # 1. Invalid speed (exceeds max 2.0)
    req_speed = {
        "jsonrpc": "2.0",
        "id": "err_speed",
        "method": "tools/call",
        "params": {
            "name": "speak_response",
            "arguments": {"text": "Valid text.", "speed": 10.0}
        }
    }
    res_speed = client.post("/mcp", json=req_speed, headers=headers)
    assert res_speed.status_code == 200
    assert res_speed.json()["result"]["isError"] is True
    assert "speed" in res_speed.json()["result"]["content"][0]["text"].lower()

    # 2. Invalid format
    req_fmt = {
        "jsonrpc": "2.0",
        "id": "err_fmt",
        "method": "tools/call",
        "params": {
            "name": "speak_response",
            "arguments": {"text": "Valid text.", "format": "flac"}
        }
    }
    res_fmt = client.post("/mcp", json=req_fmt, headers=headers)
    assert res_fmt.status_code == 200
    assert res_fmt.json()["result"]["isError"] is True
    assert "format" in res_fmt.json()["result"]["content"][0]["text"].lower()
