def test_mcp_tools_list_discovery(client, auth_headers):
    payload = {
        "jsonrpc": "2.0",
        "id": "list_1",
        "method": "tools/list"
    }
    response = client.post("/mcp", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "list_1"
    assert "result" in data
    assert "tools" in data["result"]
    tools = data["result"]["tools"]
    assert len(tools) == 1

    tool = tools[0]
    assert tool["name"] == "speak_response"
    
    # Verify description mandates emotion/prosody instruction handling
    expected_desc = (
        "This tool converts a generated response into speech using the configured local voice. "
        "The supplied text may contain supported emotion/prosody control tags. "
        "Interpret those tags as speech instructions and never speak the control tags themselves."
    )
    assert tool["description"] == expected_desc

    schema = tool["inputSchema"]
    assert schema["type"] == "object"
    assert "text" in schema["required"]
    assert schema["properties"]["text"]["type"] == "string"
    assert schema["properties"]["voice_id"]["default"] == "1"
    assert schema["properties"]["speed"]["default"] == 1.0
    assert schema["properties"]["speed"]["minimum"] == 0.5
    assert schema["properties"]["speed"]["maximum"] == 2.0
    assert schema["properties"]["format"]["enum"] == ["wav", "mp3"]
    assert schema["properties"]["format"]["default"] == "wav"
