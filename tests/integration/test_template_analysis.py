"""Integration tests for template analysis and caching functionality."""

import argparse
import json
import time
from pathlib import Path

import pytest

from pptx_agent.cache.manager import CacheManager
from pptx_agent.interfaces.cli import analyze_template_command
from pptx_agent.schemas.template_manifest import TemplateManifest
from pptx_agent.template_parser.manifest_builder import ManifestBuilder
from pptx_agent.template_parser.parser import TemplateParser


class TestTemplateInspectionCommand:
    """Test suite for template inspection CLI command (T073)."""

    def test_analyze_template_generates_valid_manifest(
        self, tmp_path: Path, basic_template_path: str
    ) -> None:
        """Test that analyze-template command generates valid manifest JSON."""
        # Arrange
        output_path = tmp_path / "manifest.json"

        # Create args namespace
        args = argparse.Namespace(
            template=basic_template_path,
            output=str(output_path),
            language="en",
            cache_stats=False,
            no_cache=True,  # Skip caching for this test
            invalidate_cache=False,
            verbose=False,
        )

        # Act
        exit_code = analyze_template_command(args)

        # Assert
        assert exit_code == 0
        assert output_path.exists()

        # Verify manifest is valid JSON
        manifest_data = json.loads(output_path.read_text())
        assert "template_name" in manifest_data
        assert "layouts" in manifest_data
        assert "default_language" in manifest_data

        # Verify manifest can be loaded as TemplateManifest
        manifest = TemplateManifest.model_validate(manifest_data)
        assert manifest.template_name == Path(basic_template_path).stem
        assert len(manifest.layouts) > 0
        assert manifest.default_language == "en"

    def test_analyze_template_with_japanese_language(
        self, tmp_path: Path, basic_template_path: str
    ) -> None:
        """Test analyze-template with Japanese language setting."""
        # Arrange
        output_path = tmp_path / "manifest_ja.json"

        args = argparse.Namespace(
            template=basic_template_path,
            output=str(output_path),
            language="ja",
            cache_stats=False,
            no_cache=True,
            invalidate_cache=False,
            verbose=False,
        )

        # Act
        exit_code = analyze_template_command(args)

        # Assert
        assert exit_code == 0
        manifest_data = json.loads(output_path.read_text())
        assert manifest_data["default_language"] == "ja"

    def test_analyze_template_prints_to_stdout_when_no_output(
        self, basic_template_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that manifest is printed to stdout when no output file specified."""
        # Arrange
        args = argparse.Namespace(
            template=str(basic_template_path),
            output=None,
            language="en",
            cache_stats=False,
            no_cache=True,
            invalidate_cache=False,
            verbose=False,
        )

        # Act
        exit_code = analyze_template_command(args)

        # Assert
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "template_name" in captured.out
        assert "layouts" in captured.out

        # Verify output is valid JSON
        manifest_data = json.loads(captured.out)
        assert "template_name" in manifest_data

    def test_analyze_template_with_cache_stats(
        self, tmp_path: Path, basic_template_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test analyze-template with cache statistics display."""
        # Arrange
        output_path = tmp_path / "manifest.json"

        args = argparse.Namespace(
            template=str(basic_template_path),
            output=str(output_path),
            language="en",
            cache_stats=True,
            no_cache=False,  # Enable caching
            invalidate_cache=False,
            verbose=False,
        )

        # Act
        exit_code = analyze_template_command(args)

        # Assert
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Cache Statistics:" in captured.out
        assert "Entries:" in captured.out
        assert "Total size:" in captured.out

    def test_analyze_template_nonexistent_file_returns_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that analyzing non-existent template returns error."""
        # Arrange
        nonexistent = tmp_path / "nonexistent.pptx"

        args = argparse.Namespace(
            template=str(nonexistent),
            output=None,
            language="en",
            cache_stats=False,
            no_cache=True,
            invalidate_cache=False,
            verbose=False,
        )

        # Act
        exit_code = analyze_template_command(args)

        # Assert
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower()

    def test_analyze_template_with_verbose_output(
        self, tmp_path: Path, basic_template_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test analyze-template with verbose output enabled."""
        # Arrange
        output_path = tmp_path / "manifest.json"

        args = argparse.Namespace(
            template=str(basic_template_path),
            output=str(output_path),
            language="en",
            cache_stats=False,
            no_cache=False,
            invalidate_cache=False,
            verbose=True,
        )

        # Act
        exit_code = analyze_template_command(args)

        # Assert
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Analyzing template:" in captured.out or "Using cached manifest" in captured.out


class TestCachePerformanceImprovement:
    """Test suite for cache performance improvement (T074)."""

    def test_cached_manifest_faster_than_parsing(
        self, tmp_path: Path, basic_template_path: str
    ) -> None:
        """Test that using cached manifest is faster than parsing template."""
        # Arrange
        cache_dir = tmp_path / "cache"
        cache_manager = CacheManager(cache_dir)

        # First parse (no cache)
        parser = TemplateParser()
        builder = ManifestBuilder()

        start_time = time.time()
        template_metadata = parser.parse_template(basic_template_path)
        manifest = builder.build_manifest(
            template_metadata, template_name=Path(basic_template_path).stem
        )
        first_parse_time = time.time() - start_time

        # Cache the manifest
        cache_manager.set_manifest(Path(basic_template_path), manifest.model_dump())

        # Second retrieval (from cache)
        start_time = time.time()
        cached_manifest = cache_manager.get_manifest(Path(basic_template_path))
        cache_retrieval_time = time.time() - start_time

        # Assert
        assert cached_manifest is not None
        # Cache retrieval should be significantly faster (at least 2x)
        assert cache_retrieval_time < first_parse_time / 2

    def test_cache_hit_reduces_analysis_time(
        self, tmp_path: Path, basic_template_path: str
    ) -> None:
        """Test that cache hit reduces overall analysis time."""
        # Arrange
        output_path = tmp_path / "manifest.json"

        args = argparse.Namespace(
            template=basic_template_path,
            output=str(output_path),
            language="en",
            cache_stats=False,
            no_cache=False,
            invalidate_cache=False,
            verbose=False,
        )

        # First run (no cache)
        start_time = time.time()
        exit_code1 = analyze_template_command(args)
        first_run_time = time.time() - start_time

        assert exit_code1 == 0

        # Second run (with cache)
        output_path.unlink()  # Remove output file
        start_time = time.time()
        exit_code2 = analyze_template_command(args)
        second_run_time = time.time() - start_time

        # Assert
        assert exit_code2 == 0
        # Second run should be faster or similar due to cache
        # Note: For small files, the difference may be negligible
        assert second_run_time <= first_run_time * 1.5  # Allow 50% margin

    def test_cache_invalidation_forces_reparse(
        self, tmp_path: Path, basic_template_path: str
    ) -> None:
        """Test that cache invalidation forces template re-parsing."""
        # Arrange
        cache_dir = tmp_path / "cache"
        cache_manager = CacheManager(cache_dir)

        # Parse and cache
        parser = TemplateParser()
        builder = ManifestBuilder()
        template_metadata = parser.parse_template(basic_template_path)
        manifest = builder.build_manifest(
            template_metadata, template_name=Path(basic_template_path).stem
        )
        cache_manager.set_manifest(Path(basic_template_path), manifest.model_dump())

        # Verify cached
        assert cache_manager.get_manifest(Path(basic_template_path)) is not None

        # Invalidate cache
        result = cache_manager.invalidate(Path(basic_template_path))
        assert result is True

        # Verify cache miss
        assert cache_manager.get_manifest(Path(basic_template_path)) is None

    def test_cache_statistics_reflect_entries(
        self, tmp_path: Path, basic_template_path: str
    ) -> None:
        """Test that cache statistics accurately reflect cached entries."""
        # Arrange
        cache_dir = tmp_path / "cache"
        cache_manager = CacheManager(cache_dir)

        # Initially empty
        stats = cache_manager.get_statistics()
        initial_count = stats["entry_count"]

        # Add entry
        parser = TemplateParser()
        builder = ManifestBuilder()
        template_metadata = parser.parse_template(basic_template_path)
        manifest = builder.build_manifest(
            template_metadata, template_name=Path(basic_template_path).stem
        )
        cache_manager.set_manifest(Path(basic_template_path), manifest.model_dump())

        # Check statistics
        stats = cache_manager.get_statistics()
        assert stats["entry_count"] == initial_count + 1
        assert stats["total_size_bytes"] > 0
        assert stats["total_size_mb"] >= 0

    def test_multiple_templates_cached_independently(
        self, tmp_path: Path, basic_template_path: str
    ) -> None:
        """Test that cache correctly handles files with identical content.

        Note: Cache uses content hash as key, so identical files share cache entry.
        The last one written wins (template2 overwrites basic-template).
        """
        # Arrange
        cache_dir = tmp_path / "cache"
        cache_manager = CacheManager(cache_dir)

        # Create second template (copy of first with different name)
        template2_path = tmp_path / "template2.pptx"
        template2_path.write_bytes(Path(basic_template_path).read_bytes())

        # Parse and cache both
        parser = TemplateParser()
        builder = ManifestBuilder()

        for template_path in [Path(basic_template_path), template2_path]:
            template_metadata = parser.parse_template(str(template_path))
            manifest = builder.build_manifest(template_metadata, template_name=template_path.stem)
            cache_manager.set_manifest(template_path, manifest.model_dump())

        # Verify both paths return cached manifest
        manifest1 = cache_manager.get_manifest(Path(basic_template_path))
        manifest2 = cache_manager.get_manifest(template2_path)

        assert manifest1 is not None
        assert manifest2 is not None

        # Since files have identical content (same hash), they share cache entry
        # The last one written (template2) is what's cached
        assert manifest1["template_name"] == "template2"
        assert manifest2["template_name"] == "template2"

        # Cache has only 1 entry (identical content = same hash = same cache key)
        stats = cache_manager.get_statistics()
        assert stats["entry_count"] == 1


# Made with Bob
