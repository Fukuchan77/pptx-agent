"""Unit tests for cache schemas."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from pptx_agent.cache.schemas import CacheEntry


def test_cache_entry_creation() -> None:
    """Test creating a valid CacheEntry."""
    entry = CacheEntry(
        file_hash="abc123",
        manifest={"slides": []},
        file_path="/path/to/template.pptx",
        file_size=1024,
    )

    assert entry.file_hash == "abc123"
    assert entry.manifest == {"slides": []}
    assert entry.file_path == "/path/to/template.pptx"
    assert entry.file_size == 1024
    assert isinstance(entry.cached_at, datetime)


def test_cache_entry_cached_at_default() -> None:
    """Test that cached_at defaults to current UTC time."""
    before = datetime.now(UTC)
    entry = CacheEntry(
        file_hash="abc123",
        manifest={"slides": []},
        file_path="/path/to/template.pptx",
        file_size=1024,
    )
    after = datetime.now(UTC)

    assert before <= entry.cached_at <= after
    assert entry.cached_at.tzinfo == UTC


def test_cache_entry_negative_file_size() -> None:
    """Test that negative file_size is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        CacheEntry(
            file_hash="abc123",
            manifest={"slides": []},
            file_path="/path/to/template.pptx",
            file_size=-1,
        )

    errors = exc_info.value.errors()
    assert any(
        error["loc"] == ("file_size",) and "greater than or equal to 0" in error["msg"]
        for error in errors
    )


def test_cache_entry_missing_required_fields() -> None:
    """Test that missing required fields raise ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        CacheEntry(manifest={"slides": []})  # type: ignore[call-arg]

    errors = exc_info.value.errors()
    missing_fields = {error["loc"][0] for error in errors}
    assert "file_hash" in missing_fields
    assert "file_path" in missing_fields
    assert "file_size" in missing_fields


def test_cache_entry_custom_cached_at() -> None:
    """Test creating CacheEntry with custom cached_at timestamp."""
    custom_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    entry = CacheEntry(
        file_hash="abc123",
        manifest={"slides": []},
        file_path="/path/to/template.pptx",
        file_size=1024,
        cached_at=custom_time,
    )

    assert entry.cached_at == custom_time


def test_cache_entry_manifest_any_dict() -> None:
    """Test that manifest accepts any dictionary structure."""
    complex_manifest = {
        "slides": [{"id": 1, "layout": "title"}],
        "metadata": {"version": "1.0", "author": "test"},
        "nested": {"deep": {"structure": True}},
    }

    entry = CacheEntry(
        file_hash="abc123",
        manifest=complex_manifest,
        file_path="/path/to/template.pptx",
        file_size=1024,
    )

    assert entry.manifest == complex_manifest


# Made with Bob
