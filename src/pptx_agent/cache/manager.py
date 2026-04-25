"""Cache manager for template manifest caching with SHA-256 keying."""

import hashlib
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from platformdirs import user_cache_dir

from pptx_agent.cache.schemas import CacheEntry
from pptx_agent.cache.storage import CacheStorage


class CacheManager:
    """Manages template manifest caching with SHA-256 hash-based keys.

    Provides high-level cache operations with automatic key generation,
    cache directory resolution, and cleanup utilities. Uses platformdirs
    for OS-appropriate cache directory with fallback to temp directory.

    Attributes:
        storage: Underlying cache storage implementation
        cache_dir: Resolved cache directory path
    """

    def __init__(self, cache_dir: Path | None = None) -> None:
        """Initialize cache manager.

        Args:
            cache_dir: Optional custom cache directory. If None, uses
                      OS-appropriate user cache directory with fallback
                      to system temp directory.
        """
        if cache_dir is None:
            cache_dir = self._resolve_cache_dir()

        self.cache_dir = cache_dir
        self.storage = CacheStorage(cache_dir)

    @staticmethod
    def _resolve_cache_dir() -> Path:
        """Resolve cache directory using platformdirs with fallback.

        Returns:
            Resolved cache directory path

        Note:
            Tries user cache directory first (~/.cache/pptx-agent on Linux/Mac,
            %LOCALAPPDATA%\\pptx-agent on Windows), falls back to temp directory
            if user cache is unavailable (e.g., in containers).
        """
        try:
            # Try user cache directory
            cache_dir = Path(user_cache_dir("pptx-agent", "pptx-agent"))
            cache_dir.mkdir(parents=True, exist_ok=True)
            # Test write access
            test_file = cache_dir / ".write_test"
            test_file.touch()
            test_file.unlink()
        except (OSError, PermissionError):
            # Fallback to temp directory
            temp_dir = Path(tempfile.gettempdir()) / "pptx-agent-cache"
            temp_dir.mkdir(parents=True, exist_ok=True)
            return temp_dir
        else:
            return cache_dir

    @staticmethod
    def compute_file_hash(file_path: Path) -> str:
        """Compute SHA-256 hash of file for cache key.

        Args:
            file_path: Path to file to hash

        Returns:
            Hexadecimal SHA-256 hash string

        Raises:
            OSError: If file cannot be read
        """
        sha256 = hashlib.sha256()
        with file_path.open("rb") as f:
            # Read in chunks for memory efficiency with large files
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def get_manifest(self, template_path: Path) -> dict[str, Any] | None:
        """Retrieve cached manifest for template file.

        Args:
            template_path: Path to template file

        Returns:
            Cached manifest dictionary if found and valid, None otherwise
        """
        if not template_path.exists():
            return None

        file_hash = self.compute_file_hash(template_path)
        entry = self.storage.get(file_hash)

        if entry is None:
            return None

        # Validate cache entry matches current file
        if entry.file_size != template_path.stat().st_size:
            # File size changed, invalidate cache
            self.storage.delete(file_hash)
            return None

        return entry.manifest

    def set_manifest(
        self,
        template_path: Path,
        manifest: dict[str, Any],
    ) -> None:
        """Cache manifest for template file.

        Args:
            template_path: Path to template file
            manifest: Manifest dictionary to cache
        """
        file_hash = self.compute_file_hash(template_path)
        file_size = template_path.stat().st_size

        entry = CacheEntry(
            file_hash=file_hash,
            manifest=manifest,
            cached_at=datetime.now(UTC),
            file_path=str(template_path),
            file_size=file_size,
        )

        self.storage.set(file_hash, entry)

    def invalidate(self, template_path: Path) -> bool:
        """Invalidate cached manifest for template file.

        Args:
            template_path: Path to template file

        Returns:
            True if cache entry was deleted, False if not found
        """
        if not template_path.exists():
            return False

        file_hash = self.compute_file_hash(template_path)
        return self.storage.delete(file_hash)

    def cleanup_stale(self, max_age_days: int = 30) -> int:
        """Remove cache entries older than specified age.

        Args:
            max_age_days: Maximum age in days (default: 30)

        Returns:
            Number of entries removed
        """
        cutoff = datetime.now(UTC) - timedelta(days=max_age_days)
        removed = 0

        for key in self.storage.list_keys():
            entry = self.storage.get(key)
            if entry and entry.cached_at < cutoff:
                self.storage.delete(key)
                removed += 1

        return removed

    def get_statistics(self) -> dict[str, int | float]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics:
            - entry_count: Number of cached entries
            - total_size_bytes: Total cache size in bytes
            - total_size_mb: Total cache size in megabytes
        """
        entry_count = len(self.storage.list_keys())
        total_size = self.storage.get_size()

        return {
            "entry_count": entry_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        }

    def clear_all(self) -> int:
        """Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        return self.storage.clear()


# Made with Bob
