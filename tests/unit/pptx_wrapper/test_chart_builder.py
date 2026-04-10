"""Tests for chart builder functionality.

Tests chart creation from ChartBlock specifications.
"""

from unittest.mock import Mock

import pytest

from pptx_agent.pptx_wrapper.chart_builder import add_chart_to_slide
from pptx_agent.pptx_wrapper.slide import SlideWrapper
from pptx_agent.schemas.visual_assets import ChartBlock


@pytest.fixture
def mock_slide():
    """Create a mock SlideWrapper for testing."""
    slide = Mock(spec=SlideWrapper)
    # Mock the public add_chart method instead of private _slide
    slide.add_chart = Mock(return_value=Mock())
    return slide


class TestChartBuilder:
    """Tests for chart builder functionality."""

    def test_add_bar_chart_creates_chart_shape(self, mock_slide):  # type: ignore[reportUnknownParameterType, reportMissingParameterType]
        """Test that adding a bar chart creates a chart shape on the slide."""
        chart_block = ChartBlock(
            placeholder_name="Chart Placeholder 1",
            chart_type="bar",
            data={
                "categories": ["Q1", "Q2", "Q3", "Q4"],
                "series": [
                    {"name": "Sales", "values": [100, 150, 120, 180]},
                    {"name": "Costs", "values": [80, 90, 85, 95]},
                ],
            },
            title="Quarterly Performance",
        )

        # This should create a chart on the slide
        add_chart_to_slide(mock_slide, chart_block)

        # Verify that a chart was added using the public method
        mock_slide.add_chart.assert_called_once()

    def test_add_line_chart_with_single_series(self, mock_slide):  # type: ignore[reportUnknownParameterType, reportMissingParameterType]
        """Test adding a line chart with a single data series."""
        chart_block = ChartBlock(
            placeholder_name="Chart Placeholder 1",
            chart_type="line",
            data={
                "categories": ["Jan", "Feb", "Mar", "Apr", "May"],
                "series": [
                    {"name": "Revenue", "values": [10, 15, 12, 18, 20]},
                ],
            },
            title="Monthly Revenue Trend",
        )

        add_chart_to_slide(mock_slide, chart_block)

        # Verify chart was added
        mock_slide.add_chart.assert_called_once()

    def test_add_pie_chart_creates_chart(self, mock_slide):  # type: ignore[reportUnknownParameterType, reportMissingParameterType]
        """Test adding a pie chart."""
        chart_block = ChartBlock(
            placeholder_name="Chart Placeholder 1",
            chart_type="pie",
            data={
                "categories": ["Product A", "Product B", "Product C"],
                "series": [
                    {"name": "Market Share", "values": [40, 35, 25]},
                ],
            },
            title="Market Share Distribution",
        )

        add_chart_to_slide(mock_slide, chart_block)

        # Verify chart was added
        mock_slide.add_chart.assert_called_once()

    def test_add_chart_with_invalid_type_raises_error(self, mock_slide):  # type: ignore[reportUnknownParameterType, reportMissingParameterType]
        """Test that invalid chart type raises ValueError."""
        chart_block = ChartBlock(
            placeholder_name="Chart Placeholder 1",
            chart_type="invalid_type",
            data={
                "categories": ["A", "B"],
                "series": [{"name": "Data", "values": [1, 2]}],
            },
            title="Test Chart",
        )

        with pytest.raises(ValueError, match="Unsupported chart type"):
            add_chart_to_slide(mock_slide, chart_block)

    def test_add_chart_with_empty_data_raises_error(self, mock_slide):  # type: ignore[reportUnknownParameterType, reportMissingParameterType]
        """Test that empty data raises ValueError."""
        chart_block = ChartBlock(
            placeholder_name="Chart Placeholder 1",
            chart_type="bar",
            data={"categories": [], "series": []},
            title="Empty Chart",
        )

        with pytest.raises(ValueError, match="Chart data cannot be empty"):
            add_chart_to_slide(mock_slide, chart_block)

    def test_add_column_chart_creates_chart(self, mock_slide):  # type: ignore[reportUnknownParameterType, reportMissingParameterType]
        """Test adding a column chart (vertical bars)."""
        chart_block = ChartBlock(
            placeholder_name="Chart Placeholder 1",
            chart_type="column",
            data={
                "categories": ["2020", "2021", "2022", "2023"],
                "series": [
                    {"name": "Growth", "values": [5, 8, 12, 15]},
                ],
            },
            title="Year-over-Year Growth",
        )

        add_chart_to_slide(mock_slide, chart_block)

        # Verify chart was added
        mock_slide.add_chart.assert_called_once()
