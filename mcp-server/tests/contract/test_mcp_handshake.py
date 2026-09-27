def test_mcp_initialize_handshake(client, auth_headers):
    payload = {
        "jsonrpc": "2.0",
        "id": "init_1",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "grok-consumer-client",
                "version": "1.0.0"
            }
        }
    }
    response = client.post("/mcp", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "init_1"
    assert "result" in data
    result = data["result"]
    assert result["protocolVersion"] == "2024-11-05"
    assert "tools" in result["capabilities"]
    assert result["serverInfo"]["name"] == "grok-voice-bridge"
    assert result["serverInfo"]["version"] == "1.0.0"

def test_mcp_notifications_initialized(client, auth_headers):
    payload = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {}
    }
    response = client.post("/mcp", json=payload, headers=auth_headers)
    assert response.status_code == 204

def test_mcp_ping(client, auth_headers):
    payload = {
        "jsonrpc": "2.0",
        "id": "ping_99",
        "method": "ping"
    }
    response = client.post("/mcp", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "ping_99"
    assert data["result"] == {}
