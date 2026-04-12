"""Unit tests for Pydantic schemas.

TDD RED PHASE: These tests are written BEFORE implementation.
They define the expected behavior of our schema classes.
"""

import pytest
from pydantic import ValidationError

from pptx_agent.schemas.presentation import PresentationSchema
from pptx_agent.schemas.slide import SlideSchema
from pptx_agent.schemas.text import TextBlock, TextCapacity
from pptx_agent.schemas.visual_assets import ChartBlock, ImageBlock, SmartArtBlock, TableBlock


class TestPresentationSchema:
    """Test PresentationSchema validation."""

    def test_valid_presentation_schema(self):
        """RED: Test valid presentation schema creation."""
        schema = PresentationSchema(
            title="Test Presentation",
            slides=[
                SlideSchema(
                    layout_name="Title Slide",
                    title="Slide 1",
                    content=[],
                    notes=None,
                )
            ],
            metadata={"author": "Test User"},
        )

        assert schema.title == "Test Presentation"
        assert len(schema.slides) == 1
        assert schema.metadata["author"] == "Test User"

    def test_presentation_requires_title(self):
        """RED: Test that presentation requires non-empty title."""
        with pytest.raises(ValidationError) as exc_info:
            PresentationSchema(
                title="",
                slides=[],
                metadata={},
            )

        assert "title" in str(exc_info.value).lower()

    def test_presentation_requires_at_least_one_slide(self):
        """RED: Test that presentation requires at least one slide."""
        with pytest.raises(ValidationError) as exc_info:
            PresentationSchema(
                title="Test",
                slides=[],
                metadata={},
            )

        assert "slides" in str(exc_info.value).lower()

    def test_presentation_with_multiple_slides(self):
        """RED: Test presentation with multiple slides."""
        schema = PresentationSchema(
            title="Multi-slide Presentation",
            slides=[
                SlideSchema(layout_name="Title Slide", title="Slide 1", content=[]),
                SlideSchema(layout_name="Content", title="Slide 2", content=[]),
                SlideSchema(layout_name="Content", title="Slide 3", content=[]),
            ],
            metadata={},
        )

        assert len(schema.slides) == 3
        assert schema.slides[0].title == "Slide 1"
        assert schema.slides[2].title == "Slide 3"


class TestSlideSchema:
    """Test SlideSchema validation."""

    def test_valid_slide_schema(self):
        """RED: Test valid slide schema creation."""
        schema = SlideSchema(
            layout_name="Title and Content",
            title="Test Slide",
            content=[],
            notes="Speaker notes here",
        )

        assert schema.layout_name == "Title and Content"
        assert schema.title == "Test Slide"
        assert schema.notes == "Speaker notes here"
        assert len(schema.content) == 0

    def test_slide_schema_without_notes(self):
        """RED: Test slide schema with optional notes=None."""
        schema = SlideSchema(
            layout_name="Blank",
            title="No Notes",
            content=[],
            notes=None,
        )

        assert schema.notes is None

    def test_slide_schema_with_text_content(self):
        """RED: Test slide schema with TextBlock content."""
        text_block = TextBlock(
            placeholder_name="Content",
            text="Sample text content",
            language="en",
        )

        schema = SlideSchema(
            layout_name="Title and Content",
            title="Content Slide",
            content=[text_block],
        )

        assert len(schema.content) == 1
        assert isinstance(schema.content[0], TextBlock)


class TestTextBlock:
    """Test TextBlock and text capacity validation."""

    def test_valid_text_block_english(self):
        """RED: Test valid English text block."""
        block = TextBlock(
            placeholder_name="Content",
            text="English text content",
            language="en",
        )

        assert block.placeholder_name == "Content"
        assert block.text == "English text content"
        assert block.language == "en"

    def test_valid_text_block_japanese(self):
        """RED: Test valid Japanese text block."""
        block = TextBlock(
            placeholder_name="Content",
            text="日本語のテキストコンテンツ",
            language="ja",
        )

        assert block.language == "ja"
        assert block.text == "日本語のテキストコンテンツ"

    def test_text_capacity_calculation_english(self):
        """RED: Test text capacity calculation for English (1.0x)."""
        capacity = TextCapacity(language="en", max_chars=100)
        effective_capacity = capacity.get_effective_capacity()

        assert effective_capacity == 100  # 1.0x for English

    def test_text_capacity_calculation_japanese(self):
        """RED: Test text capacity calculation for Japanese (0.55x)."""
        capacity = TextCapacity(language="ja", max_chars=100)
        effective_capacity = capacity.get_effective_capacity()

        assert effective_capacity == 55  # 0.55x for Japanese

    def test_text_block_validates_capacity(self):
        """RED: Test that text block validates against capacity."""
        # This should raise ValidationError if text exceeds capacity
        long_text = "x" * 1000

        with pytest.raises(ValidationError) as exc_info:
            TextBlock(
                placeholder_name="Content",
                text=long_text,
                language="en",
                max_capacity=100,
            )

        assert "capacity" in str(exc_info.value).lower() or "length" in str(exc_info.value).lower()

    def test_invalid_language_code(self):
        """RED: Test that invalid language code is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TextBlock(
                placeholder_name="Content",
                text="Text",
                language="fr",  # type: ignore[arg-type]  # Only 'en' and 'ja' are allowed - testing validation
            )

        assert "language" in str(exc_info.value).lower()


class TestVisualAssetSchemas:
    """Test visual asset schemas (ImageBlock, ChartBlock, etc.)."""

    def test_valid_image_block(self):
        """Test valid ImageBlock creation with local file path."""
        block = ImageBlock(
            placeholder_name="Picture",
            image_path="/path/to/image.png",
            alt_text="Example image",
        )

        assert block.placeholder_name == "Picture"
        assert block.image_path == "/path/to/image.png"
        assert block.alt_text == "Example image"

    def test_image_block_with_local_path(self):
        """RED: Test ImageBlock with local file path."""
        block = ImageBlock(
            placeholder_name="Picture",
            image_path="/path/to/image.png",
            alt_text="Local image",
        )

        assert block.image_path == "/path/to/image.png"

    def test_valid_chart_block(self):
        """RED: Test valid ChartBlock creation."""
        block = ChartBlock(
            placeholder_name="Chart",
            chart_type="bar",
            data={"categories": ["A", "B"], "values": [10, 20]},
            title="Sales Chart",
        )

        assert block.chart_type == "bar"
        assert block.data["values"] == [10, 20]
        assert block.title == "Sales Chart"

    def test_valid_table_block(self):
        """RED: Test valid TableBlock creation."""
        block = TableBlock(
            placeholder_name="Table",
            rows=[["A", "B"], ["1", "2"]],
            headers=["Column 1", "Column 2"],
        )

        assert len(block.rows) == 2
        assert len(block.headers) == 2
        assert block.rows[0][0] == "A"

    def test_valid_smartart_block(self):
        """RED: Test valid SmartArtBlock creation."""
        block = SmartArtBlock(
            placeholder_name="SmartArt",
            diagram_type="process",
            nodes=[
                {"text": "Step 1", "level": 0},
                {"text": "Step 2", "level": 0},
            ],
        )

        assert block.diagram_type == "process"
        assert len(block.nodes) == 2
        assert block.nodes[0]["text"] == "Step 1"

    def test_table_block_properties(self):
        """RED: Test TableBlock num_rows and num_cols properties."""
        block = TableBlock(
            placeholder_name="Table",
            rows=[["A", "B"], ["C", "D"], ["E", "F"]],
            headers=["Column 1", "Column 2"],
        )

        assert block.num_rows == 3
        assert block.num_cols == 2

    def test_chart_block_invalid_data(self):
        """RED: Test ChartBlock with invalid data structure."""
        with pytest.raises(ValidationError):
            ChartBlock(
                placeholder_name="Chart",
                chart_type="bar",
                data="invalid",  # type: ignore[arg-type]  # Should be dict - testing validation
                title="Invalid Chart",
            )

    def test_table_block_empty_rows(self):
        """RED: Test TableBlock with empty rows."""
        with pytest.raises(ValidationError):
            TableBlock(
                placeholder_name="Table",
                rows=[],
                headers=["Column 1"],
            )


class TestContentBlockUnion:
    """Test that content blocks can be used as union types."""

    def test_slide_accepts_different_content_types(self):
        """RED: Test that SlideSchema accepts various ContentBlock types."""
        schema = SlideSchema(
            layout_name="Complex Layout",
            title="Mixed Content",
            content=[
                TextBlock(
                    placeholder_name="Title",
                    text="Title text",
                    language="en",
                ),
                ImageBlock(
                    placeholder_name="Picture",
                    image_path="/path/to/img.png",
                    alt_text="Image",
                ),
                ChartBlock(
                    placeholder_name="Chart",
                    chart_type="line",
                    data={"x": [1, 2], "y": [10, 20]},
                    title="Data",
                ),
            ],
        )

        assert len(schema.content) == 3
        assert isinstance(schema.content[0], TextBlock)
        assert isinstance(schema.content[1], ImageBlock)
        assert isinstance(schema.content[2], ChartBlock)
