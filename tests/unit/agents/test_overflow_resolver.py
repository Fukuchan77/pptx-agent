"""Unit tests for overflow resolver agent.

Tests the staged overflow resolution strategies:
1. Font reduction
2. Layout change
3. Slide split
4. Content summarization
5. Forced truncation (last resort)
"""

import pytest

from pptx_agent.agents.overflow_resolver import (
    OverflowStrategy,
    resolve_overflow,
)
from pptx_agent.schemas.outline import SlideContent
from pptx_agent.schemas.template_manifest import LayoutInfo, PlaceholderInfo, TemplateManifest


@pytest.fixture
def sample_manifest() -> TemplateManifest:
    """Create a sample template manifest for testing."""
    return TemplateManifest(
        template_name="test-template",
        layouts=[
            LayoutInfo(
                name="Title and Content",
                placeholders=[
                    PlaceholderInfo(name="Title", type="TITLE", max_chars=60),
                    PlaceholderInfo(name="Content", type="BODY", max_chars=500),
                ],
            ),
            LayoutInfo(
                name="Two Content",
                placeholders=[
                    PlaceholderInfo(name="Title", type="TITLE", max_chars=60),
                    PlaceholderInfo(name="Content", type="BODY", max_chars=800),
                ],
            ),
        ],
        default_language="en",
    )


@pytest.fixture
def overflowing_slide() -> SlideContent:
    """Create a slide with content that exceeds placeholder capacity."""
    # Create content that is 600 characters (exceeds 500 char capacity)
    long_content = "A" * 600
    return SlideContent(
        slide_number=1,
        layout_name="Title and Content",
        title="Test Slide",
        content=long_content,
    )


@pytest.fixture
def fitting_slide() -> SlideContent:
    """Create a slide with content that fits within placeholder capacity."""
    return SlideContent(
        slide_number=1,
        layout_name="Title and Content",
        title="Test Slide",
        content="Short content that fits",
    )


class TestOverflowDetection:
    """Tests for overflow detection logic."""

    def test_detects_no_overflow_for_fitting_content(
        self, fitting_slide: SlideContent, sample_manifest: TemplateManifest
    ) -> None:
        """Test that resolve_overflow returns NO_ACTION when content fits."""
        resolution = resolve_overflow(fitting_slide, sample_manifest)

        assert resolution.strategy == OverflowStrategy.NO_ACTION
        assert resolution.overflow_detected is False

    def test_detects_overflow_for_long_content(
        self, overflowing_slide: SlideContent, sample_manifest: TemplateManifest
    ) -> None:
        """Test that resolve_overflow detects overflow correctly."""
        resolution = resolve_overflow(overflowing_slide, sample_manifest)

        assert resolution.overflow_detected is True
        assert resolution.strategy != OverflowStrategy.NO_ACTION


class TestFontReductionStrategy:
    """Tests for font reduction strategy (first attempt)."""

    def test_suggests_font_reduction_for_minor_overflow(
        self, sample_manifest: TemplateManifest
    ) -> None:
        """Test that font reduction is suggested for 10-20% overflow."""
        # Create content that is 550 chars (10% over 500 char limit)
        slide = SlideContent(
            slide_number=1,
            layout_name="Title and Content",
            title="Test",
            content="A" * 550,
        )

        resolution = resolve_overflow(slide, sample_manifest)

        assert resolution.strategy == OverflowStrategy.FONT_REDUCTION
        assert resolution.overflow_percentage > 0
        assert resolution.overflow_percentage <= 20


class TestLayoutChangeStrategy:
    """Tests for layout change strategy (second attempt)."""

    def test_suggests_layout_change_for_moderate_overflow(
        self, sample_manifest: TemplateManifest
    ) -> None:
        """Test that layout change is suggested for 20-50% overflow."""
        # Create content that is 650 chars (30% over 500 char limit)
        slide = SlideContent(
            slide_number=1,
            layout_name="Title and Content",
            title="Test",
            content="A" * 650,
        )

        resolution = resolve_overflow(slide, sample_manifest)

        assert resolution.strategy == OverflowStrategy.LAYOUT_CHANGE
        assert resolution.suggested_layout == "Two Content"
        assert resolution.overflow_percentage > 20


class TestSlideSplitStrategy:
    """Tests for slide split strategy (third attempt)."""

    def test_suggests_slide_split_for_large_overflow(
        self, sample_manifest: TemplateManifest
    ) -> None:
        """Test that slide split is suggested for 50-100% overflow."""
        # Create content that is 900 chars (80% over 500 char limit)
        slide = SlideContent(
            slide_number=1,
            layout_name="Title and Content",
            title="Test",
            content="A" * 900,
        )

        resolution = resolve_overflow(slide, sample_manifest)

        assert resolution.strategy == OverflowStrategy.SLIDE_SPLIT
        assert resolution.split_point is not None


class TestSummarizationStrategy:
    """Tests for content summarization strategy (fourth attempt)."""

    def test_suggests_summarization_for_extreme_overflow(
        self, sample_manifest: TemplateManifest
    ) -> None:
        """Test that summarization is suggested for >100% overflow."""
        # Create content that is 1200 chars (140% over 500 char limit)
        slide = SlideContent(
            slide_number=1,
            layout_name="Title and Content",
            title="Test",
            content="A" * 1200,
        )

        resolution = resolve_overflow(slide, sample_manifest)

        assert resolution.strategy == OverflowStrategy.SUMMARIZE
        assert resolution.target_length is not None


class TestForcedTruncationStrategy:
    """Tests for forced truncation strategy (last resort)."""

    def test_uses_truncation_when_no_alternative_layouts(self) -> None:
        """Test that truncation is used when no larger layouts are available."""
        # Manifest with only one layout
        manifest = TemplateManifest(
            template_name="single-layout",
            layouts=[
                LayoutInfo(
                    name="Title and Content",
                    placeholders=[
                        PlaceholderInfo(name="Title", type="TITLE", max_chars=60),
                        PlaceholderInfo(name="Content", type="BODY", max_chars=500),
                    ],
                ),
            ],
            default_language="en",
        )

        # Create content that exceeds capacity
        slide = SlideContent(
            slide_number=1,
            layout_name="Title and Content",
            title="Test",
            content="A" * 650,
        )

        resolution = resolve_overflow(slide, manifest)

        # Should fallback to more aggressive strategy
        assert resolution.strategy in [
            OverflowStrategy.SLIDE_SPLIT,
            OverflowStrategy.SUMMARIZE,
            OverflowStrategy.FORCED_TRUNCATION,
        ]


class TestLanguageAwareOverflow:
    """Tests for language-aware overflow detection."""

    def test_japanese_overflow_uses_language_ratio(self) -> None:
        """Test that Japanese content uses 0.55x capacity ratio."""
        manifest = TemplateManifest(
            template_name="japanese-template",
            layouts=[
                LayoutInfo(
                    name="Title and Content",
                    placeholders=[
                        PlaceholderInfo(
                            name="Title",
                            type="TITLE",
                            max_chars=60,
                            language_ratio=0.55,
                        ),
                        PlaceholderInfo(
                            name="Content",
                            type="BODY",
                            max_chars=500,
                            language_ratio=0.55,
                        ),
                    ],
                ),
            ],
            default_language="ja",
        )

        # Content at 300 chars (fits in English 500 char capacity)
        # But with 0.55x ratio, effective capacity is 275 chars - overflow!
        slide = SlideContent(
            slide_number=1,
            layout_name="Title and Content",
            title="テスト",
            content="あ" * 300,
        )

        resolution = resolve_overflow(slide, manifest, language="ja")

        assert resolution.overflow_detected is True
