"""Cache entry schemas for template manifest caching."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class CacheEntry(BaseModel):
    """Cached template manifest entry.

    Attributes:
        file_hash: SHA-256 hash of template file for cache key
        manifest: Serialized TemplateManifest dictionary
        cached_at: UTC timestamp when entry was cached
        file_path: Original template file path for reference
        file_size: Template file size in bytes for validation
    """

    file_hash: str = Field(..., description="SHA-256 hash of template file")
    manifest: dict[str, Any] = Field(..., description="Serialized TemplateManifest")
    cached_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp when cached",
    )
    file_path: str = Field(..., description="Original template file path")
    file_size: int = Field(..., ge=0, description="Template file size in bytes")


# Made with Bob
