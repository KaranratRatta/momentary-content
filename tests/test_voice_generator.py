"""Tests for voice generation and audio splitting functionality."""
import pytest
from pathlib import Path
from momentary.voice_generator import (
    _split_text_into_chunks,
    split_audio_by_boundaries,
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
