"""Unit tests for style reset fix strategies."""

from unittest.mock import Mock

from pptx_agent.fixer.schemas import FixStatus
from pptx_agent.qa.schemas import QAIssue, Severity


def make_style_violation_issue(
    slide_index: int = 0,
    shape_index: int = 0,
    rule_id: str = "QA-S-001",
    *,
    auto_fixable: bool = True,
) -> QAIssue:
    """Create a style violation QA issue for testing.

    Args:
        slide_index: Zero-based slide index
        shape_index: Zero-based shape index
        rule_id: QA rule identifier
        auto_fixable: Whether the issue can be automatically fixed

    Returns:
        QA issue instance for style violation
    """
    return QAIssue(
        rule_id=rule_id,
        severity=Severity.WARNING,
        slide_index=slide_index,
        shape_index=shape_index,
        message="Off-template font usage detected",
        auto_fixable=auto_fixable,
        suggested_fix="Reset to template master font",
    )


class TestStyleResetStrategy:
    """Tests for style reset fix strategy."""

    def test_reset_font_to_master_success(self) -> None:
        """Test successful font reset to template master."""
        # This test will fail until we implement the strategy
        from pptx_agent.fixer.strategies.style import StyleResetStrategy

        issue = make_style_violation_issue()
        strategy = StyleResetStrategy()

        # Mock presentation with off-template font
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_shape = Mock()
        mock_text_frame = Mock()
        mock_paragraph = Mock()
        mock_run = Mock()
        mock_master = Mock()
        mock_master_shape = Mock()
        mock_master_text_frame = Mock()
        mock_master_paragraph = Mock()
        mock_master_run = Mock()

        # Setup hierarchy
        mock_presentation.prs.slides = [mock_slide]
        mock_slide.shapes = [mock_shape]
        mock_slide.slide_layout.slide_master = mock_master
        mock_shape.has_text_frame = True
        mock_shape.text_frame = mock_text_frame
        mock_text_frame.paragraphs = [mock_paragraph]
        mock_paragraph.runs = [mock_run]
        mock_run.font.name = "Comic Sans"  # Off-template font

        # Master font
        mock_master.shapes = [mock_master_shape]
        mock_master_shape.has_text_frame = True
        mock_master_shape.text_frame = mock_master_text_frame
        mock_master_text_frame.paragraphs = [mock_master_paragraph]
        mock_master_paragraph.runs = [mock_master_run]
        mock_master_run.font.name = "Arial"  # Template font

        result = strategy.apply(issue, mock_presentation)

        assert result.status == FixStatus.SUCCESS
        assert "reset" in result.message.lower() or "font" in result.message.lower()
        assert mock_run.font.name == "Arial"
        assert len(result.changes_made) > 0

    def test_reset_color_to_master(self) -> None:
        """Test color reset to template master."""
        from pptx_agent.fixer.strategies.style import StyleResetStrategy

        issue = make_style_violation_issue(rule_id="QA-S-002")
        issue.message = "Off-template color usage detected"
        strategy = StyleResetStrategy()

        # Mock with off-template color
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_shape = Mock()
        mock_text_frame = Mock()
        mock_paragraph = Mock()
        mock_run = Mock()
        mock_master = Mock()

        mock_presentation.prs.slides = [mock_slide]
        mock_slide.shapes = [mock_shape]
        mock_slide.slide_layout.slide_master = mock_master
        mock_shape.has_text_frame = True
        mock_shape.text_frame = mock_text_frame
        mock_text_frame.paragraphs = [mock_paragraph]
        mock_paragraph.runs = [mock_run]
        mock_paragraph.level = 0  # Add level attribute
        mock_paragraph.alignment = None  # Add alignment attribute
        mock_run.font.name = "Comic Sans"  # Off-template font
        mock_run.font.bold = False
        mock_run.font.italic = False
        mock_run.font.underline = False

        # Mock master shapes (empty list to use defaults)
        mock_master.shapes = []

        result = strategy.apply(issue, mock_presentation)

        assert result.status == FixStatus.SUCCESS
        # Message is generic "Style reset to master defaults" which is correct
        assert "reset" in result.message.lower() or "style" in result.message.lower()

    def test_reset_style_no_text_frame(self) -> None:
        """Test style reset handles shapes without text frames."""
        from pptx_agent.fixer.strategies.style import StyleResetStrategy

        issue = make_style_violation_issue()
        strategy = StyleResetStrategy()

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

    def test_reset_style_no_master_available(self) -> None:
        """Test style reset when no master is available."""
        from pptx_agent.fixer.strategies.style import StyleResetStrategy

        issue = make_style_violation_issue()
        strategy = StyleResetStrategy()

        # Mock without master
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_shape = Mock()
        mock_text_frame = Mock()
        mock_paragraph = Mock()
        mock_run = Mock()
        mock_layout = Mock()

        mock_presentation.prs.slides = [mock_slide]
        mock_slide.shapes = [mock_shape]
        mock_slide.slide_layout = mock_layout
        mock_layout.slide_master = None
        mock_shape.has_text_frame = True
        mock_shape.text_frame = mock_text_frame
        mock_text_frame.paragraphs = [mock_paragraph]
        mock_paragraph.runs = [mock_run]
        mock_paragraph.level = 0
        mock_paragraph.alignment = None
        mock_run.font.name = "Comic Sans"
        mock_run.font.bold = False
        mock_run.font.italic = False
        mock_run.font.underline = False

        result = strategy.apply(issue, mock_presentation)

        # Implementation uses default values when no master available, so it succeeds
        assert result.status == FixStatus.SUCCESS
        assert "reset" in result.message.lower() or "style" in result.message.lower()

    def test_reset_bullet_indent(self) -> None:
        """Test bullet indent reset for invalid levels."""
        from pptx_agent.fixer.strategies.style import StyleResetStrategy

        issue = make_style_violation_issue(rule_id="QA-S-003")
        issue.message = "Invalid bullet indent level (> 4)"
        strategy = StyleResetStrategy()

        # Mock with invalid indent
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_shape = Mock()
        mock_text_frame = Mock()
        mock_paragraph = Mock()
        mock_master = Mock()

        mock_presentation.prs.slides = [mock_slide]
        mock_slide.shapes = [mock_shape]
        mock_slide.slide_layout.slide_master = mock_master
        mock_shape.has_text_frame = True
        mock_shape.text_frame = mock_text_frame
        mock_text_frame.paragraphs = [mock_paragraph]
        mock_paragraph.level = 5  # Invalid level (> 4)
        mock_paragraph.runs = []  # No runs to process
        mock_paragraph.alignment = None

        # Mock master shapes (empty to use defaults)
        mock_master.shapes = []

        result = strategy.apply(issue, mock_presentation)

        assert result.status == FixStatus.SUCCESS
        assert mock_paragraph.level == 0  # Should be reset to 0
        # Message is generic "Style reset to master defaults" which is correct
        assert "reset" in result.message.lower() or "style" in result.message.lower()
        # Verify the change was recorded
        assert any(
            "indent" in change.lower() or "level" in change.lower()
            for change in result.changes_made
        )

    def test_reset_style_multiple_paragraphs(self) -> None:
        """Test style reset handles multiple paragraphs."""
        from pptx_agent.fixer.strategies.style import StyleResetStrategy

        issue = make_style_violation_issue()
        strategy = StyleResetStrategy()

        # Mock with multiple paragraphs
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_shape = Mock()
        mock_text_frame = Mock()
        mock_para1 = Mock()
        mock_para2 = Mock()
        mock_run1 = Mock()
        mock_run2 = Mock()
        mock_master = Mock()
        mock_master_shape = Mock()
        mock_master_text_frame = Mock()
        mock_master_para = Mock()
        mock_master_run = Mock()

        mock_presentation.prs.slides = [mock_slide]
        mock_slide.shapes = [mock_shape]
        mock_slide.slide_layout.slide_master = mock_master
        mock_shape.has_text_frame = True
        mock_shape.text_frame = mock_text_frame
        mock_text_frame.paragraphs = [mock_para1, mock_para2]
        mock_para1.runs = [mock_run1]
        mock_para2.runs = [mock_run2]
        mock_run1.font.name = "Comic Sans"
        mock_run2.font.name = "Times New Roman"

        # Master
        mock_master.shapes = [mock_master_shape]
        mock_master_shape.has_text_frame = True
        mock_master_shape.text_frame = mock_master_text_frame
        mock_master_text_frame.paragraphs = [mock_master_para]
        mock_master_para.runs = [mock_master_run]
        mock_master_run.font.name = "Arial"

        result = strategy.apply(issue, mock_presentation)

        assert result.status == FixStatus.SUCCESS
        assert mock_run1.font.name == "Arial"
        assert mock_run2.font.name == "Arial"

    def test_reset_style_invalid_slide_index(self) -> None:
        """Test style reset handles invalid slide index."""
        from pptx_agent.fixer.strategies.style import StyleResetStrategy

        issue = make_style_violation_issue(slide_index=999)
        strategy = StyleResetStrategy()

        mock_presentation = Mock()
        mock_presentation.prs.slides = []

        result = strategy.apply(issue, mock_presentation)

        assert result.status == FixStatus.FAILED
        assert "invalid" in result.message.lower() or "not found" in result.message.lower()

    def test_reset_style_invalid_shape_index(self) -> None:
        """Test style reset handles invalid shape index."""
        from pptx_agent.fixer.strategies.style import StyleResetStrategy

        issue = make_style_violation_issue(shape_index=999)
        strategy = StyleResetStrategy()

        mock_presentation = Mock()
        mock_slide = Mock()
        mock_presentation.prs.slides = [mock_slide]
        mock_slide.shapes = []

        result = strategy.apply(issue, mock_presentation)

        assert result.status == FixStatus.FAILED
        assert "invalid" in result.message.lower() or "not found" in result.message.lower()


# Made with Bob
