"""Unit tests for cache manager with SHA-256 keying."""

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from pptx_agent.cache.manager import CacheManager
from pptx_agent.cache.schemas import CacheEntry


@pytest.fixture
def temp_template(tmp_path: Path) -> Path:
    """Create temporary template file for testing.

    Args:
        tmp_path: pytest temporary directory fixture

    Returns:
        Path to temporary template file
    """
    template = tmp_path / "test_template.pptx"
    template.write_bytes(b"fake pptx content for testing")
    return template


@pytest.fixture
def cache_manager(tmp_path: Path) -> CacheManager:
    """Create cache manager instance for testing.

    Args:
        tmp_path: pytest temporary directory fixture

    Returns:
        CacheManager instance with temporary cache directory
    """
    cache_dir = tmp_path / "cache"
    return CacheManager(cache_dir)


@pytest.fixture
def sample_manifest() -> dict[str, Any]:
    """Create sample manifest for testing.

    Returns:
        Sample manifest dictionary
    """
    return {
        "template_path": "/test/template.pptx",
        "layouts": [
            {
                "name": "Title Slide",
                "placeholders": [{"name": "Title", "type": "TITLE", "max_chars": 100}],
            }
        ],
    }


def test_manager_initialization_with_custom_dir(tmp_path: Path) -> None:
    """Test cache manager initialization with custom directory."""
    cache_dir = tmp_path / "custom_cache"
    manager = CacheManager(cache_dir)

    assert manager.cache_dir == cache_dir
    assert cache_dir.exists()


def test_manager_initialization_with_default_dir() -> None:
    """Test cache manager initialization with default directory."""
    manager = CacheManager()

    # Should resolve to user cache directory or temp fallback
    assert manager.cache_dir.exists()
    assert manager.cache_dir.is_dir()


def test_compute_file_hash(temp_template: Path) -> None:
    """Test SHA-256 hash computation for files."""
    hash1 = CacheManager.compute_file_hash(temp_template)

    # Hash should be consistent
    hash2 = CacheManager.compute_file_hash(temp_template)
    assert hash1 == hash2

    # Hash should be valid SHA-256 (64 hex characters)
    assert len(hash1) == 64
    assert all(c in "0123456789abcdef" for c in hash1)

    # Verify hash is correct
    expected_hash = hashlib.sha256(temp_template.read_bytes()).hexdigest()
    assert hash1 == expected_hash


def test_set_and_get_manifest(
    cache_manager: CacheManager,
    temp_template: Path,
    sample_manifest: dict[str, Any],
) -> None:
    """Test storing and retrieving manifest."""
    # Store manifest
    cache_manager.set_manifest(temp_template, sample_manifest)

    # Retrieve manifest
    retrieved = cache_manager.get_manifest(temp_template)
    assert retrieved is not None
    assert retrieved == sample_manifest


def test_get_manifest_nonexistent_template(
    cache_manager: CacheManager,
    tmp_path: Path,
) -> None:
    """Test retrieving manifest for non-existent template."""
    nonexistent = tmp_path / "nonexistent.pptx"
    result = cache_manager.get_manifest(nonexistent)
    assert result is None


def test_get_manifest_cache_miss(
    cache_manager: CacheManager,
    temp_template: Path,
) -> None:
    """Test retrieving manifest when not cached."""
    result = cache_manager.get_manifest(temp_template)
    assert result is None


def test_cache_invalidation_on_file_change(
    cache_manager: CacheManager,
    temp_template: Path,
    sample_manifest: dict[str, Any],
) -> None:
    """Test cache invalidation when file size changes."""
    # Store manifest
    cache_manager.set_manifest(temp_template, sample_manifest)

    # Verify cached
    assert cache_manager.get_manifest(temp_template) == sample_manifest

    # Modify file (change size)
    temp_template.write_bytes(b"different content with different size")

    # Cache should be invalidated
    result = cache_manager.get_manifest(temp_template)
    assert result is None


def test_invalidate_manifest(
    cache_manager: CacheManager,
    temp_template: Path,
    sample_manifest: dict[str, Any],
) -> None:
    """Test manual cache invalidation."""
    # Store manifest
    cache_manager.set_manifest(temp_template, sample_manifest)
    assert cache_manager.get_manifest(temp_template) is not None

    # Invalidate
    result = cache_manager.invalidate(temp_template)
    assert result is True

    # Should be gone
    assert cache_manager.get_manifest(temp_template) is None


def test_invalidate_nonexistent_template(
    cache_manager: CacheManager,
    tmp_path: Path,
) -> None:
    """Test invalidating non-existent template."""
    nonexistent = tmp_path / "nonexistent.pptx"
    result = cache_manager.invalidate(nonexistent)
    assert result is False


def test_cleanup_stale_entries(
    cache_manager: CacheManager,
    temp_template: Path,
    sample_manifest: dict[str, Any],
) -> None:
    """Test cleanup of stale cache entries."""
    # Store manifest
    cache_manager.set_manifest(temp_template, sample_manifest)

    # Get the cache entry and modify its timestamp
    file_hash = cache_manager.compute_file_hash(temp_template)
    entry = cache_manager.storage.get(file_hash)
    assert entry is not None

    # Make entry old (31 days ago)
    old_entry = CacheEntry(
        file_hash=entry.file_hash,
        manifest=entry.manifest,
        cached_at=datetime.now(UTC) - timedelta(days=31),
        file_path=entry.file_path,
        file_size=entry.file_size,
    )
    cache_manager.storage.set(file_hash, old_entry)

    # Cleanup stale entries (max age 30 days)
    removed = cache_manager.cleanup_stale(max_age_days=30)
    assert removed == 1

    # Entry should be gone
    assert cache_manager.get_manifest(temp_template) is None


def test_cleanup_stale_keeps_recent(
    cache_manager: CacheManager,
    temp_template: Path,
    sample_manifest: dict[str, Any],
) -> None:
    """Test cleanup keeps recent entries."""
    # Store manifest (recent)
    cache_manager.set_manifest(temp_template, sample_manifest)

    # Cleanup stale entries
    removed = cache_manager.cleanup_stale(max_age_days=30)
    assert removed == 0

    # Entry should still exist
    assert cache_manager.get_manifest(temp_template) == sample_manifest


def test_get_statistics(
    cache_manager: CacheManager,
    temp_template: Path,
    sample_manifest: dict[str, Any],
) -> None:
    """Test getting cache statistics."""
    # Initially empty
    stats = cache_manager.get_statistics()
    assert stats["entry_count"] == 0
    assert stats["total_size_bytes"] >= 0

    # Add entry
    cache_manager.set_manifest(temp_template, sample_manifest)

    # Statistics should update
    stats = cache_manager.get_statistics()
    assert stats["entry_count"] == 1
    assert stats["total_size_bytes"] > 0
    assert stats["total_size_mb"] >= 0  # May be 0 for very small entries


def test_clear_all(
    cache_manager: CacheManager,
    temp_template: Path,
    sample_manifest: dict[str, Any],
) -> None:
    """Test clearing all cache entries."""
    # Add entries
    cache_manager.set_manifest(temp_template, sample_manifest)

    # Create another template
    temp_template2 = temp_template.parent / "template2.pptx"
    temp_template2.write_bytes(b"different content")
    cache_manager.set_manifest(temp_template2, sample_manifest)

    # Verify entries exist
    assert cache_manager.get_manifest(temp_template) is not None
    assert cache_manager.get_manifest(temp_template2) is not None

    # Clear all
    count = cache_manager.clear_all()
    assert count == 2

    # All entries should be gone
    assert cache_manager.get_manifest(temp_template) is None
    assert cache_manager.get_manifest(temp_template2) is None


def test_cache_directory_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test fallback to temp directory when user cache unavailable."""

    def mock_user_cache_dir(*args: Any, **kwargs: Any) -> None:
        """Mock user_cache_dir to raise permission error."""
        msg = "No access"
        raise PermissionError(msg)

    # Mock platformdirs to raise error
    monkeypatch.setattr(
        "pptx_agent.cache.manager.user_cache_dir",
        mock_user_cache_dir,
    )

    # Should fall back to temp directory
    manager = CacheManager()
    assert manager.cache_dir.exists()
    assert "pptx-agent-cache" in str(manager.cache_dir)


def test_hash_consistency_across_reads(temp_template: Path) -> None:
    """Test hash remains consistent across multiple reads."""
    hashes = [CacheManager.compute_file_hash(temp_template) for _ in range(5)]

    # All hashes should be identical
    assert len(set(hashes)) == 1


def test_different_files_different_hashes(tmp_path: Path) -> None:
    """Test different files produce different hashes."""
    file1 = tmp_path / "file1.pptx"
    file2 = tmp_path / "file2.pptx"

    file1.write_bytes(b"content 1")
    file2.write_bytes(b"content 2")

    hash1 = CacheManager.compute_file_hash(file1)
    hash2 = CacheManager.compute_file_hash(file2)

    assert hash1 != hash2


# Made with Bob
