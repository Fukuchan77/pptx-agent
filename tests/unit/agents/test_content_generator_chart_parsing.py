"""Tests for chart data parsing robustness in content generator."""

import logging

import pytest

from pptx_agent.agents.content_generator import parse_chart_data


class TestChartDataParsingRobustness:
    """Test suite for chart data parsing with invalid numeric values."""

    def test_parse_chart_data_with_invalid_numeric_value_logs_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that invalid numeric strings trigger warning logs before fallback."""
        # Arrange
        content = "chart:bar|Q1=100,Q2=invalid,Q3=200"
        placeholder_name = "Content Placeholder"
        title = "Test Chart"

        # Act
        with caplog.at_level(logging.WARNING):
            result = parse_chart_data(content, placeholder_name, title)

        # Assert - warning should be logged
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "WARNING"
        assert "invalid" in caplog.records[0].message.lower()
        assert (
            "numeric" in caplog.records[0].message.lower()
            or "value" in caplog.records[0].message.lower()
        )

        # Assert - fallback value should be 0.0
        assert result.data["series"][0]["values"] == [100.0, 0.0, 200.0]
        assert result.data["categories"] == ["Q1", "Q2", "Q3"]

    def test_parse_chart_data_with_multiple_invalid_values_logs_multiple_warnings(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that multiple invalid values each trigger a warning."""
        # Arrange
        content = "chart:line|Jan=abc,Feb=200,Mar=xyz,Apr=300"
        placeholder_name = "Content Placeholder"
        title = "Test Chart"

        # Act
        with caplog.at_level(logging.WARNING):
            result = parse_chart_data(content, placeholder_name, title)

        # Assert - two warnings should be logged
        assert len(caplog.records) == 2

        # Check first warning contains 'abc'
        assert "abc" in caplog.records[0].message

        # Check second warning contains 'xyz'
        assert "xyz" in caplog.records[1].message

        # Assert - fallback values should be 0.0
        assert result.data["series"][0]["values"] == [0.0, 200.0, 0.0, 300.0]

    def test_parse_chart_data_with_empty_string_value_logs_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that empty string values trigger warning."""
        # Arrange
        content = "chart:bar|Q1=100,Q2=,Q3=300"
        placeholder_name = "Content Placeholder"
        title = "Test Chart"

        # Act
        with caplog.at_level(logging.WARNING):
            result = parse_chart_data(content, placeholder_name, title)

        # Assert - warning should be logged for empty value
        assert len(caplog.records) >= 1
        warning_messages = [record.message for record in caplog.records]
        assert any("" in msg or "empty" in msg.lower() for msg in warning_messages)

        # Assert - fallback value should be 0.0
        assert result.data["series"][0]["values"] == [100.0, 0.0, 300.0]

    def test_parse_chart_data_with_valid_values_no_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that valid numeric values don't trigger warnings."""
        # Arrange
        content = "chart:bar|Q1=100,Q2=150.5,Q3=200"
        placeholder_name = "Content Placeholder"
        title = "Test Chart"

        # Act
        with caplog.at_level(logging.WARNING):
            result = parse_chart_data(content, placeholder_name, title)

        # Assert - no warnings should be logged
        assert len(caplog.records) == 0

        # Assert - all values parsed correctly
        assert result.data["series"][0]["values"] == [100.0, 150.5, 200.0]

    def test_parse_chart_data_warning_includes_invalid_value_for_debugging(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that warning message includes the invalid value for debugging."""
        # Arrange
        invalid_value = "not_a_number"
        content = f"chart:pie|Category A={invalid_value}"
        placeholder_name = "Content Placeholder"
        title = "Test Chart"

        # Act
        with caplog.at_level(logging.WARNING):
            result = parse_chart_data(content, placeholder_name, title)

        # Assert - warning should contain the invalid value
        assert len(caplog.records) == 1
        assert invalid_value in caplog.records[0].message

        # Assert - fallback occurred
        assert result.data["series"][0]["values"] == [0.0]
