def test_mcp_invalid_json_body(client, auth_headers):
    response = client.post(
        "/mcp",
        content="not valid json {[[",
        headers={"Content-Type": "application/json", **auth_headers}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["error"]["code"] == -32700

def test_mcp_non_object_json_body(client, auth_headers):
    response = client.post(
        "/mcp",
        json=["item1", "item2"],
        headers=auth_headers
    )
    assert response.status_code == 400
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["error"]["code"] == -32600

def test_mcp_missing_method(client, auth_headers):
    response = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": "1"},
        headers=auth_headers
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == -32600

def test_mcp_unknown_method(client, auth_headers):
    response = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": "err_1", "method": "nonexistent/custom_method"},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "err_1"
    assert data["error"]["code"] == -32601
    assert "not supported" in data["error"]["message"]

def test_mcp_unknown_tool_call(client, auth_headers):
    payload = {
        "jsonrpc": "2.0",
        "id": "err_2",
        "method": "tools/call",
        "params": {
            "name": "unsupported_tool",
            "arguments": {}
        }
    }
    response = client.post("/mcp", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "err_2"
    assert data["error"]["code"] == -32601
    assert "not found" in data["error"]["message"]

def test_mcp_speak_missing_required_text(client, auth_headers):
    payload = {
        "jsonrpc": "2.0",
        "id": "val_1",
        "method": "tools/call",
        "params": {
            "name": "speak_response",
            "arguments": {
                "voice_id": "1"
            }
        }
    }
    response = client.post("/mcp", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    result = data["result"]
    assert result["isError"] is True
    assert "validation" in result["content"][0]["text"].lower()

def test_mcp_speak_invalid_speed(client, auth_headers):
    payload = {
        "jsonrpc": "2.0",
        "id": "val_2",
        "method": "tools/call",
        "params": {
            "name": "speak_response",
            "arguments": {
                "text": "Valid text with invalid speed.",
                "speed": 5.0
            }
        }
    }
    response = client.post("/mcp", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    result = data["result"]
    assert result["isError"] is True

def test_mcp_speak_invalid_format(client, auth_headers):
    payload = {
        "jsonrpc": "2.0",
        "id": "val_3",
        "method": "tools/call",
        "params": {
            "name": "speak_response",
            "arguments": {
                "text": "Valid text with invalid format.",
                "format": "flac"
            }
        }
    }
    response = client.post("/mcp", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    result = data["result"]
    assert result["isError"] is True

def test_mcp_speak_empty_text_after_tags(client, auth_headers):
    payload = {
        "jsonrpc": "2.0",
        "id": "val_4",
        "method": "tools/call",
        "params": {
            "name": "speak_response",
            "arguments": {
                "text": "[amused]   [laughing]  "
            }
        }
    }
    response = client.post("/mcp", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    result = data["result"]
    assert result["isError"] is True
    assert "no pronounceable content" in result["content"][0]["text"]

def test_mcp_speak_text_too_large(client, auth_headers):
    payload = {
        "jsonrpc": "2.0",
        "id": "val_5",
        "method": "tools/call",
        "params": {
            "name": "speak_response",
            "arguments": {
                "text": "A" * 5001
            }
        }
    }
    response = client.post("/mcp", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    result = data["result"]
    assert result["isError"] is True
