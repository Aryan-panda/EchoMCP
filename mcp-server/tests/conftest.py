import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.dependencies import get_tts_provider, get_audio_service, get_voice_service
from app.services.providers.mock import MockTTSProvider
from app.services.audio_service import AudioService
from app.services.voice_service import VoiceService

@pytest.fixture(scope="session")
def test_dirs(tmp_path_factory):
    base = tmp_path_factory.mktemp("echomcp_test")
    voices_dir = base / "voices"
    output_dir = base / "output"
    
    voices_dir.mkdir(parents=True)
    v1_dir = voices_dir / "1"
    v1_dir.mkdir(parents=True)
    (v1_dir / "reference.wav").write_bytes(b"RIFFdummywavbytes")
    (v1_dir / "metadata.json").write_text('{"voice_id": "1", "name": "Voice 1"}')

    output_dir.mkdir(parents=True)
    (output_dir / "metadata").mkdir(parents=True)

    return {"voices": voices_dir, "output": output_dir}

@pytest.fixture
def mock_tts():
    return MockTTSProvider()

@pytest.fixture
def test_audio_svc(test_dirs):
    return AudioService(output_dir=test_dirs["output"])

@pytest.fixture
def test_voice_svc(test_dirs):
    return VoiceService(voices_dir=test_dirs["voices"])

@pytest.fixture
def client(mock_tts, test_audio_svc, test_voice_svc):
    app.dependency_overrides[get_tts_provider] = lambda: mock_tts
    app.dependency_overrides[get_audio_service] = lambda: test_audio_svc
    app.dependency_overrides[get_voice_service] = lambda: test_voice_svc

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
