import io
import time
import wave
from datetime import datetime, timezone, timedelta
from pathlib import Path
from app.models.speech import AudioFormat, SynthesisStatus
from app.services.audio_service import AudioService
from app.utils.ids import generate_audio_id

def create_sample_wav_bytes(duration: float = 1.0, sample_rate: int = 22050) -> bytes:
    """Generate valid PCM WAV bytes for testing."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        num_frames = int(duration * sample_rate)
        wf.writeframes(b"\x00\x00" * num_frames)
    return buf.getvalue()

def test_partitioned_dated_directory_structure(client, test_dirs):
    """
    PASS CRITERIA:
    Files are stored in output/YYYY/MM/DD/aud_<id>.wav and output/metadata/aud_<id>.json.
    """
    speak_res = client.post("/api/v1/speak", json={"text": "Testing dated directory partition.", "voice_id": "1"})
    assert speak_res.status_code == 200
    audio_id = speak_res.json()["audio_id"]

    now = datetime.now(timezone.utc)
    expected_rel_dir = Path(now.strftime("%Y")) / now.strftime("%m") / now.strftime("%d")
    expected_audio_file = test_dirs["output"] / expected_rel_dir / f"{audio_id}.wav"
    expected_meta_file = test_dirs["output"] / "metadata" / f"{audio_id}.json"

    assert expected_audio_file.exists(), f"Audio file not found at {expected_audio_file}"
    assert expected_meta_file.exists(), f"Metadata JSON not found at {expected_meta_file}"
    assert expected_audio_file.stat().st_size > 44

def test_audio_metadata_schema_accuracy(client):
    """Verify metadata model fields, types, and persistence integrity."""
    speak_res = client.post("/api/v1/speak", json={"text": "Checking metadata schema accuracy.", "voice_id": "1"})
    assert speak_res.status_code == 200
    audio_id = speak_res.json()["audio_id"]

    meta_res = client.get(f"/api/v1/audio/{audio_id}")
    assert meta_res.status_code == 200
    meta = meta_res.json()

    assert meta["audio_id"] == audio_id
    assert meta["text"] == "Checking metadata schema accuracy."
    assert meta["voice_id"] == "1"
    assert meta["format"] == "wav"
    assert meta["duration_seconds"] > 0
    assert meta["sample_rate"] == 22050
    assert meta["channels"] == 1
    assert meta["status"] == "completed"
    assert "file_path" in meta
    assert meta["file_size_bytes"] > 0

def test_sequential_multi_turn_conversation_replay(client):
    """
    PASS CRITERIA:
    Sequential turns are saved independently and can be sequentially replayed.
    """
    turn_texts = [
        "Turn 1: User asks a question about quantum computing.",
        "Turn 2: Grok responds explaining quantum entanglement.",
        "Turn 3: User follows up asking about qubits.",
        "Turn 4: Grok explains superposition and decoherence."
    ]

    audio_ids = []
    for text in turn_texts:
        res = client.post("/api/v1/speak", json={"text": text, "voice_id": "1"})
        assert res.status_code == 200
        audio_ids.append(res.json()["audio_id"])

    # 1. Verify every turn can be sequentially streamed and replayed
    for audio_id in audio_ids:
        stream_res = client.get(f"/api/v1/audio/{audio_id}/file")
        assert stream_res.status_code == 200
        assert stream_res.headers["content-type"] == "audio/wav"
        assert stream_res.headers["accept-ranges"] == "bytes"
        assert len(stream_res.content) > 100

    # 2. Verify history endpoint returns turns ordered newest-first
    hist_res = client.get("/api/v1/audio?limit=10")
    assert hist_res.status_code == 200
    items = hist_res.json()["items"]
    returned_ids = [item["audio_id"] for item in items]

    # Verify all audio_ids are present in history
    for a_id in audio_ids:
        assert a_id in returned_ids

    # Most recent turn should appear before earlier turns
    assert returned_ids.index(audio_ids[3]) < returned_ids.index(audio_ids[0])

def test_byte_range_audio_streaming(client):
    """Verify HTTP range request support (206 Partial Content) for seekable playback."""
    res = client.post("/api/v1/speak", json={"text": "Byte range audio test content."})
    audio_id = res.json()["audio_id"]

    # Request first 44 bytes (standard RIFF/WAV header)
    headers = {"Range": "bytes=0-43"}
    range_res = client.get(f"/api/v1/audio/{audio_id}/file", headers=headers)

    assert range_res.status_code == 206
    assert len(range_res.content) == 44
    assert range_res.content.startswith(b"RIFF")
    assert "Content-Range" in range_res.headers
    assert range_res.headers["Content-Range"].startswith("bytes 0-43/")

def test_pagination_and_voice_filtering(client):
    """Verify paginated listing and filtering by voice_id."""
    # Generate audio
    client.post("/api/v1/speak", json={"text": "Pagination item 1", "voice_id": "1"})
    client.post("/api/v1/speak", json={"text": "Pagination item 2", "voice_id": "1"})
    client.post("/api/v1/speak", json={"text": "Pagination item 3", "voice_id": "1"})

    # Page 1, limit 2
    res_p1 = client.get("/api/v1/audio?page=1&limit=2")
    assert res_p1.status_code == 200
    data_p1 = res_p1.json()
    assert len(data_p1["items"]) == 2
    assert data_p1["page"] == 1
    assert data_p1["limit"] == 2
    assert data_p1["total"] >= 3

    # Filter by non-existent voice_id
    res_filtered = client.get("/api/v1/audio?voice_id=999")
    assert res_filtered.status_code == 200
    assert len(res_filtered.json()["items"]) == 0

def test_path_traversal_attack_rejection(client):
    """Verify security defenses against directory traversal attempts in audio_id."""
    malicious_ids = [
        "../etc/passwd",
        "..\\windows\\win.ini",
        "aud_../../secret",
        "aud_%2e%2e%2fsecret",
        "../../output/metadata",
    ]
    for bad_id in malicious_ids:
        res_meta = client.get(f"/api/v1/audio/{bad_id}")
        assert res_meta.status_code in [400, 404]

        res_file = client.get(f"/api/v1/audio/{bad_id}/file")
        assert res_file.status_code in [400, 404]

        res_del = client.delete(f"/api/v1/audio/{bad_id}")
        assert res_del.status_code in [400, 404]

def test_retention_cleanup_policy(test_dirs, client):
    """
    PASS CRITERIA:
    Retention cleanup safely deletes expired audio files and companion metadata,
    pruning empty directories without affecting active records.
    """
    audio_svc = AudioService(output_dir=test_dirs["output"])

    # 1. Create an active record (current timestamp)
    active_bytes = create_sample_wav_bytes(1.0)
    active_id = generate_audio_id()
    audio_svc.save_audio(audio_id=active_id, text="Current active record", audio_bytes=active_bytes)

    # 2. Create an expired record (simulated 20 days ago)
    old_bytes = create_sample_wav_bytes(1.0)
    old_id = generate_audio_id()
    audio_svc.save_audio(audio_id=old_id, text="Old record to be purged", audio_bytes=old_bytes)

    # Manually backdate the old record's metadata JSON and audio file
    old_meta_file = test_dirs["output"] / "metadata" / f"{old_id}.json"
    old_meta = audio_svc.get_audio_metadata(old_id)
    old_time = datetime.now(timezone.utc) - timedelta(days=20)
    old_meta.created_at = old_time
    old_meta_file.write_text(old_meta.model_dump_json(indent=2), encoding="utf-8")

    # 3. Trigger cleanup for records older than 10 days
    cleanup_res = client.post("/api/v1/audio/cleanup?days=10")
    assert cleanup_res.status_code == 200
    assert cleanup_res.json()["deleted_count"] >= 1

    # 4. Verify old record is deleted
    assert audio_svc.get_audio_metadata(old_id) is None
    assert audio_svc.get_audio_file_path(old_id) is None

    # 5. Verify active record is still intact and playable
    assert audio_svc.get_audio_metadata(active_id) is not None
    active_file = audio_svc.get_audio_file_path(active_id)
    assert active_file is not None
    assert active_file.exists()

def test_single_audio_record_deletion(client):
    """Verify manual deletion of an individual audio record."""
    speak_res = client.post("/api/v1/speak", json={"text": "Audio record to delete individually."})
    audio_id = speak_res.json()["audio_id"]

    # Delete audio record
    del_res = client.delete(f"/api/v1/audio/{audio_id}")
    assert del_res.status_code == 204

    # Subsequent GET returns 404
    get_res = client.get(f"/api/v1/audio/{audio_id}")
    assert get_res.status_code == 404

    file_res = client.get(f"/api/v1/audio/{audio_id}/file")
    assert file_res.status_code == 404
