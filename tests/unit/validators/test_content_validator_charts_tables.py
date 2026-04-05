"""Unit tests for chart and table constraint validation in content validator."""

import pytest

from pptx_agent.schemas.presentation import PresentationSchema
from pptx_agent.schemas.slide import SlideSchema
from pptx_agent.schemas.text import TextBlock
from pptx_agent.schemas.visual_assets import ChartBlock, TableBlock
from pptx_agent.validators.content_validator import validate_content
from pptx_agent.validators.exceptions import ContentValidationError


class TestChartValidation:
    """Test cases for chart constraint validation."""

    def test_validate_valid_chart_block(self) -> None:
        """Test that valid chart passes validation."""
        slides = [
            SlideSchema(
                layout_name="Chart Layout",
                title="Sales Data",
                content=[
                    TextBlock(placeholder_name="Title", text="Sales Data", language="en"),
                    ChartBlock(
                        placeholder_name="Chart",
                        chart_type="bar",
                        data={"series": ["Q1", "Q2"], "values": [100, 200]},
                        title="Quarterly Sales",
                    ),
                ],
            ),
        ]
        presentation = PresentationSchema(title="Test Presentation", slides=slides)
        result = validate_content(presentation)
        assert result == presentation

    def test_validate_chart_with_invalid_type(self) -> None:
        """Test that unsupported chart type raises error."""
        slides = [
            SlideSchema(
                layout_name="Chart Layout",
                title="Data",
                content=[
                    TextBlock(placeholder_name="Title", text="Data", language="en"),
                    ChartBlock(
                        placeholder_name="Chart",
                        chart_type="invalid_type",  # Invalid chart type
                        data={"series": ["A"], "values": [100]},
                        title="Chart",
                    ),
                ],
            ),
        ]
        presentation = PresentationSchema(title="Test Presentation", slides=slides)

        with pytest.raises(
            ContentValidationError,
            match="Slide 1 'Data' has invalid chart type 'invalid_type'",
        ):
            validate_content(presentation)

    def test_validate_chart_with_all_supported_types(self) -> None:
        """Test that all supported chart types pass validation."""
        supported_types = ["bar", "column", "line", "pie", "scatter", "doughnut", "area", "radar"]

        for chart_type in supported_types:
            slides = [
                SlideSchema(
                    layout_name="Chart Layout",
                    title=f"{chart_type.title()} Chart",
                    content=[
                        TextBlock(
                            placeholder_name="Title",
                            text=f"{chart_type.title()} Chart",
                            language="en",
                        ),
                        ChartBlock(
                            placeholder_name="Chart",
                            chart_type=chart_type,
                            data={"series": ["A"], "values": [100]},
                            title="Chart",
                        ),
                    ],
                ),
            ]
            presentation = PresentationSchema(title="Test Presentation", slides=slides)
            result = validate_content(presentation)
            assert result == presentation

    def test_validate_chart_with_empty_data(self) -> None:
        """Test that chart with empty data is rejected by Pydantic schema."""
        # Note: This is already validated by Pydantic's Field(min_length=1) on data
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="Dictionary should have at least 1 item"):
            ChartBlock(
                placeholder_name="Chart",
                chart_type="bar",
                data={},  # Empty data - rejected by schema
                title="Chart",
            )


class TestTableValidation:
    """Test cases for table constraint validation."""

    def test_validate_valid_table_block(self) -> None:
        """Test that valid table passes validation."""
        slides = [
            SlideSchema(
                layout_name="Table Layout",
                title="Data Table",
                content=[
                    TextBlock(placeholder_name="Title", text="Data Table", language="en"),
                    TableBlock(
                        placeholder_name="Table",
                        headers=["Name", "Value"],
                        rows=[["Item 1", "100"], ["Item 2", "200"]],
                    ),
                ],
            ),
        ]
        presentation = PresentationSchema(title="Test Presentation", slides=slides)
        result = validate_content(presentation)
        assert result == presentation

    def test_validate_table_exceeds_max_rows(self) -> None:
        """Test that table with >20 rows raises error."""
        # Create 21 rows (exceeds max 20)
        rows = [[f"Item {i}", str(i * 10)] for i in range(1, 22)]
        slides = [
            SlideSchema(
                layout_name="Table Layout",
                title="Large Table",
                content=[
                    TextBlock(placeholder_name="Title", text="Large Table", language="en"),
                    TableBlock(
                        placeholder_name="Table",
                        headers=["Name", "Value"],
                        rows=rows,
                    ),
                ],
            ),
        ]
        presentation = PresentationSchema(title="Test Presentation", slides=slides)

        with pytest.raises(
            ContentValidationError,
            match="Slide 1 'Large Table' has table with 21 rows \\(max 20\\)",
        ):
            validate_content(presentation)

    def test_validate_table_exceeds_max_columns(self) -> None:
        """Test that table with >10 columns raises error."""
        # Create 11 columns (exceeds max 10)
        headers = [f"Col{i}" for i in range(1, 12)]
        rows = [[str(i * j) for j in range(1, 12)] for i in range(1, 3)]
        slides = [
            SlideSchema(
                layout_name="Table Layout",
                title="Wide Table",
                content=[
                    TextBlock(placeholder_name="Title", text="Wide Table", language="en"),
                    TableBlock(
                        placeholder_name="Table",
                        headers=headers,
                        rows=rows,
                    ),
                ],
            ),
        ]
        presentation = PresentationSchema(title="Test Presentation", slides=slides)

        with pytest.raises(
            ContentValidationError,
            match="Slide 1 'Wide Table' has table with 11 columns \\(max 10\\)",
        ):
            validate_content(presentation)

    def test_validate_table_at_max_dimensions(self) -> None:
        """Test that table with exactly 20 rows x 10 columns passes."""
        headers = [f"Col{i}" for i in range(1, 11)]  # 10 columns
        rows = [[str(i * j) for j in range(1, 11)] for i in range(1, 21)]  # 20 rows
        slides = [
            SlideSchema(
                layout_name="Table Layout",
                title="Max Table",
                content=[
                    TextBlock(placeholder_name="Title", text="Max Table", language="en"),
                    TableBlock(
                        placeholder_name="Table",
                        headers=headers,
                        rows=rows,
                    ),
                ],
            ),
        ]
        presentation = PresentationSchema(title="Test Presentation", slides=slides)
        result = validate_content(presentation)
        assert result == presentation

    def test_validate_table_with_inconsistent_row_lengths(self) -> None:
        """Test that table with inconsistent row lengths raises error."""
        slides = [
            SlideSchema(
                layout_name="Table Layout",
                title="Bad Table",
                content=[
                    TextBlock(placeholder_name="Title", text="Bad Table", language="en"),
                    TableBlock(
                        placeholder_name="Table",
                        headers=["Name", "Value"],
                        rows=[
                            ["Item 1", "100"],
                            ["Item 2", "200", "Extra"],  # Inconsistent length
                        ],
                    ),
                ],
            ),
        ]
        presentation = PresentationSchema(title="Test Presentation", slides=slides)

        with pytest.raises(
            ContentValidationError,
            match="Slide 1 'Bad Table' has table with inconsistent row lengths",
        ):
            validate_content(presentation)

    def test_validate_table_with_empty_rows(self) -> None:
        """Test that table with empty rows is rejected by Pydantic schema."""
        # Note: This is already validated by Pydantic's Field(min_length=1) on rows
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="List should have at least 1 item"):
            TableBlock(
                placeholder_name="Table",
                headers=["Name", "Value"],
                rows=[],  # Empty rows - rejected by schema
            )


class TestMixedContentValidation:
    """Test cases for slides with mixed content types."""

    def test_validate_slide_with_text_chart_and_table(self) -> None:
        """Test that slide with text, chart, and table all pass validation."""
        slides = [
            SlideSchema(
                layout_name="Mixed Layout",
                title="Mixed Content",
                content=[
                    TextBlock(placeholder_name="Title", text="Mixed Content", language="en"),
                    ChartBlock(
                        placeholder_name="Chart",
                        chart_type="bar",
                        data={"series": ["Q1"], "values": [100]},
                        title="Chart",
                    ),
                    TableBlock(
                        placeholder_name="Table",
                        headers=["Name", "Value"],
                        rows=[["Item 1", "100"]],
                    ),
                ],
            ),
        ]
        presentation = PresentationSchema(title="Test Presentation", slides=slides)
        result = validate_content(presentation)
        assert result == presentation

    def test_validate_multiple_slides_with_charts_and_tables(self) -> None:
        """Test that multiple slides with charts and tables pass validation."""
        slides = [
            SlideSchema(
                layout_name="Chart Layout",
                title="Chart Slide",
                content=[
                    TextBlock(placeholder_name="Title", text="Chart Slide", language="en"),
                    ChartBlock(
                        placeholder_name="Chart",
                        chart_type="pie",
                        data={"series": ["A", "B"], "values": [50, 50]},
                        title="Pie Chart",
                    ),
                ],
            ),
            SlideSchema(
                layout_name="Table Layout",
                title="Table Slide",
                content=[
                    TextBlock(placeholder_name="Title", text="Table Slide", language="en"),
                    TableBlock(
                        placeholder_name="Table",
                        headers=["Col1", "Col2"],
                        rows=[["A", "1"], ["B", "2"]],
                    ),
                ],
            ),
        ]
        presentation = PresentationSchema(title="Test Presentation", slides=slides)
        result = validate_content(presentation)
        assert result == presentation
