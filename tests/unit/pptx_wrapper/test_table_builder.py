"""Tests for table builder functionality.

Tests table creation from TableBlock specifications.
"""

from unittest.mock import Mock

import pytest

from pptx_agent.pptx_wrapper.slide import SlideWrapper
from pptx_agent.pptx_wrapper.table_builder import add_table_to_slide
from pptx_agent.schemas.visual_assets import TableBlock


@pytest.fixture
def mock_slide():
    """Create a mock SlideWrapper for testing."""
    slide = Mock(spec=SlideWrapper)
    # Mock the public add_table method instead of private _slide
    slide.add_table = Mock(return_value=Mock(table=Mock()))
    return slide


class TestTableBuilder:
    """Tests for table builder functionality."""

    def test_add_simple_table_creates_table_shape(self, mock_slide):  # type: ignore[reportUnknownParameterType, reportMissingParameterType]
        """Test that adding a table creates a table shape on the slide."""
        table_block = TableBlock(
            placeholder_name="Table Placeholder 1",
            headers=["Product", "Q1", "Q2", "Q3"],
            rows=[
                ["Product A", "100", "150", "120"],
                ["Product B", "80", "90", "85"],
                ["Product C", "120", "110", "130"],
            ],
        )

        # This should create a table on the slide
        add_table_to_slide(mock_slide, table_block)

        # Verify that a table was added using the public method
        mock_slide.add_table.assert_called_once()

    def test_add_table_with_many_columns(self, mock_slide):  # type: ignore[reportUnknownParameterType, reportMissingParameterType]
        """Test adding a table with many columns (up to 10)."""
        table_block = TableBlock(
            placeholder_name="Table Placeholder 1",
            headers=[
                "Col1",
                "Col2",
                "Col3",
                "Col4",
                "Col5",
                "Col6",
                "Col7",
                "Col8",
                "Col9",
                "Col10",
            ],
            rows=[
                ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10"],
                ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9", "B10"],
            ],
        )

        add_table_to_slide(mock_slide, table_block)

        # Verify table was added
        mock_slide.add_table.assert_called_once()

    def test_add_table_with_many_rows(self, mock_slide):  # type: ignore[reportUnknownParameterType, reportMissingParameterType]
        """Test adding a table with many rows (up to 20)."""
        headers = ["Name", "Value"]
        rows = [[f"Row{i}", f"Value{i}"] for i in range(20)]

        table_block = TableBlock(
            placeholder_name="Table Placeholder 1",
            headers=headers,
            rows=rows,
        )

        add_table_to_slide(mock_slide, table_block)

        # Verify table was added
        mock_slide.add_table.assert_called_once()

    def test_add_table_with_empty_headers_raises_error(self, mock_slide):  # type: ignore[reportUnknownParameterType, reportMissingParameterType]
        """Test that empty headers raise ValueError."""
        table_block = TableBlock(
            placeholder_name="Table Placeholder 1",
            headers=[],
            rows=[["A", "B"]],
        )

        with pytest.raises(ValueError, match="Table must have at least one column"):
            add_table_to_slide(mock_slide, table_block)

    def test_add_table_with_mismatched_column_count_raises_error(self, mock_slide):  # type: ignore[reportUnknownParameterType, reportMissingParameterType]
        """Test that mismatched column counts raise ValueError."""
        table_block = TableBlock(
            placeholder_name="Table Placeholder 1",
            headers=["Col1", "Col2", "Col3"],
            rows=[
                ["A", "B", "C"],
                ["D", "E"],  # Only 2 columns, should be 3
            ],
        )

        with pytest.raises(ValueError, match="Row 1 has 2 columns, expected 3"):
            add_table_to_slide(mock_slide, table_block)

    def test_table_properties_num_rows_and_cols(self):
        """Test that TableBlock properties correctly report dimensions."""
        table_block = TableBlock(
            placeholder_name="Table Placeholder 1",
            headers=["A", "B", "C"],
            rows=[
                ["1", "2", "3"],
                ["4", "5", "6"],
            ],
        )

        assert table_block.num_rows == 2
        assert table_block.num_cols == 3

    def test_add_single_row_table(self, mock_slide):  # type: ignore[reportUnknownParameterType, reportMissingParameterType]
        """Test adding a table with just one data row."""
        table_block = TableBlock(
            placeholder_name="Table Placeholder 1",
            headers=["Category", "Value"],
            rows=[["Total", "100"]],
        )

        add_table_to_slide(mock_slide, table_block)

        # Verify table was added
        mock_slide.add_table.assert_called_once()
