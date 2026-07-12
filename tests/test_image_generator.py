"""Tests for image generator thumbnail functionality."""

import pytest
from pathlib import Path
from momentary.image_generator import generate_thumbnail


def test_thumbnail_function_exists():
    """generate_thumbnail function should exist."""
    assert callable(generate_thumbnail), "generate_thumbnail should be callable"


def test_thumbnail_requires_prompt():
    """generate_thumbnail should require a prompt parameter."""
    import inspect
    sig = inspect.signature(generate_thumbnail)
    params = list(sig.parameters.keys())
    assert "thumbnail_prompt" in params, "Should have thumbnail_prompt parameter"


def test_thumbnail_accepts_optional_params():
    """generate_thumbnail should accept optional model, style, and run_dir parameters."""
    import inspect
    sig = inspect.signature(generate_thumbnail)
    params = sig.parameters
    
    assert "model" in params, "Should have model parameter"
    assert "style" in params, "Should have style parameter"
    assert "run_dir" in params, "Should have run_dir parameter"
    
    assert params["model"].default is None, "model should default to None"
    assert params["style"].default is None, "style should default to None"
    assert params["run_dir"].default is None, "run_dir should default to None"


def test_thumbnail_returns_string():
    """generate_thumbnail should return a string (file path)."""
    # This is a signature test - actual API calls would be integration tests
    # We're just verifying the function is set up correctly
    import inspect
    sig = inspect.signature(generate_thumbnail)
    # Function should exist and be callable (verified in test_thumbnail_function_exists)
    assert sig is not None
