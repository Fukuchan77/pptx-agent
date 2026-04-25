"""Unit tests for placeholder population fix strategies."""

from unittest.mock import Mock

from pptx_agent.fixer.schemas import FixStatus
from pptx_agent.qa.schemas import QAIssue, Severity


def make_empty_placeholder_issue(
    slide_index: int = 0,
    shape_index: int = 0,
    *,
    auto_fixable: bool = True,
) -> QAIssue:
    """Create an empty placeholder QA issue for testing.

    Args:
        slide_index: Zero-based slide index
        shape_index: Zero-based shape index
        auto_fixable: Whether the issue can be automatically fixed

    Returns:
        QA issue instance for empty placeholder
    """
    return QAIssue(
        rule_id="QA-L-002",
        severity=Severity.ERROR,
        slide_index=slide_index,
        shape_index=shape_index,
        message="Empty title placeholder detected",
        auto_fixable=auto_fixable,
        suggested_fix="Populate from outline headers",
    )


class TestPlaceholderPopulationStrategy:
    """Tests for placeholder population fix strategy."""

    def test_populate_title_placeholder_success(self) -> None:
        """Test successful population of empty title placeholder."""
        # This test will fail until we implement the strategy
        from pptx_agent.fixer.strategies.placeholder import PlaceholderPopulationStrategy

        issue = make_empty_placeholder_issue()
        strategy = PlaceholderPopulationStrategy()

        # Mock presentation with empty title
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_shape = Mock()
        mock_text_frame = Mock()

        mock_presentation.prs.slides = [mock_slide]
        mock_slide.shapes = [mock_shape]
        mock_shape.has_text_frame = True
        mock_shape.text_frame = mock_text_frame
        mock_shape.is_placeholder = True
        mock_shape.placeholder_format.type = 1  # TITLE placeholder type
        mock_text_frame.text = ""

        # Mock outline data
        mock_outline = Mock()
        mock_outline.slides = [{"title": "Generated Title"}]

        result = strategy.apply(issue, mock_presentation, mock_outline)

        assert result.status == FixStatus.SUCCESS
        assert "populated" in result.message.lower()
        assert mock_text_frame.text == "Generated Title"
        assert len(result.changes_made) > 0

    def test_populate_placeholder_no_outline_data(self) -> None:
        """Test placeholder population when no outline data available."""
        from pptx_agent.fixer.strategies.placeholder import PlaceholderPopulationStrategy

        issue = make_empty_placeholder_issue()
        strategy = PlaceholderPopulationStrategy()

        mock_presentation = Mock()
        mock_slide = Mock()
        mock_shape = Mock()

        mock_presentation.prs.slides = [mock_slide]
        mock_slide.shapes = [mock_shape]
        mock_shape.is_placeholder = True

        result = strategy.apply(issue, mock_presentation, outline=None)

        assert result.status == FixStatus.FAILED
        assert "no outline" in result.message.lower() or "missing data" in result.message.lower()

    def test_populate_placeholder_not_a_placeholder(self) -> None:
        """Test placeholder population on non-placeholder shape."""
        from pptx_agent.fixer.strategies.placeholder import PlaceholderPopulationStrategy

        issue = make_empty_placeholder_issue()
        strategy = PlaceholderPopulationStrategy()

        mock_presentation = Mock()
        mock_slide = Mock()
        mock_shape = Mock()

        mock_presentation.prs.slides = [mock_slide]
        mock_slide.shapes = [mock_shape]
        mock_shape.is_placeholder = False

        mock_outline = Mock()

        result = strategy.apply(issue, mock_presentation, mock_outline)

        assert result.status == FixStatus.FAILED
        assert "not a placeholder" in result.message.lower()

    def test_populate_placeholder_already_has_content(self) -> None:
        """Test placeholder population skips placeholders with existing content."""
        from pptx_agent.fixer.strategies.placeholder import PlaceholderPopulationStrategy

        issue = make_empty_placeholder_issue()
        strategy = PlaceholderPopulationStrategy()

        mock_presentation = Mock()
        mock_slide = Mock()
        mock_shape = Mock()
        mock_text_frame = Mock()

        mock_presentation.prs.slides = [mock_slide]
        mock_slide.shapes = [mock_shape]
        mock_shape.has_text_frame = True
        mock_shape.text_frame = mock_text_frame
        mock_shape.is_placeholder = True
        mock_text_frame.text = "Existing content"

        mock_outline = Mock()

        result = strategy.apply(issue, mock_presentation, mock_outline)

        assert result.status == FixStatus.SKIPPED
        assert "already has content" in result.message.lower()

    def test_populate_body_placeholder(self) -> None:
        """Test population of body placeholder with bullet points."""
        from pptx_agent.fixer.strategies.placeholder import PlaceholderPopulationStrategy

        issue = QAIssue(
            rule_id="QA-L-003",
            severity=Severity.WARNING,
            slide_index=0,
            shape_index=0,  # Changed from 1 to 0 to match mock_slide.shapes list
            message="Unpopulated body placeholder",
            auto_fixable=True,
        )
        strategy = PlaceholderPopulationStrategy()

        mock_presentation = Mock()
        mock_slide = Mock()
        mock_shape = Mock()
        mock_text_frame = Mock()

        # Mock the clear() and add_paragraph() methods
        mock_text_frame.clear = Mock()
        mock_paragraph = Mock()
        mock_text_frame.add_paragraph = Mock(return_value=mock_paragraph)

        mock_presentation.prs.slides = [mock_slide]
        mock_slide.shapes = [mock_shape]
        mock_shape.has_text_frame = True
        mock_shape.text_frame = mock_text_frame
        mock_shape.is_placeholder = True
        mock_shape.placeholder_format.type = 2  # BODY placeholder type
        mock_text_frame.text = ""

        # Mock outline with bullet points
        mock_outline = Mock()
        mock_outline.slides = [{"bullets": ["Point 1", "Point 2", "Point 3"]}]

        result = strategy.apply(issue, mock_presentation, mock_outline)

        assert result.status == FixStatus.SUCCESS
        assert "populated" in result.message.lower()
        # Verify clear() was called
        mock_text_frame.clear.assert_called_once()
        # Verify add_paragraph() was called 3 times (once per bullet)
        assert mock_text_frame.add_paragraph.call_count == 3

    def test_populate_placeholder_invalid_slide_index(self) -> None:
        """Test placeholder population handles invalid slide index."""
        from pptx_agent.fixer.strategies.placeholder import PlaceholderPopulationStrategy

        issue = make_empty_placeholder_issue(slide_index=999)
        strategy = PlaceholderPopulationStrategy()

        mock_presentation = Mock()
        mock_presentation.prs.slides = []
        mock_outline = Mock()

        result = strategy.apply(issue, mock_presentation, mock_outline)

        assert result.status == FixStatus.FAILED
        assert "invalid" in result.message.lower() or "not found" in result.message.lower()

    def test_populate_placeholder_invalid_shape_index(self) -> None:
        """Test placeholder population handles invalid shape index."""
        from pptx_agent.fixer.strategies.placeholder import PlaceholderPopulationStrategy

        issue = make_empty_placeholder_issue(shape_index=999)
        strategy = PlaceholderPopulationStrategy()

        mock_presentation = Mock()
        mock_slide = Mock()
        mock_presentation.prs.slides = [mock_slide]
        mock_slide.shapes = []
        mock_outline = Mock()

        result = strategy.apply(issue, mock_presentation, mock_outline)

        assert result.status == FixStatus.FAILED
        assert "invalid" in result.message.lower() or "not found" in result.message.lower()


# Made with Bob
