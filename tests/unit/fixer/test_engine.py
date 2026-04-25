"""Unit tests for fixer engine."""

import pytest

from pptx_agent.fixer.engine import FixEngine, FixStrategyRegistry
from pptx_agent.fixer.schemas import FixResult, FixStatus
from pptx_agent.qa.schemas import QAIssue, QAReport, Severity


def make_issue(
    rule_id: str = "QA-L-001",
    *,
    auto_fixable: bool = True,
) -> QAIssue:
    """Create a QA issue for fixer tests.

    Args:
        rule_id: Rule identifier for the issue
        auto_fixable: Whether the issue can be automatically fixed

    Returns:
        QA issue instance
    """
    return QAIssue(
        rule_id=rule_id,
        severity=Severity.ERROR,
        slide_index=0,
        message="Overflow detected",
        auto_fixable=auto_fixable,
    )


def make_fix_result(issue: QAIssue, status: FixStatus = FixStatus.SUCCESS) -> FixResult:
    """Create a fix result for a QA issue.

    Args:
        issue: Issue associated with the result
        status: Fix operation status

    Returns:
        Structured fix result
    """
    return FixResult(
        issue=issue,
        status=status,
        message="Fix applied",
    )


def test_registry_register_and_get_strategy() -> None:
    """Test strategy registration and retrieval."""
    registry = FixStrategyRegistry()

    def strategy(issue: QAIssue) -> FixResult:
        return make_fix_result(issue)

    registry.register("QA-L-001", strategy)

    assert "QA-L-001" in registry
    assert len(registry) == 1
    assert registry.get_strategy("QA-L-001") is strategy


def test_registry_rejects_duplicate_rule_id() -> None:
    """Test duplicate strategy registration raises error."""
    registry = FixStrategyRegistry()

    def strategy(issue: QAIssue) -> FixResult:
        return make_fix_result(issue)

    registry.register("QA-L-001", strategy)

    with pytest.raises(ValueError, match="already registered"):
        registry.register("QA-L-001", strategy)


def test_registry_unregister_existing_rule() -> None:
    """Test unregister removes an existing strategy."""
    registry = FixStrategyRegistry()

    def strategy(issue: QAIssue) -> FixResult:
        return make_fix_result(issue)

    registry.register("QA-L-001", strategy)

    assert registry.unregister("QA-L-001") is True
    assert "QA-L-001" not in registry
    assert len(registry) == 0


def test_engine_rejects_invalid_iteration_count() -> None:
    """Test engine validates max iteration configuration."""
    with pytest.raises(ValueError, match="greater than or equal to 1"):
        FixEngine(max_iterations=0)


def test_apply_fix_skips_non_autofixable_issue() -> None:
    """Test single fix skips non auto-fixable issues."""
    engine = FixEngine(registry=FixStrategyRegistry())
    issue = make_issue(auto_fixable=False)

    result = engine.apply_fix(issue)

    assert result.status == FixStatus.SKIPPED
    assert "not marked as auto-fixable" in result.message


def test_apply_fix_skips_when_no_strategy_registered() -> None:
    """Test single fix skips issues without a registered strategy."""
    engine = FixEngine(registry=FixStrategyRegistry())
    issue = make_issue()

    result = engine.apply_fix(issue)

    assert result.status == FixStatus.SKIPPED
    assert "No fix strategy registered" in result.message


def test_apply_fix_returns_strategy_result() -> None:
    """Test single fix delegates to registered strategy."""
    registry = FixStrategyRegistry()
    issue = make_issue()

    def strategy(current_issue: QAIssue) -> FixResult:
        return FixResult(
            issue=current_issue,
            status=FixStatus.SUCCESS,
            message="Reduced font size",
            changes_made=["Reduced font size from 18pt to 16pt"],
        )

    registry.register(issue.rule_id, strategy)
    engine = FixEngine(registry=registry)

    result = engine.apply_fix(issue)

    assert result.status == FixStatus.SUCCESS
    assert result.changes_made == ["Reduced font size from 18pt to 16pt"]


def test_apply_fix_handles_strategy_exception() -> None:
    """Test single fix converts strategy exceptions into failed results."""
    registry = FixStrategyRegistry()
    issue = make_issue()

    def failing_strategy(current_issue: QAIssue) -> FixResult:
        msg = "boom"
        raise RuntimeError(msg)

    registry.register(issue.rule_id, failing_strategy)
    engine = FixEngine(registry=registry)

    result = engine.apply_fix(issue)

    assert result.status == FixStatus.FAILED
    assert result.message == "Fix strategy failed: boom"


def test_run_fix_loop_applies_registered_strategies_once() -> None:
    """Test fix loop applies fixable issue strategies."""
    registry = FixStrategyRegistry()
    issue = make_issue()

    def strategy(current_issue: QAIssue) -> FixResult:
        return FixResult(
            issue=current_issue,
            status=FixStatus.SUCCESS,
            message="Reduced font size",
        )

    registry.register(issue.rule_id, strategy)
    engine = FixEngine(registry=registry, max_iterations=3)
    report = QAReport(
        total_issues=1,
        error_count=1,
        issues=[issue],
    )

    result = engine.run_fix_loop(report)

    assert result.iterations == 1
    assert len(result.fixes_applied) == 1
    assert result.fixes_applied[0].status == FixStatus.SUCCESS
    assert result.final_qa_report.fix_iterations == 1
    assert result.success is False


def test_run_fix_loop_stops_when_no_fixable_issues_exist() -> None:
    """Test fix loop exits without iterations when nothing is fixable."""
    engine = FixEngine(registry=FixStrategyRegistry(), max_iterations=3)
    report = QAReport(
        total_issues=1,
        error_count=1,
        issues=[make_issue(auto_fixable=False)],
    )

    result = engine.run_fix_loop(report)

    assert result.iterations == 0
    assert result.fixes_applied == []
    assert result.final_qa_report.fix_iterations == 0
    assert result.success is False


def test_run_fix_loop_stops_after_failed_or_skipped_iteration() -> None:
    """Test fix loop stops when an iteration makes no progress."""
    registry = FixStrategyRegistry()
    issue = make_issue()

    def strategy(current_issue: QAIssue) -> FixResult:
        return FixResult(
            issue=current_issue,
            status=FixStatus.FAILED,
            message="Could not fix",
        )

    registry.register(issue.rule_id, strategy)
    engine = FixEngine(registry=registry, max_iterations=3)
    report = QAReport(
        total_issues=1,
        error_count=1,
        issues=[issue],
    )

    result = engine.run_fix_loop(report)

    assert result.iterations == 1
    assert len(result.fixes_applied) == 1
    assert result.fixes_applied[0].status == FixStatus.FAILED


# Made with Bob
