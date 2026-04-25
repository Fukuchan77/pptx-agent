"""Cache storage implementation with file locking for concurrent access safety."""

import contextlib
import json
from pathlib import Path

from filelock import FileLock

from pptx_agent.cache.schemas import CacheEntry


class CacheStorage:
    """File-based cache storage with locking for concurrent access.

    Provides thread-safe and process-safe cache operations using file locks.
    Each cache entry is stored as a separate JSON file with a corresponding
    lock file to prevent race conditions.

    Attributes:
        cache_dir: Directory where cache files are stored
    """

    def __init__(self, cache_dir: Path) -> None:
        """Initialize cache storage.

        Args:
            cache_dir: Directory for cache files (created if doesn't exist)
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for a given key.

        Args:
            key: Cache key (typically SHA-256 hash)

        Returns:
            Path to cache file
        """
        return self.cache_dir / f"{key}.json"

    def _get_lock_path(self, key: str) -> Path:
        """Get lock file path for a given key.

        Args:
            key: Cache key

        Returns:
            Path to lock file
        """
        return self.cache_dir / f"{key}.lock"

    def get(self, key: str) -> CacheEntry | None:
        """Retrieve cache entry by key with file locking.

        Args:
            key: Cache key to retrieve

        Returns:
            CacheEntry if found, None otherwise
        """
        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            return None

        lock_path = self._get_lock_path(key)
        lock = FileLock(lock_path, timeout=10)

        try:
            with lock, cache_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                return CacheEntry.model_validate(data)
        except (json.JSONDecodeError, ValueError, OSError):
            # Corrupted cache entry, remove it
            self._remove_file_safe(cache_path)
            return None

    def set(self, key: str, entry: CacheEntry) -> None:
        """Store cache entry with file locking.

        Args:
            key: Cache key to store under
            entry: Cache entry to store
        """
        cache_path = self._get_cache_path(key)
        lock_path = self._get_lock_path(key)
        lock = FileLock(lock_path, timeout=10)

        with lock, cache_path.open("w", encoding="utf-8") as f:
            json.dump(entry.model_dump(mode="json"), f, indent=2)

    def delete(self, key: str) -> bool:
        """Delete cache entry by key with file locking.

        Args:
            key: Cache key to delete

        Returns:
            True if entry was deleted, False if not found
        """
        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            return False

        lock_path = self._get_lock_path(key)
        lock = FileLock(lock_path, timeout=10)

        with lock:
            self._remove_file_safe(cache_path)
            self._remove_file_safe(lock_path)
            return True

    def exists(self, key: str) -> bool:
        """Check if cache entry exists.

        Args:
            key: Cache key to check

        Returns:
            True if entry exists, False otherwise
        """
        return self._get_cache_path(key).exists()

    def list_keys(self) -> list[str]:
        """List all cache keys.

        Returns:
            List of cache keys (file stems without .json extension)
        """
        return [
            path.stem for path in self.cache_dir.glob("*.json") if not path.name.endswith(".lock")
        ]

    def clear(self) -> int:
        """Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        count = 0
        for key in self.list_keys():
            if self.delete(key):
                count += 1
        return count

    def get_size(self) -> int:
        """Get total size of cache directory in bytes.

        Returns:
            Total size in bytes
        """
        return sum(path.stat().st_size for path in self.cache_dir.rglob("*") if path.is_file())

    @staticmethod
    def _remove_file_safe(path: Path) -> None:
        """Safely remove a file, ignoring errors.

        Args:
            path: File path to remove
        """
        with contextlib.suppress(OSError):
            path.unlink(missing_ok=True)


# Made with Bob
