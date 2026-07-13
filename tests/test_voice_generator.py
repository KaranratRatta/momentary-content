"""Tests for voice generation and audio splitting functionality."""
import pytest
from pathlib import Path
from momentary.voice_generator import (
    _split_text_into_chunks,
    split_audio_by_boundaries,
    _match_scenes_to_timestamps,
    _create_fallback_boundaries,
    regenerate_boundaries,
)


class TestSplitTextIntoChunks:
    """Test the text chunking functionality."""

    def test_empty_text(self):
        """Test chunking empty text."""
        chunks = _split_text_into_chunks("", target_words=175)
        assert chunks == []

    def test_short_text_single_chunk(self):
        """Test text shorter than target words creates single chunk."""
        text = "This is a short sentence."
        chunks = _split_text_into_chunks(text, target_words=175)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_exact_target_words(self):
        """Test text exactly at target word count."""
        words = ["word"] * 175
        text = " ".join(words)
        chunks = _split_text_into_chunks(text, target_words=175)
        assert len(chunks) == 1

    def test_multiple_chunks(self):
        """Test text longer than target creates multiple chunks."""
        # Create text with sentences that total ~350 words
        sentences = ["This is sentence number one.", "This is sentence number two.", "This is sentence number three."]
        text = " ".join(sentences * 40)  # Repeat to get enough words
        chunks = _split_text_into_chunks(text, target_words=50)
        assert len(chunks) >= 2

    def test_sentence_boundary_respected(self):
        """Test that chunks don't split sentences."""
        # Create sentences that would split if not respected
        text = "First sentence. Second sentence. Third sentence."
        chunks = _split_text_into_chunks(text, target_words=2)
        # Should create separate chunks for each sentence
        assert len(chunks) >= 2

    def test_no_empty_chunks(self):
        """Test that no empty chunks are created."""
        text = "Hello world."
        chunks = _split_text_into_chunks(text, target_words=175)
        for chunk in chunks:
            assert chunk.strip() != ""


class TestSplitAudioByBoundaries:
    """Test the audio splitting functionality."""

    def test_empty_boundaries(self, tmp_path):
        """Test splitting with empty boundaries."""
        # This test requires actual audio file, so we'll skip if pydub not available
        pytest.skip("Requires actual MP3 file for testing")

    def test_single_boundary(self, tmp_path):
        """Test splitting with single boundary."""
        # This test requires actual audio file, so we'll skip if pydub not available
        pytest.skip("Requires actual MP3 file for testing")

    def test_boundary_clamping(self, tmp_path):
        """Test that boundaries are clamped to audio length."""
        pytest.skip("Requires actual MP3 file for testing")

    def test_invalid_boundary_times(self, tmp_path):
        """Test handling of invalid boundary times."""
        pytest.skip("Requires actual MP3 file for testing")

    def test_audio_directory_creation(self, tmp_path):
        """Test that audio directory is created if it doesn't exist."""
        pytest.skip("Requires actual MP3 file for testing")


class TestIntegration:
    """Integration tests for the full pipeline."""

    def test_chunking_and_splitting_workflow(self, tmp_path):
        """Test the workflow of chunking text then splitting audio."""
        pytest.skip("Requires actual MP3 file for testing")


class TestBoundaryAdjustment:
    """Test that scene boundaries preserve inter-scene pauses."""

    def test_match_scenes_preserves_pauses(self):
        """Test that _match_scenes_to_timestamps adjusts boundaries to preserve pauses."""
        scenes = [
            {"narration": "First scene."},
            {"narration": "Second scene."},
            {"narration": "Third scene."},
        ]

        full_text = "First scene. Second scene. Third scene."
        chars = list(full_text)
        start_times = [i * 0.1 for i in range(len(chars))]
        end_times = [(i + 1) * 0.1 for i in range(len(chars))]

        boundaries = _match_scenes_to_timestamps(scenes, chars, start_times, end_times)

        assert len(boundaries) == 3

        assert boundaries[0]["start"] == 0.0
        assert boundaries[0]["end"] == boundaries[1]["start"]

        assert boundaries[1]["end"] == boundaries[2]["start"]

        assert boundaries[2]["end"] == (len(chars)) * 0.1

    def test_match_scenes_handles_mismatch(self):
        """Test that _match_scenes_to_timestamps handles character mismatches gracefully."""
        scenes = [
            {"narration": "Hello"},
            {"narration": "World"},
        ]

        chars = list("Hello World")
        start_times = [i * 0.1 for i in range(len(chars))]
        end_times = [(i + 1) * 0.1 for i in range(len(chars))]

        boundaries = _match_scenes_to_timestamps(scenes, chars, start_times, end_times)

        assert len(boundaries) == 2
        assert boundaries[0]["scene_index"] == 0
        assert boundaries[1]["scene_index"] == 1
        assert boundaries[0]["end"] == boundaries[1]["start"]

    def test_match_scenes_handles_short_arrays(self):
        """Test that _match_scenes_to_timestamps doesn't crash with short arrays."""
        scenes = [
            {"narration": "Hello"},
            {"narration": "World"},
        ]

        chars = list("Hello")
        start_times = [0.0, 0.1, 0.2, 0.3, 0.4]
        end_times = [0.1, 0.2, 0.3, 0.4, 0.5]

        boundaries = _match_scenes_to_timestamps(scenes, chars, start_times, end_times)

        assert len(boundaries) == 2
        assert boundaries[0]["scene_index"] == 0
        assert boundaries[1]["scene_index"] == 1

    def test_create_fallback_boundaries(self):
        """Test that _create_fallback_boundaries creates correct structure."""
        boundaries = _create_fallback_boundaries(5)

        assert len(boundaries) == 5
        for i, boundary in enumerate(boundaries):
            assert boundary["scene_index"] == i
            assert boundary["start"] == i * 5.0
            assert boundary["end"] == (i + 1) * 5.0

    def test_single_audio_boundary_adjustment(self, tmp_path, monkeypatch):
        """Test that generate_single_audio adjusts boundaries to preserve pauses."""
        from momentary.voice_generator import generate_single_audio
        from unittest.mock import MagicMock, patch
        import base64

        scenes = [
            {"narration": "First scene."},
            {"narration": "Second scene."},
            {"narration": "Third scene."},
        ]

        full_text = "First scene. Second scene. Third scene."
        chars = list(full_text)
        
        mock_alignment = MagicMock()
        mock_alignment.characters = chars
        mock_alignment.character_start_times_seconds = [i * 0.1 for i in range(len(chars))]
        mock_alignment.character_end_times_seconds = [(i + 1) * 0.1 for i in range(len(chars))]

        mock_result = MagicMock()
        mock_result.audio_base_64 = base64.b64encode(b"fake audio data").decode()
        mock_result.alignment = mock_alignment

        mock_client = MagicMock()
        mock_client.text_to_speech.convert_with_timestamps.return_value = mock_result

        with patch('momentary.voice_generator.ElevenLabs', return_value=mock_client):
            audio_path, data = generate_single_audio(scenes, run_dir=tmp_path)

        boundaries = data["boundaries"]
        assert len(boundaries) == 3

        assert boundaries[0]["start"] == 0.0
        assert boundaries[0]["end"] == boundaries[1]["start"]

        assert boundaries[1]["end"] == boundaries[2]["start"]

        assert boundaries[2]["end"] == (len(chars)) * 0.1

    def test_chunked_audio_boundary_adjustment(self, tmp_path, monkeypatch):
        """Test that generate_chunked_audio adjusts boundaries to preserve pauses."""
        from momentary.voice_generator import generate_chunked_audio
        from unittest.mock import MagicMock, patch
        import base64

        scenes = [
            {"narration": "First scene."},
            {"narration": "Second scene."},
            {"narration": "Third scene."},
        ]

        full_text = "First scene. Second scene. Third scene."
        chars = list(full_text)
        
        mock_alignment = MagicMock()
        mock_alignment.characters = chars
        mock_alignment.character_start_times_seconds = [i * 0.1 for i in range(len(chars))]
        mock_alignment.character_end_times_seconds = [(i + 1) * 0.1 for i in range(len(chars))]

        mock_result = MagicMock()
        mock_result.audio_base_64 = base64.b64encode(b"fake audio data").decode()
        mock_result.alignment = mock_alignment

        mock_client = MagicMock()
        mock_client.text_to_speech.convert_with_timestamps.return_value = mock_result

        with patch('momentary.voice_generator.ElevenLabs', return_value=mock_client):
            with patch('pydub.AudioSegment') as mock_audio:
                mock_audio.empty.return_value = MagicMock()
                mock_audio.from_file.return_value = MagicMock()
                audio_path, data = generate_chunked_audio(scenes, run_dir=tmp_path)

        boundaries = data["boundaries"]
        assert len(boundaries) == 3

        assert boundaries[0]["start"] == 0.0
        assert boundaries[0]["end"] == boundaries[1]["start"]

        assert boundaries[1]["end"] == boundaries[2]["start"]

        assert boundaries[2]["end"] == (len(chars)) * 0.1


class TestRegenerateBoundaries:
    """Test the regenerate_boundaries function."""

    def test_regenerate_boundaries_missing_script(self, tmp_path):
        """Test that regenerate_boundaries raises error when script.json is missing."""
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        (audio_dir / "full_audio.mp3").write_bytes(b"fake audio")
        
        with pytest.raises(FileNotFoundError, match="No script.json found"):
            regenerate_boundaries(tmp_path)

    def test_regenerate_boundaries_missing_audio(self, tmp_path):
        """Test that regenerate_boundaries raises error when full_audio.mp3 is missing."""
        import json
        script = {"scenes": [{"narration": "Test"}]}
        (tmp_path / "script.json").write_text(json.dumps(script))
        
        with pytest.raises(FileNotFoundError, match="No full_audio.mp3 found"):
            regenerate_boundaries(tmp_path)

    def test_regenerate_boundaries_empty_scenes(self, tmp_path):
        """Test that regenerate_boundaries raises error when scenes are empty."""
        import json
        script = {"scenes": []}
        (tmp_path / "script.json").write_text(json.dumps(script))
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        (audio_dir / "full_audio.mp3").write_bytes(b"fake audio")
        
        with pytest.raises(ValueError, match="No scenes found"):
            regenerate_boundaries(tmp_path)

    def test_regenerate_boundaries_success(self, tmp_path, monkeypatch):
        """Test successful boundary regeneration."""
        import json
        from unittest.mock import MagicMock, patch
        import base64
        
        scenes = [
            {"narration": "First scene."},
            {"narration": "Second scene."},
        ]
        script = {"scenes": scenes}
        (tmp_path / "script.json").write_text(json.dumps(script))
        
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        (audio_dir / "full_audio.mp3").write_bytes(b"fake audio")
        
        full_text = "First scene. Second scene."
        chars = list(full_text)
        
        mock_alignment = MagicMock()
        mock_alignment.characters = chars
        mock_alignment.character_start_times_seconds = [i * 0.1 for i in range(len(chars))]
        mock_alignment.character_end_times_seconds = [(i + 1) * 0.1 for i in range(len(chars))]
        
        mock_result = MagicMock()
        mock_result.alignment = mock_alignment
        
        mock_client = MagicMock()
        mock_client.text_to_speech.convert_with_timestamps.return_value = mock_result
        
        with patch('momentary.voice_generator.ElevenLabs', return_value=mock_client):
            audio_path, data = regenerate_boundaries(tmp_path)
        
        assert "boundaries" in data
        boundaries = data["boundaries"]
        assert len(boundaries) == 2
        
        boundaries_path = tmp_path / "audio" / "boundaries.json"
        assert boundaries_path.exists()
        
        with open(boundaries_path) as f:
            saved_boundaries = json.load(f)
        assert len(saved_boundaries) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
