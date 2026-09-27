import pytest
from app.services.providers.base import TTSProvider
from app.services.providers.mock import MockTTSProvider
from app.services.providers.cosyvoice import CosyVoiceProvider

def test_cannot_instantiate_base_provider():
    """Verify that TTSProvider cannot be instantiated directly without implementations."""
    with pytest.raises(TypeError) as excinfo:
        TTSProvider()
    assert "Can't instantiate abstract class" in str(excinfo.value)

def test_incomplete_provider_subclass_fails():
    """Verify that a subclass omitting any required abstract method cannot be instantiated."""
    class IncompleteProvider(TTSProvider):
        async def health(self):
            return {"status": "ok"}
        # Omits status, synthesize, register_voice, delete_voice, list_voices

    with pytest.raises(TypeError) as excinfo:
        IncompleteProvider()
    assert "Can't instantiate abstract class" in str(excinfo.value)

def test_mock_provider_is_instance_of_base():
    mock = MockTTSProvider()
    assert isinstance(mock, TTSProvider)

def test_cosyvoice_provider_is_instance_of_base():
    cosy = CosyVoiceProvider(base_url="http://localhost:8080")
    assert isinstance(cosy, TTSProvider)
