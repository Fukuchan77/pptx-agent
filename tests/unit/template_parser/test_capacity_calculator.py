"""Unit tests for template parser capacity calculator.

Tests for capacity calculation logic that determines effective text capacity
for template placeholders based on language ratios.
"""

from pptx_agent.schemas.template_manifest import LayoutInfo, PlaceholderInfo, TemplateManifest
from pptx_agent.template_parser.capacity_calculator import (
    calculate_effective_capacity,
    calculate_layout_capacities,
    calculate_manifest_capacities,
)


class TestCalculateEffectiveCapacity:
    """Tests for calculate_effective_capacity function."""

    def test_english_capacity_no_adjustment(self):
        """Test English capacity is not adjusted (1.0x ratio)."""
        capacity = calculate_effective_capacity(max_chars=1000, language="en")
        assert capacity == 1000

    def test_japanese_capacity_adjusted(self):
        """Test Japanese capacity is adjusted (0.55x ratio)."""
        capacity = calculate_effective_capacity(max_chars=1000, language="ja")
        assert capacity == 550  # 1000 * 0.55

    def test_japanese_capacity_rounded_down(self):
        """Test Japanese capacity is rounded down to integer."""
        capacity = calculate_effective_capacity(max_chars=100, language="ja")
        assert capacity == 55  # int(100 * 0.55)

    def test_small_capacity(self):
        """Test calculation with small capacity values."""
        capacity_en = calculate_effective_capacity(max_chars=10, language="en")
        capacity_ja = calculate_effective_capacity(max_chars=10, language="ja")
        assert capacity_en == 10
        assert capacity_ja == 5  # int(10 * 0.55)

    def test_large_capacity(self):
        """Test calculation with large capacity values."""
        capacity_en = calculate_effective_capacity(max_chars=10000, language="en")
        capacity_ja = calculate_effective_capacity(max_chars=10000, language="ja")
        assert capacity_en == 10000
        assert capacity_ja == 5500  # int(10000 * 0.55)


class TestCalculateLayoutCapacities:
    """Tests for calculate_layout_capacities function."""

    def test_single_placeholder_english(self):
        """Test capacity calculation for single placeholder layout in English."""
        layout = LayoutInfo(
            name="Title Slide",
            placeholders=[
                PlaceholderInfo(name="Title", type="TITLE", max_chars=100),
            ],
        )
        capacities = calculate_layout_capacities(layout, language="en")
        assert len(capacities) == 1
        assert capacities["Title"] == 100

    def test_single_placeholder_japanese(self):
        """Test capacity calculation for single placeholder layout in Japanese."""
        layout = LayoutInfo(
            name="Title Slide",
            placeholders=[
                PlaceholderInfo(name="Title", type="TITLE", max_chars=100),
            ],
        )
        capacities = calculate_layout_capacities(layout, language="ja")
        assert len(capacities) == 1
        assert capacities["Title"] == 55  # int(100 * 0.55)

    def test_multiple_placeholders(self):
        """Test capacity calculation for layout with multiple placeholders."""
        layout = LayoutInfo(
            name="Content Slide",
            placeholders=[
                PlaceholderInfo(name="Title", type="TITLE", max_chars=80),
                PlaceholderInfo(name="Content", type="TEXT", max_chars=500),
                PlaceholderInfo(name="Footer", type="TEXT", max_chars=50),
            ],
        )
        capacities_en = calculate_layout_capacities(layout, language="en")
        capacities_ja = calculate_layout_capacities(layout, language="ja")

        # English
        assert capacities_en["Title"] == 80
        assert capacities_en["Content"] == 500
        assert capacities_en["Footer"] == 50

        # Japanese
        assert capacities_ja["Title"] == 44  # int(80 * 0.55)
        assert capacities_ja["Content"] == 275  # int(500 * 0.55)
        assert capacities_ja["Footer"] == 27  # int(50 * 0.55)


class TestCalculateManifestCapacities:
    """Tests for calculate_manifest_capacities function."""

    def test_single_layout_english(self):
        """Test capacity calculation for manifest with single layout in English."""
        manifest = TemplateManifest(
            template_name="Basic Template",
            layouts=[
                LayoutInfo(
                    name="Title Slide",
                    placeholders=[
                        PlaceholderInfo(name="Title", type="TITLE", max_chars=100),
                    ],
                ),
            ],
        )
        capacities = calculate_manifest_capacities(manifest, language="en")
        assert len(capacities) == 1
        assert "Title Slide" in capacities
        assert capacities["Title Slide"]["Title"] == 100

    def test_multiple_layouts(self):
        """Test capacity calculation for manifest with multiple layouts."""
        manifest = TemplateManifest(
            template_name="Multi-Layout Template",
            layouts=[
                LayoutInfo(
                    name="Title Slide",
                    placeholders=[
                        PlaceholderInfo(name="Title", type="TITLE", max_chars=100),
                        PlaceholderInfo(name="Subtitle", type="TEXT", max_chars=150),
                    ],
                ),
                LayoutInfo(
                    name="Content Slide",
                    placeholders=[
                        PlaceholderInfo(name="Title", type="TITLE", max_chars=80),
                        PlaceholderInfo(name="Content", type="TEXT", max_chars=500),
                    ],
                ),
            ],
        )
        capacities_ja = calculate_manifest_capacities(manifest, language="ja")

        assert len(capacities_ja) == 2
        assert "Title Slide" in capacities_ja
        assert "Content Slide" in capacities_ja

        # Title Slide
        assert capacities_ja["Title Slide"]["Title"] == 55  # int(100 * 0.55)
        assert capacities_ja["Title Slide"]["Subtitle"] == 82  # int(150 * 0.55)

        # Content Slide
        assert capacities_ja["Content Slide"]["Title"] == 44  # int(80 * 0.55)
        assert capacities_ja["Content Slide"]["Content"] == 275  # int(500 * 0.55)

    def test_uses_default_language_from_manifest(self):
        """Test that manifest's default language is used when language not specified."""
        manifest = TemplateManifest(
            template_name="Japanese Template",
            layouts=[
                LayoutInfo(
                    name="Title Slide",
                    placeholders=[
                        PlaceholderInfo(name="Title", type="TITLE", max_chars=100),
                    ],
                ),
            ],
            default_language="ja",
        )
        # When language is not specified, should use manifest's default_language
        capacities = calculate_manifest_capacities(manifest)
        assert capacities["Title Slide"]["Title"] == 55  # int(100 * 0.55) for Japanese
