def test_mcp_speak_response_defaults(client, auth_headers, test_dirs):
    payload = {
        "jsonrpc": "2.0",
        "id": "call_1",
        "method": "tools/call",
        "params": {
            "name": "speak_response",
            "arguments": {
                "text": "Hello from Grok via MCP!"
            }
        }
    }
    response = client.post("/mcp", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "call_1"
    result = data["result"]
    assert result["isError"] is False
    assert len(result["content"]) == 1
    assert "Audio generated successfully" in result["content"][0]["text"]

    struct = result["structured_data"]
    audio_id = struct["audio_id"]
    assert audio_id.startswith("aud_")
    assert struct["status"] == "completed"
    assert struct["format"] == "wav"
    assert struct["duration_seconds"] > 0
    assert struct["audio_url"] == f"/api/v1/audio/{audio_id}"

    # Verify physical file persistence on disk
    meta_file = test_dirs["output"] / "metadata" / f"{audio_id}.json"
    assert meta_file.exists()

def test_mcp_speak_response_with_emotion_tags(client, auth_headers):
    payload = {
        "jsonrpc": "2.0",
        "id": "call_2",
        "method": "tools/call",
        "params": {
            "name": "speak_response",
            "arguments": {
                "text": "[amused] Oh, come on! [laughing] That is actually brilliant.",
                "voice_id": "1",
                "speed": 1.2,
                "format": "wav"
            }
        }
    }
    response = client.post("/mcp", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    result = data["result"]
    assert result["isError"] is False
    assert result["structured_data"]["status"] == "completed"

def test_mcp_speak_response_custom_params(client, auth_headers):
    payload = {
        "jsonrpc": "2.0",
        "id": "call_3",
        "method": "tools/call",
        "params": {
            "name": "speak_response",
            "arguments": {
                "text": "Speaking at a different pace and format.",
                "voice_id": "1",
                "speed": 1.5,
                "format": "mp3"
            }
        }
    }
    response = client.post("/mcp", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    result = data["result"]
    assert result["isError"] is False
    assert result["structured_data"]["format"] == "mp3"

def test_mcp_sequential_invocations_persist_separately(client, auth_headers, test_dirs):
    # Response 1
    p1 = {
        "jsonrpc": "2.0",
        "id": "seq_1",
        "method": "tools/call",
        "params": {
            "name": "speak_response",
            "arguments": {"text": "This is response number 1."}
        }
    }
    r1 = client.post("/mcp", json=p1, headers=auth_headers).json()
    id1 = r1["result"]["structured_data"]["audio_id"]

    # Response 2
    p2 = {
        "jsonrpc": "2.0",
        "id": "seq_2",
        "method": "tools/call",
        "params": {
            "name": "speak_response",
            "arguments": {"text": "This is response number 2."}
        }
    }
    r2 = client.post("/mcp", json=p2, headers=auth_headers).json()
    id2 = r2["result"]["structured_data"]["audio_id"]

    # Both audio records must exist independently
    assert id1 != id2
    meta_dir = test_dirs["output"] / "metadata"
    assert (meta_dir / f"{id1}.json").exists()
    assert (meta_dir / f"{id2}.json").exists()
