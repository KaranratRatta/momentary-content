"""Tests for video assembly functionality."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from momentary.video_assembler import (
    apply_motion_effect,
    add_crossfade,
    assemble_video,
    assemble_video_with_boundaries,
    get_audio_duration,
)


class TestCrossfade:
    """Test crossfade functionality."""

    def test_add_crossfade_empty_list(self):
        """Test crossfade with empty clip list."""
        result = add_crossfade([])
        assert result == []


class TestAssembleVideoWithBoundaries:
    """Test boundary-based video assembly."""

    def test_creates_clips_with_correct_durations(self, tmp_path):
        """Test that each clip gets the correct duration from boundaries."""
        images_dir = tmp_path / "images"
        images_dir.mkdir()
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()

        for i in range(3):
            (images_dir / f"scene_{i:03d}.png").write_bytes(b"fake")
        (audio_dir / "full_audio.mp3").write_bytes(b"fake")

        boundaries = [
            {"scene_index": 0, "start": 0.0, "end": 3.5},
            {"scene_index": 1, "start": 3.5, "end": 7.2},
            {"scene_index": 2, "start": 7.2, "end": 10.0},
        ]

        image_paths = [str(images_dir / f"scene_{i:03d}.png") for i in range(3)]
        full_audio_path = str(audio_dir / "full_audio.mp3")

        mock_clip = MagicMock()
        mock_clip.with_start.return_value = mock_clip
        mock_clip.with_audio.return_value = mock_clip

        mock_composite = MagicMock()
        mock_composite.with_audio.return_value = mock_composite

        with patch("momentary.video_assembler.apply_motion_effect", return_value=mock_clip) as mock_motion, \
             patch("momentary.video_assembler.AudioFileClip") as mock_audio_cls, \
             patch("momentary.video_assembler.CompositeVideoClip", return_value=mock_composite) as mock_composite_cls:
            result = assemble_video_with_boundaries(
                image_paths, full_audio_path, boundaries, "Test", motion="static", run_dir=tmp_path
            )

        assert mock_motion.call_count == 3
        assert mock_motion.call_args_list[0][0][1] == 3.5
        assert mock_motion.call_args_list[1][0][1] == 3.7
        assert mock_motion.call_args_list[2][0][1] == 2.8

        mock_clip.with_start.assert_any_call(0.0)
        mock_clip.with_start.assert_any_call(3.5)
        mock_clip.with_start.assert_any_call(7.2)

        mock_composite_cls.assert_called_once()
        assert result == str(tmp_path / "video.mp4")

    def test_variety_motion_cycles_effects(self, tmp_path):
        """Test that variety motion cycles through effects."""
        images_dir = tmp_path / "images"
        images_dir.mkdir()
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()

        for i in range(7):
            (images_dir / f"scene_{i:03d}.png").write_bytes(b"fake")
        (audio_dir / "full_audio.mp3").write_bytes(b"fake")

        boundaries = [
            {"scene_index": i, "start": i * 2.0, "end": (i + 1) * 2.0}
            for i in range(7)
        ]

        image_paths = [str(images_dir / f"scene_{i:03d}.png") for i in range(7)]
        full_audio_path = str(audio_dir / "full_audio.mp3")

        mock_clip = MagicMock()
        mock_clip.with_start.return_value = mock_clip

        mock_composite = MagicMock()
        mock_composite.with_audio.return_value = mock_composite

        with patch("momentary.video_assembler.apply_motion_effect", return_value=mock_clip) as mock_motion, \
             patch("momentary.video_assembler.AudioFileClip"), \
             patch("momentary.video_assembler.CompositeVideoClip", return_value=mock_composite):
            assemble_video_with_boundaries(
                image_paths, full_audio_path, boundaries, "Test", motion="variety", run_dir=tmp_path
            )

        effects_used = [call[0][2] for call in mock_motion.call_args_list]
        assert effects_used[0] == "static"
        assert effects_used[1] == "zoom_in"
        assert effects_used[6] == "pan_down"

    def test_output_path_uses_run_dir(self, tmp_path):
        """Test that output is saved to run_dir/video.mp4."""
        images_dir = tmp_path / "images"
        images_dir.mkdir()
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()

        (images_dir / "scene_000.png").write_bytes(b"fake")
        (audio_dir / "full_audio.mp3").write_bytes(b"fake")

        boundaries = [{"scene_index": 0, "start": 0.0, "end": 5.0}]
        image_paths = [str(images_dir / "scene_000.png")]
        full_audio_path = str(audio_dir / "full_audio.mp3")

        mock_clip = MagicMock()
        mock_clip.with_start.return_value = mock_clip
        mock_composite = MagicMock()
        mock_composite.with_audio.return_value = mock_composite

        with patch("momentary.video_assembler.apply_motion_effect", return_value=mock_clip), \
             patch("momentary.video_assembler.AudioFileClip"), \
             patch("momentary.video_assembler.CompositeVideoClip", return_value=mock_composite):
            result = assemble_video_with_boundaries(
                image_paths, full_audio_path, boundaries, "Test", run_dir=tmp_path
            )

        assert result == str(tmp_path / "video.mp4")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
