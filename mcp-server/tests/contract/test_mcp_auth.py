def test_mcp_missing_auth_header(client):
    response = client.post("/mcp", json={"jsonrpc": "2.0", "id": "1", "method": "ping"})
    assert response.status_code == 401
    assert "detail" in response.json()
    assert "Missing Authorization header" in response.json()["detail"]

def test_mcp_invalid_auth_scheme(client):
    headers = {"Authorization": "Basic dXNlcjpwYXNz"}
    response = client.post("/mcp", json={"jsonrpc": "2.0", "id": "1", "method": "ping"}, headers=headers)
    assert response.status_code == 401
    assert "Invalid Bearer token" in response.json()["detail"] or "Authorization" in response.json()["detail"]

def test_mcp_wrong_auth_token(client):
    headers = {"Authorization": "Bearer wrong-token-xyz"}
    response = client.post("/mcp", json={"jsonrpc": "2.0", "id": "1", "method": "ping"}, headers=headers)
    assert response.status_code == 401
    assert "Invalid Bearer token" in response.json()["detail"]

def test_mcp_valid_auth_token(client, auth_headers):
    response = client.post("/mcp", json={"jsonrpc": "2.0", "id": "1", "method": "ping"}, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "1"
    assert data["result"] == {}

def test_mcp_get_probe_auth(client, auth_headers):
    # Missing auth
    unauth_resp = client.get("/mcp")
    assert unauth_resp.status_code == 401

    # Valid auth
    auth_resp = client.get("/mcp", headers=auth_headers)
    assert auth_resp.status_code == 200
    assert auth_resp.json()["status"] == "ready"
    assert auth_resp.json()["transport"] == "streamable-http"
