"""Tests for video assembly functionality."""
import pytest
from pathlib import Path
from momentary.video_assembler import (
    apply_motion_effect,
    add_crossfade,
    assemble_video,
    get_audio_duration,
)


class TestCrossfade:
    """Test crossfade functionality."""

    def test_add_crossfade_empty_list(self):
        """Test crossfade with empty clip list."""
        result = add_crossfade([])
        assert result == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
