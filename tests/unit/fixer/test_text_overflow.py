"""Unit tests for text overflow fix strategies."""

from unittest.mock import Mock, patch

from pptx_agent.fixer.schemas import FixStatus
from pptx_agent.qa.schemas import QAIssue, Severity


def make_text_overflow_issue(
    slide_index: int = 0,
    shape_index: int = 0,
    *,
    auto_fixable: bool = True,
) -> QAIssue:
    """Create a text overflow QA issue for testing.

    Args:
        slide_index: Zero-based slide index
        shape_index: Zero-based shape index
        auto_fixable: Whether the issue can be automatically fixed

    Returns:
        QA issue instance for text overflow
    """
    return QAIssue(
        rule_id="QA-L-001",
        severity=Severity.ERROR,
        slide_index=slide_index,
        shape_index=shape_index,
        message="Text overflow detected in text frame (estimated 600 characters)",
        auto_fixable=auto_fixable,
        suggested_fix="Reduce font size, switch layout, or summarize content",
    )


class TestFontReductionStrategy:
    """Tests for font reduction fix strategy."""

    def test_font_reduction_success(self) -> None:
        """Test successful font reduction fixes text overflow."""
        # This test will fail until we implement the strategy
        from pptx_agent.fixer.strategies.text_overflow import FontReductionStrategy

        issue = make_text_overflow_issue()
        strategy = FontReductionStrategy()

        # Mock presentation wrapper
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_shape = Mock()
        mock_text_frame = Mock()
        mock_paragraph = Mock()
        mock_run = Mock()

        # Setup mock hierarchy
        mock_presentation.prs.slides = [mock_slide]
        mock_slide.shapes = [mock_shape]
        mock_shape.has_text_frame = True
        mock_shape.text_frame = mock_text_frame
        mock_text_frame.paragraphs = [mock_paragraph]
        mock_paragraph.runs = [mock_run]
        mock_run.font.size = 120000  # 12pt in EMUs (English Metric Units)

        result = strategy.apply(issue, mock_presentation)

        assert result.status == FixStatus.SUCCESS
        assert "font size reduced" in result.message.lower()
        assert len(result.changes_made) > 0
        assert mock_run.font.size < 120000  # Font size should be reduced

    def test_font_reduction_minimum_threshold(self) -> None:
        """Test font reduction respects minimum font size threshold."""
        from pptx_agent.fixer.strategies.text_overflow import FontReductionStrategy

        issue = make_text_overflow_issue()
        strategy = FontReductionStrategy()

        # Mock with already small font
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_shape = Mock()
        mock_text_frame = Mock()
        mock_paragraph = Mock()
        mock_run = Mock()

        mock_presentation.prs.slides = [mock_slide]
        mock_slide.shapes = [mock_shape]
        mock_shape.has_text_frame = True
        mock_shape.text_frame = mock_text_frame
        mock_text_frame.paragraphs = [mock_paragraph]
        mock_paragraph.runs = [mock_run]
        mock_run.font.size = 80000  # 8pt - already at minimum

        result = strategy.apply(issue, mock_presentation)

        # Should fail or return partial since font is already at minimum
        assert result.status in {FixStatus.FAILED, FixStatus.PARTIAL}
        assert "minimum" in result.message.lower() or "cannot reduce" in result.message.lower()

    def test_font_reduction_no_text_frame(self) -> None:
        """Test font reduction handles shapes without text frames."""
        from pptx_agent.fixer.strategies.text_overflow import FontReductionStrategy

        issue = make_text_overflow_issue()
        strategy = FontReductionStrategy()

        # Mock shape without text frame
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_shape = Mock()

        mock_presentation.prs.slides = [mock_slide]
        mock_slide.shapes = [mock_shape]
        mock_shape.has_text_frame = False

        result = strategy.apply(issue, mock_presentation)

        assert result.status == FixStatus.FAILED
        assert "no text frame" in result.message.lower()

    def test_font_reduction_multiple_runs(self) -> None:
        """Test font reduction handles multiple text runs."""
        from pptx_agent.fixer.strategies.text_overflow import FontReductionStrategy

        issue = make_text_overflow_issue()
        strategy = FontReductionStrategy()

        # Create proper mock fonts that track size changes
        class MockFont:
            def __init__(self, size: int) -> None:
                self.size = size

        class MockRun:
            def __init__(self, size: int) -> None:
                self.font = MockFont(size)

        # Mock with multiple runs
        # Note: 1pt = 12700 EMU, so 14pt=177800, 12pt=152400, 10pt=127000
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_shape = Mock()
        mock_text_frame = Mock()
        mock_paragraph = Mock()
        mock_run1 = MockRun(177800)  # 14pt
        mock_run2 = MockRun(152400)  # 12pt
        mock_run3 = MockRun(127000)  # 10pt

        mock_presentation.prs.slides = [mock_slide]
        mock_slide.shapes = [mock_shape]
        mock_shape.has_text_frame = True
        mock_shape.text_frame = mock_text_frame
        mock_text_frame.paragraphs = [mock_paragraph]
        mock_paragraph.runs = [mock_run1, mock_run2, mock_run3]

        result = strategy.apply(issue, mock_presentation)

        assert result.status == FixStatus.SUCCESS
        # All runs should be reduced (10% reduction)
        assert mock_run1.font.size == 160020  # 177800 * 0.9 = 160020 (14pt -> 12.6pt)
        assert mock_run2.font.size == 137160  # 152400 * 0.9 = 137160 (12pt -> 10.8pt)
        assert mock_run3.font.size == 114300  # 127000 * 0.9 = 114300 (10pt -> 9pt)

    def test_font_reduction_invalid_slide_index(self) -> None:
        """Test font reduction handles invalid slide index."""
        from pptx_agent.fixer.strategies.text_overflow import FontReductionStrategy

        issue = make_text_overflow_issue(slide_index=999)
        strategy = FontReductionStrategy()

        mock_presentation = Mock()
        mock_presentation.prs.slides = []

        result = strategy.apply(issue, mock_presentation)

        assert result.status == FixStatus.FAILED
        assert "invalid" in result.message.lower() or "not found" in result.message.lower()

    def test_font_reduction_invalid_shape_index(self) -> None:
        """Test font reduction handles invalid shape index."""
        from pptx_agent.fixer.strategies.text_overflow import FontReductionStrategy

        issue = make_text_overflow_issue(shape_index=999)
        strategy = FontReductionStrategy()

        mock_presentation = Mock()
        mock_slide = Mock()
        mock_presentation.prs.slides = [mock_slide]
        mock_slide.shapes = []

        result = strategy.apply(issue, mock_presentation)

        assert result.status == FixStatus.FAILED
        assert "invalid" in result.message.lower() or "not found" in result.message.lower()


class TestLayoutSwitchingStrategy:
    """Tests for layout switching fix strategy."""

    def test_layout_switching_success(self) -> None:
        """Test successful layout switch fixes text overflow."""
        # This test will fail until we implement the strategy
        from pptx_agent.fixer.strategies.text_overflow import LayoutSwitchingStrategy

        issue = make_text_overflow_issue()
        strategy = LayoutSwitchingStrategy()

        # Mock presentation with multiple layouts
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_shape = Mock()
        mock_layout1 = Mock()
        mock_layout2 = Mock()

        mock_presentation.prs.slides = [mock_slide]
        mock_slide.shapes = [mock_shape]
        mock_slide.slide_layout = mock_layout1
        mock_presentation.prs.slide_layouts = [mock_layout1, mock_layout2]

        result = strategy.apply(issue, mock_presentation)

        # Layout switching is not yet implemented, so it returns SKIPPED
        assert result.status == FixStatus.SKIPPED
        assert "layout" in result.message.lower()
        assert len(result.changes_made) > 0

    def test_layout_switching_no_alternative_layouts(self) -> None:
        """Test layout switching when no alternative layouts available."""
        from pptx_agent.fixer.strategies.text_overflow import LayoutSwitchingStrategy

        issue = make_text_overflow_issue()
        strategy = LayoutSwitchingStrategy()

        # Mock with only one layout
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_layout = Mock()

        mock_presentation.prs.slides = [mock_slide]
        mock_slide.slide_layout = mock_layout
        mock_presentation.prs.slide_layouts = [mock_layout]

        result = strategy.apply(issue, mock_presentation)

        assert result.status == FixStatus.FAILED
        assert "no alternative" in result.message.lower()


class TestContentSummarizationStrategy:
    """Tests for content summarization fix strategy."""

    def test_content_summarization_success(self) -> None:
        """Test successful content summarization fixes text overflow."""
        # This test will fail until we implement the strategy
        from pptx_agent.fixer.strategies.text_overflow import ContentSummarizationStrategy

        issue = make_text_overflow_issue()
        strategy = ContentSummarizationStrategy()

        # Mock presentation with long text
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_shape = Mock()
        mock_text_frame = Mock()

        mock_presentation.prs.slides = [mock_slide]
        mock_slide.shapes = [mock_shape]
        mock_shape.has_text_frame = True
        mock_shape.text_frame = mock_text_frame
        mock_text_frame.text = "This is a very long text " * 50  # Long text

        with patch("pptx_agent.fixer.strategies.text_overflow.summarize_text") as mock_summarize:
            mock_summarize.return_value = "Summarized text"

            result = strategy.apply(issue, mock_presentation)

            assert result.status == FixStatus.SUCCESS
            assert "summarized" in result.message.lower()
            assert mock_text_frame.text == "Summarized text"

    def test_content_summarization_short_text(self) -> None:
        """Test content summarization skips already short text."""
        from pptx_agent.fixer.strategies.text_overflow import ContentSummarizationStrategy

        issue = make_text_overflow_issue()
        strategy = ContentSummarizationStrategy()

        # Mock with short text
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_shape = Mock()
        mock_text_frame = Mock()

        mock_presentation.prs.slides = [mock_slide]
        mock_slide.shapes = [mock_shape]
        mock_shape.has_text_frame = True
        mock_shape.text_frame = mock_text_frame
        mock_text_frame.text = "Short text"

        result = strategy.apply(issue, mock_presentation)

        assert result.status == FixStatus.SKIPPED
        assert (
            "already short" in result.message.lower()
            or "no summarization needed" in result.message.lower()
        )


# Made with Bob
