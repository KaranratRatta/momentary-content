"""
parser.py — Stage 1: Parse script with timestamps into structured segments.

Reads a text file with timestamps and extracts each segment.

Supports two formats:
  - Newline-separated (traditional):
        00:00:00 this puppy lost his parents
        00:00:02 found this duck

  - Continuous (no newlines between timestamps):
        00:00:00 this puppy lost his parents 00:00:02 found this duck

Outputs: list of {timestamp_seconds, timestamp_str, text, segment_index}
"""

import re
from pathlib import Path
from typing import List, Dict


def parse_script(
    script_path: str,
    timestamp_pattern: str = r"(\d{1,2}:\d{2}(?::\d{2})?)",
) -> List[Dict]:
    """
    Parse a script file into timestamped segments.

    Works for both newline-separated and continuous formats.
    Finds all timestamps in the text, then extracts the text between them.
    Timestamps are colon-separated: HH:MM:SS or MM:SS.

    Args:
        script_path: Path to the script text file.
        timestamp_pattern: Regex to match timestamps.

    Returns:
        List of dicts: [{timestamp_seconds, timestamp_str, text, segment_index}, ...]
    """
    raw = Path(script_path).read_text(encoding="utf-8").strip()
    pattern = re.compile(timestamp_pattern)

    # Find all timestamp matches with their positions
    matches = list(pattern.finditer(raw))
    if not matches:
        return []

    segments = []
    for i, match in enumerate(matches):
        ts_str = match.group(1)
        start = match.end()

        # Text goes from after this timestamp until the next timestamp
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(raw)

        text = raw[start:end].strip()
        # Clean up any leftover newlines in the text
        text = " ".join(text.split())

        segments.append(
            {
                "timestamp_str": ts_str,
                "timestamp_seconds": _to_seconds(ts_str),
                "text": text,
                "segment_index": len(segments),
            }
        )

    return segments


def _to_seconds(ts: str) -> float:
    """Convert HH:MM:SS or MM:SS to total seconds."""
    parts = [int(p) for p in ts.split(":")]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    elif len(parts) == 2:
        return parts[0] * 60 + parts[1]
    else:
        return float(parts[0])


# ─── CLI usage ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import json, sys

    path = sys.argv[1] if len(sys.argv) > 1 else "scripts/input.txt"
    segments = parse_script(path)
    print(json.dumps(segments, indent=2))