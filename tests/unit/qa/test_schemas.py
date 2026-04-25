"""Unit tests for QA schemas."""

import pytest

from pptx_agent.qa.schemas import QAIssue, QAReport, Severity


def test_severity_enum_values() -> None:
    """Test Severity enum has correct values."""
    assert Severity.ERROR == "error"
    assert Severity.WARNING == "warning"
    assert Severity.INFO == "info"


def test_qa_issue_creation() -> None:
    """Test creating QA issue with required fields."""
    issue = QAIssue(
        rule_id="QA-L-001",
        severity=Severity.ERROR,
        slide_index=0,
        message="Test issue",
    )

    assert issue.rule_id == "QA-L-001"
    assert issue.severity == Severity.ERROR
    assert issue.slide_index == 0
    assert issue.shape_index is None
    assert issue.message == "Test issue"
    assert issue.auto_fixable is False
    assert issue.suggested_fix is None


def test_qa_issue_with_shape_index() -> None:
    """Test QA issue with shape-level location."""
    issue = QAIssue(
        rule_id="QA-L-002",
        severity=Severity.WARNING,
        slide_index=1,
        shape_index=3,
        message="Shape issue",
    )

    assert issue.slide_index == 1
    assert issue.shape_index == 3


def test_qa_issue_auto_fixable() -> None:
    """Test QA issue marked as auto-fixable."""
    issue = QAIssue(
        rule_id="QA-L-003",
        severity=Severity.ERROR,
        slide_index=0,
        message="Auto-fixable issue",
        auto_fixable=True,
    )

    assert issue.auto_fixable is True
    assert issue.suggested_fix is None


def test_qa_issue_with_suggested_fix() -> None:
    """Test QA issue with manual fix suggestion."""
    issue = QAIssue(
        rule_id="QA-L-004",
        severity=Severity.WARNING,
        slide_index=2,
        message="Manual fix needed",
        suggested_fix="Reduce text by 20%",
    )

    assert issue.suggested_fix == "Reduce text by 20%"


def test_qa_issue_validation_negative_slide_index() -> None:
    """Test QA issue rejects negative slide index."""
    with pytest.raises(ValueError, match="greater than or equal to 0"):
        QAIssue(
            rule_id="QA-L-005",
            severity=Severity.ERROR,
            slide_index=-1,
            message="Invalid slide index",
        )


def test_qa_issue_validation_negative_shape_index() -> None:
    """Test QA issue rejects negative shape index."""
    with pytest.raises(ValueError, match="greater than or equal to 0"):
        QAIssue(
            rule_id="QA-L-006",
            severity=Severity.ERROR,
            slide_index=0,
            shape_index=-1,
            message="Invalid shape index",
        )


def test_qa_report_empty() -> None:
    """Test creating empty QA report."""
    report = QAReport()

    assert report.total_issues == 0
    assert report.error_count == 0
    assert report.warning_count == 0
    assert report.info_count == 0
    assert len(report.issues) == 0
    assert report.fix_iterations == 0
    assert report.passed is True


def test_qa_report_with_issues() -> None:
    """Test QA report with multiple issues."""
    issues = [
        QAIssue(
            rule_id="QA-L-001",
            severity=Severity.ERROR,
            slide_index=0,
            message="Error 1",
        ),
        QAIssue(
            rule_id="QA-L-002",
            severity=Severity.ERROR,
            slide_index=1,
            message="Error 2",
        ),
        QAIssue(
            rule_id="QA-L-003",
            severity=Severity.WARNING,
            slide_index=2,
            message="Warning 1",
        ),
        QAIssue(
            rule_id="QA-L-004",
            severity=Severity.INFO,
            slide_index=3,
            message="Info 1",
        ),
    ]

    report = QAReport(
        total_issues=4,
        error_count=2,
        warning_count=1,
        info_count=1,
        issues=issues,
    )

    assert report.total_issues == 4
    assert report.error_count == 2
    assert report.warning_count == 1
    assert report.info_count == 1
    assert len(report.issues) == 4
    assert report.passed is False  # Has errors


def test_qa_report_passed_with_warnings() -> None:
    """Test QA report passes with warnings but no errors."""
    issues = [
        QAIssue(
            rule_id="QA-L-001",
            severity=Severity.WARNING,
            slide_index=0,
            message="Warning",
        ),
    ]

    report = QAReport(
        total_issues=1,
        warning_count=1,
        issues=issues,
    )

    assert report.passed is True  # No errors = passed


def test_qa_report_to_json() -> None:
    """Test QA report JSON serialization."""
    issue = QAIssue(
        rule_id="QA-L-001",
        severity=Severity.ERROR,
        slide_index=0,
        message="Test error",
    )

    report = QAReport(
        total_issues=1,
        error_count=1,
        issues=[issue],
    )

    json_str = report.to_json()
    assert isinstance(json_str, str)
    assert "QA-L-001" in json_str
    assert "Test error" in json_str
    assert '"passed": false' in json_str


def test_qa_report_to_markdown_empty() -> None:
    """Test Markdown generation for empty report."""
    report = QAReport()
    markdown = report.to_markdown()

    assert "# QA Report" in markdown
    assert "✅ PASSED" in markdown
    assert "**Total Issues**: 0" in markdown


def test_qa_report_to_markdown_with_errors() -> None:
    """Test Markdown generation with errors."""
    issues = [
        QAIssue(
            rule_id="QA-L-001",
            severity=Severity.ERROR,
            slide_index=0,
            message="Critical error",
            auto_fixable=True,
        ),
    ]

    report = QAReport(
        total_issues=1,
        error_count=1,
        issues=issues,
    )

    markdown = report.to_markdown()
    assert "❌ FAILED" in markdown
    assert "## ❌ Errors" in markdown
    assert "[QA-L-001]" in markdown
    assert "Slide 1" in markdown
    assert "Critical error" in markdown
    assert "(auto-fixable)" in markdown


def test_qa_report_to_markdown_with_warnings() -> None:
    """Test Markdown generation with warnings."""
    issues = [
        QAIssue(
            rule_id="QA-L-002",
            severity=Severity.WARNING,
            slide_index=1,
            shape_index=2,
            message="Minor issue",
            suggested_fix="Manual fix required",
        ),
    ]

    report = QAReport(
        total_issues=1,
        warning_count=1,
        issues=issues,
    )

    markdown = report.to_markdown()
    assert "## ⚠️ Warnings" in markdown
    assert "[QA-L-002]" in markdown
    assert "Slide 2, Shape 3" in markdown  # 1-based display
    assert "Minor issue" in markdown
    assert "*Suggested fix*: Manual fix required" in markdown


def test_qa_report_to_markdown_with_info() -> None:
    """Test Markdown generation with info messages."""
    issues = [
        QAIssue(
            rule_id="QA-L-003",
            severity=Severity.INFO,
            slide_index=0,
            message="Informational message",
        ),
    ]

    report = QAReport(
        total_issues=1,
        info_count=1,
        issues=issues,
    )

    markdown = report.to_markdown()
    assert "## ℹ️ Info" in markdown  # noqa: RUF001
    assert "[QA-L-003]" in markdown
    assert "Informational message" in markdown


def test_qa_report_to_markdown_with_fix_iterations() -> None:
    """Test Markdown includes fix iteration count."""
    report = QAReport(fix_iterations=3)
    markdown = report.to_markdown()

    assert "**Fix Iterations**: 3" in markdown


def test_qa_report_validation_negative_counts() -> None:
    """Test QA report rejects negative counts."""
    with pytest.raises(ValueError, match="greater than or equal to 0"):
        QAReport(total_issues=-1)

    with pytest.raises(ValueError, match="greater than or equal to 0"):
        QAReport(error_count=-1)


# Made with Bob
