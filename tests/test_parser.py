"""Tests for parser.py — script → timestamped segments."""

from parser import parse_script, _to_seconds


def test_parse_hh_mm_ss(tmp_path):
    p = tmp_path / "s.txt"
    p.write_text("00:00:00 alpha\n00:00:02 beta\n")
    segs = parse_script(str(p))
    assert [s["text"] for s in segs] == ["alpha", "beta"]
    assert segs[0]["timestamp_str"] == "00:00:00"
    assert segs[0]["timestamp_seconds"] == 0
    assert segs[1]["timestamp_seconds"] == 2
    assert [s["segment_index"] for s in segs] == [0, 1]


def test_parse_mm_ss(tmp_path):
    p = tmp_path / "s.txt"
    p.write_text("01:30 one and a half minutes\n02:00 two minutes\n")
    segs = parse_script(str(p))
    assert segs[0]["timestamp_seconds"] == 90
    assert segs[1]["timestamp_seconds"] == 120


def test_parse_continuous_no_newlines(tmp_path):
    """Timestamps crammed onto one line still split correctly."""
    p = tmp_path / "s.txt"
    p.write_text("00:00:00 alpha 00:00:02 beta 00:00:04 gamma")
    segs = parse_script(str(p))
    assert [s["text"] for s in segs] == ["alpha", "beta", "gamma"]


def test_parse_no_timestamps_returns_empty(tmp_path):
    p = tmp_path / "s.txt"
    p.write_text("just some words with no timestamps here")
    assert parse_script(str(p)) == []


def test_to_seconds_formats():
    assert _to_seconds("00:00:05") == 5
    assert _to_seconds("00:02:00") == 120
    assert _to_seconds("01:00:00") == 3600
    assert _to_seconds("90") == 90.0
    assert _to_seconds("1:30") == 90
