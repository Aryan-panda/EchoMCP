def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_version_endpoint(client):
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "grok-voice-bridge"
    assert data["version"] == "1.0.0"

def test_ready_endpoint(client):
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["mcp"] is True
    assert data["tts"] is True
    assert data["voice_1"] is True
    assert data["audio_store"] is True
    assert data["ready"] is True
