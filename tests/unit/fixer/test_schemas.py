"""Unit tests for fixer schemas."""

import pytest

from pptx_agent.fixer.schemas import FixLoopResult, FixResult, FixStatus
from pptx_agent.qa.schemas import QAIssue, QAReport, Severity


def make_issue(*, auto_fixable: bool = True) -> QAIssue:
    """Create a reusable QA issue fixture.

    Args:
        auto_fixable: Whether the issue should be marked auto-fixable

    Returns:
        QA issue instance for fixer tests
    """
    return QAIssue(
        rule_id="QA-L-001",
        severity=Severity.ERROR,
        slide_index=0,
        message="Overflow detected",
        auto_fixable=auto_fixable,
    )


def test_fix_status_enum_values() -> None:
    """Test FixStatus enum has expected values."""
    assert FixStatus.SUCCESS == "success"
    assert FixStatus.PARTIAL == "partial"
    assert FixStatus.FAILED == "failed"
    assert FixStatus.SKIPPED == "skipped"


def test_fix_result_creation() -> None:
    """Test creating a fix result with required fields."""
    issue = make_issue()
    result = FixResult(
        issue=issue,
        status=FixStatus.SUCCESS,
        message="Reduced font size",
    )

    assert result.issue == issue
    assert result.status == FixStatus.SUCCESS
    assert result.message == "Reduced font size"
    assert result.changes_made == []


def test_fix_result_with_changes() -> None:
    """Test fix result captures applied changes."""
    result = FixResult(
        issue=make_issue(),
        status=FixStatus.PARTIAL,
        message="Applied partial fix",
        changes_made=["Reduced font size from 18pt to 16pt"],
    )

    assert result.changes_made == ["Reduced font size from 18pt to 16pt"]


def test_fix_loop_result_creation() -> None:
    """Test creating a fix loop result."""
    issue = make_issue()
    fix_result = FixResult(
        issue=issue,
        status=FixStatus.SUCCESS,
        message="Fixed overflow",
    )
    report = QAReport(total_issues=0)

    loop_result = FixLoopResult(
        iterations=1,
        fixes_applied=[fix_result],
        final_qa_report=report,
        success=True,
    )

    assert loop_result.iterations == 1
    assert loop_result.fixes_applied == [fix_result]
    assert loop_result.final_qa_report == report
    assert loop_result.success is True


def test_fix_loop_result_validation_negative_iterations() -> None:
    """Test fix loop result rejects negative iterations."""
    with pytest.raises(ValueError, match="greater than or equal to 0"):
        FixLoopResult(
            iterations=-1,
            fixes_applied=[],
            final_qa_report=QAReport(),
            success=False,
        )


# Made with Bob
