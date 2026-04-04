"""Sample schema instances for testing.

This module provides reusable schema fixtures for testing validators,
agents, and pipeline components.
"""

from pptx_agent.schemas import (
    ChartBlock,
    ImageBlock,
    PresentationSchema,
    SlideSchema,
    SmartArtBlock,
    TableBlock,
    TextBlock,
)


def create_valid_presentation() -> PresentationSchema:
    """Create a valid presentation schema for testing.

    Returns:
        A complete presentation with multiple slides and varied content.
    """
    return PresentationSchema(
        title="Test Presentation",
        slides=[
            create_valid_slide(),
            create_title_slide(),
            create_chart_slide(),
            create_table_slide(),
        ],
        metadata={"author": "Test Suite", "version": "1.0"},
    )


def create_valid_slide() -> SlideSchema:
    """Create a valid slide schema for testing.

    Returns:
        A basic content slide with text block.
    """
    return SlideSchema(
        layout_name="Title and Content",
        title="Test Slide",
        content=[
            TextBlock(
                placeholder_name="content",
                text="Sample content text for testing purposes.",
                language="en",
            )
        ],
        notes="These are sample speaker notes for the test slide.",
    )


def create_title_slide() -> SlideSchema:
    """Create a title slide schema.

    Returns:
        A title slide with title and subtitle.
    """
    return SlideSchema(
        layout_name="Title Slide",
        title="Presentation Title",
        content=[
            TextBlock(
                placeholder_name="subtitle",
                text="A comprehensive overview of the testing framework",
                language="en",
            )
        ],
        notes=None,
    )


def create_overflow_slide() -> SlideSchema:
    """Create a slide with text overflow for testing capacity warnings.

    Returns:
        A slide with very long text that exceeds typical placeholder capacity.
    """
    long_text = "This is a very long text that exceeds capacity. " * 100
    return SlideSchema(
        layout_name="Title and Content",
        title="Overflow Test",
        content=[
            TextBlock(
                placeholder_name="content",
                text=long_text,
                language="en",
            )
        ],
    )


def create_japanese_slide() -> SlideSchema:
    """Create a slide with Japanese text for language testing.

    Returns:
        A slide with Japanese content using 0.55x capacity multiplier.
    """
    return SlideSchema(
        layout_name="Title and Content",
        title="日本語テストスライド",
        content=[
            TextBlock(
                placeholder_name="content",
                text="これは日本語のテストです。全角文字は半角文字の約1.8倍の幅を持つため、"
                "テキスト容量の計算には0.55倍の係数を適用します。この機能により、"
                "日本語コンテンツでもプレースホルダーに適切に収まることを保証します。",
                language="ja",
            )
        ],
        notes="日本語のスピーカーノート",
    )


def create_chart_slide() -> SlideSchema:
    """Create a slide with a chart for visual asset testing.

    Returns:
        A slide with chart data.
    """
    return SlideSchema(
        layout_name="Title and Content",
        title="Sales Performance Chart",
        content=[
            ChartBlock(
                placeholder_name="content",
                chart_type="bar",
                data={
                    "categories": ["Q1", "Q2", "Q3", "Q4"],
                    "series": [
                        {"name": "Revenue", "values": [100, 150, 175, 200]},
                        {"name": "Profit", "values": [20, 30, 35, 45]},
                    ],
                },
                title="Quarterly Performance",
            )
        ],
    )


def create_table_slide() -> SlideSchema:
    """Create a slide with a table for visual asset testing.

    Returns:
        A slide with table data.
    """
    return SlideSchema(
        layout_name="Title and Content",
        title="Product Comparison Table",
        content=[
            TableBlock(
                placeholder_name="content",
                rows=[
                    ["Product A", "$99", "4.5"],
                    ["Product B", "$149", "4.8"],
                    ["Product C", "$199", "4.9"],
                ],
                headers=["Product", "Price", "Rating"],
            )
        ],
    )


def create_image_slide() -> SlideSchema:
    """Create a slide with an image for visual asset testing.

    Returns:
        A slide with image block.
    """
    return SlideSchema(
        layout_name="Title and Content",
        title="Sample Image",
        content=[
            ImageBlock(
                placeholder_name="content",
                image_path="tests/fixtures/sample_image.png",
                alt_text="Sample image for testing",
            )
        ],
    )


def create_smartart_slide() -> SlideSchema:
    """Create a slide with SmartArt for visual asset testing.

    Returns:
        A slide with SmartArt nodes.
    """
    return SlideSchema(
        layout_name="Title and Content",
        title="Process Flow",
        content=[
            SmartArtBlock(
                placeholder_name="content",
                diagram_type="process",
                nodes=[
                    {"text": "Plan", "level": 0},
                    {"text": "Execute", "level": 0},
                    {"text": "Review", "level": 0},
                    {"text": "Improve", "level": 0},
                ],
            )
        ],
    )


def create_mixed_content_slide() -> SlideSchema:
    """Create a slide with multiple content types.

    Returns:
        A slide with text, image, and other content blocks.
    """
    return SlideSchema(
        layout_name="Two Content",
        title="Mixed Content Example",
        content=[
            TextBlock(
                placeholder_name="left_content",
                text="Key points about the topic:",
                language="en",
            ),
            ImageBlock(
                placeholder_name="right_content",
                image_path="tests/fixtures/diagram.png",
                alt_text="Supporting diagram",
            ),
        ],
    )


def create_minimal_presentation() -> PresentationSchema:
    """Create a minimal valid presentation with one slide.

    Returns:
        Simplest possible valid presentation.
    """
    return PresentationSchema(
        title="Minimal Presentation",
        slides=[
            SlideSchema(
                layout_name="Title Slide",
                title="Hello World",
                content=[],
            )
        ],
    )


def create_multilanguage_presentation() -> PresentationSchema:
    """Create a presentation with mixed Japanese and English content.

    Returns:
        Presentation with both ja and en slides.
    """
    return PresentationSchema(
        title="Multi-Language Presentation / 多言語プレゼンテーション",
        slides=[
            create_title_slide(),
            create_valid_slide(),
            create_japanese_slide(),
        ],
        metadata={"languages": ["en", "ja"]},
    )
