import random
import numpy as np
from PIL import Image
from pathlib import Path
from moviepy import (
    VideoClip,
    AudioFileClip,
    concatenate_videoclips,
    CompositeVideoClip,
)
from momentary.config import (
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    FPS,
    TRANSITION_DURATION,
)


def get_audio_duration(audio_path: str) -> float:
    audio = AudioFileClip(audio_path)
    duration = audio.duration
    audio.close()
    return duration


def apply_motion_effect(image_path: str, duration: float, effect: str = "static") -> VideoClip:
    img = Image.open(image_path)
    img_array = np.array(img)

    if effect == "static":
        def make_frame(t):
            return img_array[:VIDEO_HEIGHT, :VIDEO_WIDTH]
        clip = VideoClip(make_frame, duration=duration).with_fps(FPS)
        return clip

    if effect == "random":
        effects = ["zoom_in", "zoom_out", "pan_left", "pan_right", "pan_up", "pan_down"]
        effect = random.choice(effects)

    zoom_start = 1.15
    zoom_end = 1.0 if effect in ["zoom_in", "pan_left", "pan_right", "pan_up", "pan_down"] else 1.15

    if effect == "zoom_out":
        zoom_start, zoom_end = 1.0, 1.15

    def make_frame(t):
        progress = t / duration
        current_zoom = zoom_start + (zoom_end - zoom_start) * progress
        current_zoom = max(current_zoom, 1.0)

        h, w = img_array.shape[:2]
        new_w = int(w * current_zoom)
        new_h = int(h * current_zoom)

        img_resized = img.resize((new_w, new_h), Image.LANCZOS)
        resized_array = np.array(img_resized)

        rh, rw = resized_array.shape[:2]

        if effect in ["zoom_in", "zoom_out"]:
            cx = rw // 2
            cy = rh // 2
        elif effect == "pan_left":
            cx = int(rw * 0.65)
            cy = rh // 2
        elif effect == "pan_right":
            cx = int(rw * 0.35)
            cy = rh // 2
        elif effect == "pan_up":
            cx = rw // 2
            cy = int(rh * 0.65)
        elif effect == "pan_down":
            cx = rw // 2
            cy = int(rh * 0.35)
        else:
            cx = rw // 2
            cy = rh // 2

        x1 = max(0, cx - VIDEO_WIDTH // 2)
        y1 = max(0, cy - VIDEO_HEIGHT // 2)
        x2 = min(rw, x1 + VIDEO_WIDTH)
        y2 = min(rh, y1 + VIDEO_HEIGHT)

        crop = resized_array[y1:y2, x1:x2]

        if crop.shape[0] < VIDEO_HEIGHT or crop.shape[1] < VIDEO_WIDTH:
            pad_h = max(0, VIDEO_HEIGHT - crop.shape[0])
            pad_w = max(0, VIDEO_WIDTH - crop.shape[1])
            crop = np.pad(
                crop,
                ((0, pad_h), (0, pad_w), (0, 0)),
                mode="edge",
            )

        crop = crop[:VIDEO_HEIGHT, :VIDEO_WIDTH]
        return crop

    clip = VideoClip(make_frame, duration=duration).with_fps(FPS)
    return clip


def add_crossfade(clips: list) -> list:
    return clips


def assemble_video(image_paths: list, audio_paths: list, title: str, motion: str = "static", run_dir: Path | None = None) -> str:
    print("  Assembling video...")

    clips = []
    for i, (img_path, audio_path) in enumerate(zip(image_paths, audio_paths)):
        audio_duration = get_audio_duration(audio_path)

        if motion == "variety":
            effects = ["static", "zoom_in", "zoom_out", "pan_left", "pan_right", "pan_up", "pan_down"]
            scene_effect = effects[i % len(effects)]
        else:
            scene_effect = motion

        print(f"    Scene {i + 1}: {audio_duration:.1f}s audio, effect: {scene_effect}")

        video_clip = apply_motion_effect(img_path, audio_duration, scene_effect)
        audio_clip = AudioFileClip(audio_path)

        video_clip = video_clip.with_audio(audio_clip)
        clips.append(video_clip)

    print("  Adding transitions...")
    clips = add_crossfade(clips)

    print("  Concatenating scenes...")
    final = concatenate_videoclips(clips, method="compose")

    if run_dir:
        output_path = run_dir / "video.mp4"
    else:
        output_path = Path("output") / f"{title}.mp4"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"  Exporting to {output_path}...")
    final.write_videofile(
        str(output_path),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile=str(output_path.parent / "temp-audio.m4a"),
        remove_temp=True,
        preset="medium",
        threads=4,
    )

    final.close()
    for clip in clips:
        clip.close()

    print(f"  Video saved: {output_path}")
    return str(output_path)


def assemble_video_with_boundaries(image_paths: list, full_audio_path: str, boundaries: list, title: str, motion: str = "static", run_dir: Path | None = None) -> str:
    print("  Assembling video with boundaries...")

    total_duration = max(b["end"] for b in boundaries) if boundaries else 0
    print(f"  Total duration: {total_duration:.1f}s")

    clips = []
    for i, (img_path, boundary) in enumerate(zip(image_paths, boundaries)):
        duration = boundary["end"] - boundary["start"]

        if motion == "variety":
            effects = ["static", "zoom_in", "zoom_out", "pan_left", "pan_right", "pan_up", "pan_down"]
            scene_effect = effects[i % len(effects)]
        else:
            scene_effect = motion

        print(f"    Scene {i + 1}: {duration:.1f}s (showing from {boundary['start']:.1f}s to {boundary['end']:.1f}s), effect: {scene_effect}")

        video_clip = apply_motion_effect(img_path, duration, scene_effect)
        video_clip = video_clip.with_start(boundary["start"])
        clips.append(video_clip)

    print("  Compositing scenes into timeline...")
    final_video = CompositeVideoClip(clips, size=(VIDEO_WIDTH, VIDEO_HEIGHT))

    print(f"  Loading full audio: {full_audio_path}")
    full_audio = AudioFileClip(full_audio_path)
    final_video = final_video.with_audio(full_audio)

    if run_dir:
        output_path = run_dir / "video.mp4"
    else:
        output_path = Path("output") / f"{title}.mp4"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"  Exporting to {output_path}...")
    final_video.write_videofile(
        str(output_path),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile=str(output_path.parent / "temp-audio.m4a"),
        remove_temp=True,
        preset="medium",
        threads=4,
    )

    final_video.close()
    for clip in clips:
        clip.close()

    print(f"  Video saved: {output_path}")
    return str(output_path)
