from app.utils.ids import generate_request_id, generate_audio_id, is_valid_audio_id

def test_generate_request_id():
    req_id = generate_request_id()
    assert req_id.startswith("req_")
    assert len(req_id) > 10

def test_generate_audio_id():
    aud_id = generate_audio_id()
    assert aud_id.startswith("aud_")
    assert is_valid_audio_id(aud_id) is True

def test_audio_id_security_path_traversal():
    assert is_valid_audio_id("../aud_123") is False
    assert is_valid_audio_id("aud_123/../../etc") is False
    assert is_valid_audio_id("aud_123;rm -rf") is False
    assert is_valid_audio_id("aud_valid_123") is True
