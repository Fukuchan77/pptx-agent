"""Template manifest caching module.

This module provides file-based caching for template manifests to improve
performance when reusing the same templates.
"""

from pptx_agent.cache.manager import CacheManager
from pptx_agent.cache.schemas import CacheEntry
from pptx_agent.cache.storage import CacheStorage

__all__ = ["CacheEntry", "CacheManager", "CacheStorage"]

# Made with Bob
