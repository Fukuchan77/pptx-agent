"""Unit tests for cache storage with file locking."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from pptx_agent.cache.schemas import CacheEntry
from pptx_agent.cache.storage import CacheStorage


@pytest.fixture
def temp_cache_dir(tmp_path: Path) -> Path:
    """Create temporary cache directory for testing.

    Args:
        tmp_path: pytest temporary directory fixture

    Returns:
        Path to temporary cache directory
    """
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
def cache_storage(temp_cache_dir: Path) -> CacheStorage:
    """Create cache storage instance for testing.

    Args:
        temp_cache_dir: Temporary cache directory

    Returns:
        CacheStorage instance
    """
    return CacheStorage(temp_cache_dir)


@pytest.fixture
def sample_entry() -> CacheEntry:
    """Create sample cache entry for testing.

    Returns:
        Sample CacheEntry
    """
    return CacheEntry(
        file_hash="abc123",
        manifest={"layouts": [], "template_path": "/test/template.pptx"},
        cached_at=datetime.now(UTC),
        file_path="/test/template.pptx",
        file_size=1024,
    )


def test_storage_initialization(temp_cache_dir: Path) -> None:
    """Test cache storage initialization creates directory."""
    storage = CacheStorage(temp_cache_dir)
    assert storage.cache_dir == temp_cache_dir
    assert temp_cache_dir.exists()


def test_storage_creates_missing_directory(tmp_path: Path) -> None:
    """Test cache storage creates directory if it doesn't exist."""
    cache_dir = tmp_path / "new_cache"
    assert not cache_dir.exists()

    storage = CacheStorage(cache_dir)
    assert cache_dir.exists()
    assert storage.cache_dir == cache_dir


def test_set_and_get_entry(
    cache_storage: CacheStorage,
    sample_entry: CacheEntry,
) -> None:
    """Test storing and retrieving cache entry."""
    key = "test_key"

    # Store entry
    cache_storage.set(key, sample_entry)

    # Retrieve entry
    retrieved = cache_storage.get(key)
    assert retrieved is not None
    assert retrieved.file_hash == sample_entry.file_hash
    assert retrieved.manifest == sample_entry.manifest
    assert retrieved.file_path == sample_entry.file_path
    assert retrieved.file_size == sample_entry.file_size


def test_get_nonexistent_entry(cache_storage: CacheStorage) -> None:
    """Test retrieving non-existent entry returns None."""
    result = cache_storage.get("nonexistent_key")
    assert result is None


def test_exists(cache_storage: CacheStorage, sample_entry: CacheEntry) -> None:
    """Test checking if cache entry exists."""
    key = "test_key"

    # Entry doesn't exist initially
    assert not cache_storage.exists(key)

    # Store entry
    cache_storage.set(key, sample_entry)

    # Entry now exists
    assert cache_storage.exists(key)


def test_delete_entry(cache_storage: CacheStorage, sample_entry: CacheEntry) -> None:
    """Test deleting cache entry."""
    key = "test_key"

    # Store entry
    cache_storage.set(key, sample_entry)
    assert cache_storage.exists(key)

    # Delete entry
    result = cache_storage.delete(key)
    assert result is True
    assert not cache_storage.exists(key)


def test_delete_nonexistent_entry(cache_storage: CacheStorage) -> None:
    """Test deleting non-existent entry returns False."""
    result = cache_storage.delete("nonexistent_key")
    assert result is False


def test_list_keys(cache_storage: CacheStorage, sample_entry: CacheEntry) -> None:
    """Test listing all cache keys."""
    # Initially empty
    assert cache_storage.list_keys() == []

    # Add entries
    cache_storage.set("key1", sample_entry)
    cache_storage.set("key2", sample_entry)
    cache_storage.set("key3", sample_entry)

    # List keys
    keys = cache_storage.list_keys()
    assert len(keys) == 3
    assert set(keys) == {"key1", "key2", "key3"}


def test_clear_all(cache_storage: CacheStorage, sample_entry: CacheEntry) -> None:
    """Test clearing all cache entries."""
    # Add entries
    cache_storage.set("key1", sample_entry)
    cache_storage.set("key2", sample_entry)
    cache_storage.set("key3", sample_entry)

    assert len(cache_storage.list_keys()) == 3

    # Clear all
    count = cache_storage.clear()
    assert count == 3
    assert cache_storage.list_keys() == []


def test_get_size(cache_storage: CacheStorage, sample_entry: CacheEntry) -> None:
    """Test getting total cache size."""
    # Initially zero or small
    initial_size = cache_storage.get_size()

    # Add entry
    cache_storage.set("key1", sample_entry)

    # Size should increase
    new_size = cache_storage.get_size()
    assert new_size > initial_size


def test_corrupted_cache_entry(
    cache_storage: CacheStorage,
    temp_cache_dir: Path,
) -> None:
    """Test handling of corrupted cache entry."""
    key = "corrupted_key"
    cache_path = temp_cache_dir / f"{key}.json"

    # Write invalid JSON
    cache_path.write_text("invalid json {{{")

    # Should return None and remove corrupted file
    result = cache_storage.get(key)
    assert result is None
    assert not cache_path.exists()


def test_concurrent_access_with_locking(
    cache_storage: CacheStorage,
    sample_entry: CacheEntry,
) -> None:
    """Test file locking prevents race conditions.

    Note: This is a basic test. Full concurrent testing would require
    multiprocessing or threading, which is beyond unit test scope.
    """
    key = "test_key"

    # Store entry
    cache_storage.set(key, sample_entry)

    # Retrieve entry (should work with locking)
    retrieved = cache_storage.get(key)
    assert retrieved is not None
    assert retrieved.file_hash == sample_entry.file_hash


def test_cache_path_generation(temp_cache_dir: Path) -> None:
    """Test cache file path generation."""
    storage = CacheStorage(temp_cache_dir)

    cache_path = storage._get_cache_path("test_key")  # type: ignore[reportPrivateUsage]
    assert cache_path == temp_cache_dir / "test_key.json"

    lock_path = storage._get_lock_path("test_key")  # type: ignore[reportPrivateUsage]
    assert lock_path == temp_cache_dir / "test_key.lock"


def test_remove_file_safe(temp_cache_dir: Path) -> None:
    """Test safe file removal ignores errors."""
    storage = CacheStorage(temp_cache_dir)

    # Create test file
    test_file = temp_cache_dir / "test.txt"
    test_file.write_text("test")
    assert test_file.exists()

    # Remove file
    storage._remove_file_safe(test_file)  # type: ignore[reportPrivateUsage]
    assert not test_file.exists()

    # Removing non-existent file should not raise error
    storage._remove_file_safe(test_file)  # type: ignore[reportPrivateUsage]


# Made with Bob
