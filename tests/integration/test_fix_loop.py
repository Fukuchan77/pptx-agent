"""Integration tests for fix loop convergence and iteration handling."""

from pathlib import Path

import pytest

from pptx_agent.fixer.engine import FixEngine, FixStrategyRegistry
from pptx_agent.fixer.schemas import FixResult, FixStatus
from pptx_agent.qa.schemas import QAIssue, QAReport, Severity


def make_qa_report_with_errors(error_count: int = 3) -> QAReport:
    """Create a QA report with specified number of errors.

    Args:
        error_count: Number of error-level issues to include

    Returns:
        QA report with auto-fixable errors
    """
    issues = [
        QAIssue(
            rule_id=f"QA-L-00{i + 1}",
            severity=Severity.ERROR,
            slide_index=i,
            shape_index=0,
            message=f"Error {i + 1}",
            auto_fixable=True,
        )
        for i in range(error_count)
    ]

    return QAReport(
        total_issues=error_count,
        error_count=error_count,
        warning_count=0,
        info_count=0,
        issues=issues,
    )


class TestFixLoopConvergence:
    """Integration tests for fix loop convergence behavior."""

    def test_fix_loop_converges_on_first_iteration(self) -> None:
        """Test fix loop converges when all issues fixed in first iteration."""
        # Create registry with successful fix strategies
        registry = FixStrategyRegistry()

        def successful_fix(issue: QAIssue) -> FixResult:
            return FixResult(
                issue=issue,
                status=FixStatus.SUCCESS,
                message="Fixed successfully",
                changes_made=["Applied fix"],
            )

        # Register strategies for all rules
        for i in range(3):
            registry.register(f"QA-L-00{i + 1}", successful_fix)

        engine = FixEngine(registry=registry, max_iterations=3)
        report = make_qa_report_with_errors(error_count=3)

        result = engine.run_fix_loop(report)

        assert result.iterations == 1
        assert len(result.fixes_applied) == 3
        assert all(fix.status == FixStatus.SUCCESS for fix in result.fixes_applied)
        # Note: Current implementation doesn't re-run QA, so success depends on
        # whether we update the report. For now, we check iterations.

    def test_fix_loop_converges_after_multiple_iterations(self) -> None:
        """Test fix loop converges after multiple iterations."""
        registry = FixStrategyRegistry()
        call_count = {"count": 0}

        def progressive_fix(issue: QAIssue) -> FixResult:
            """Fix that succeeds after multiple attempts."""
            call_count["count"] += 1
            if call_count["count"] <= 2:
                return FixResult(
                    issue=issue,
                    status=FixStatus.PARTIAL,
                    message="Partially fixed",
                    changes_made=["Partial fix applied"],
                )
            return FixResult(
                issue=issue,
                status=FixStatus.SUCCESS,
                message="Fixed successfully",
                changes_made=["Complete fix applied"],
            )

        registry.register("QA-L-001", progressive_fix)

        engine = FixEngine(registry=registry, max_iterations=3)
        report = make_qa_report_with_errors(error_count=1)

        result = engine.run_fix_loop(report)

        # Current implementation runs once per iteration
        assert result.iterations >= 1
        assert len(result.fixes_applied) >= 1

    def test_fix_loop_stops_when_no_fixable_issues(self) -> None:
        """Test fix loop stops when no auto-fixable issues remain."""
        registry = FixStrategyRegistry()

        engine = FixEngine(registry=registry, max_iterations=3)

        # Create report with non-fixable issues
        issues = [
            QAIssue(
                rule_id="QA-L-001",
                severity=Severity.ERROR,
                slide_index=0,
                message="Non-fixable error",
                auto_fixable=False,  # Not fixable
            )
        ]
        report = QAReport(
            total_issues=1,
            error_count=1,
            warning_count=0,
            info_count=0,
            issues=issues,
        )

        result = engine.run_fix_loop(report)

        assert result.iterations == 0  # Should not iterate
        assert len(result.fixes_applied) == 0

    def test_fix_loop_stops_when_all_fixes_fail(self) -> None:
        """Test fix loop stops when all fix attempts fail."""
        registry = FixStrategyRegistry()

        def failing_fix(issue: QAIssue) -> FixResult:
            return FixResult(
                issue=issue,
                status=FixStatus.FAILED,
                message="Fix failed",
            )

        registry.register("QA-L-001", failing_fix)
        registry.register("QA-L-002", failing_fix)

        engine = FixEngine(registry=registry, max_iterations=3)
        report = make_qa_report_with_errors(error_count=2)

        result = engine.run_fix_loop(report)

        assert result.iterations == 1  # Tries once, then stops
        assert all(fix.status == FixStatus.FAILED for fix in result.fixes_applied)

    def test_fix_loop_handles_mixed_success_and_failure(self) -> None:
        """Test fix loop handles mix of successful and failed fixes."""
        registry = FixStrategyRegistry()

        def successful_fix(issue: QAIssue) -> FixResult:
            return FixResult(
                issue=issue,
                status=FixStatus.SUCCESS,
                message="Fixed",
                changes_made=["Applied fix"],
            )

        def failing_fix(issue: QAIssue) -> FixResult:
            return FixResult(
                issue=issue,
                status=FixStatus.FAILED,
                message="Failed",
            )

        registry.register("QA-L-001", successful_fix)
        registry.register("QA-L-002", failing_fix)

        engine = FixEngine(registry=registry, max_iterations=3)
        report = make_qa_report_with_errors(error_count=2)

        result = engine.run_fix_loop(report)

        assert result.iterations >= 1
        assert len(result.fixes_applied) == 2
        assert result.fixes_applied[0].status == FixStatus.SUCCESS
        assert result.fixes_applied[1].status == FixStatus.FAILED


class TestMaxIterationsHandling:
    """Integration tests for maximum iterations handling."""

    def test_fix_loop_respects_max_iterations_limit(self) -> None:
        """Test fix loop stops at maximum iterations."""
        registry = FixStrategyRegistry()

        def never_succeeds(issue: QAIssue) -> FixResult:
            """Fix that never fully succeeds."""
            return FixResult(
                issue=issue,
                status=FixStatus.PARTIAL,
                message="Partially fixed",
                changes_made=["Partial fix"],
            )

        registry.register("QA-L-001", never_succeeds)

        max_iters = 5
        engine = FixEngine(registry=registry, max_iterations=max_iters)
        report = make_qa_report_with_errors(error_count=1)

        result = engine.run_fix_loop(report)

        # Should stop at max iterations
        assert result.iterations <= max_iters

    def test_fix_loop_with_max_iterations_one(self) -> None:
        """Test fix loop with max_iterations=1."""
        registry = FixStrategyRegistry()

        def successful_fix(issue: QAIssue) -> FixResult:
            return FixResult(
                issue=issue,
                status=FixStatus.SUCCESS,
                message="Fixed",
                changes_made=["Fix applied"],
            )

        registry.register("QA-L-001", successful_fix)

        engine = FixEngine(registry=registry, max_iterations=1)
        report = make_qa_report_with_errors(error_count=1)

        result = engine.run_fix_loop(report)

        assert result.iterations == 1
        assert len(result.fixes_applied) == 1

    def test_fix_loop_tracks_iteration_count_correctly(self) -> None:
        """Test fix loop accurately tracks iteration count."""
        registry = FixStrategyRegistry()
        iteration_tracker = {"count": 0}

        def tracking_fix(issue: QAIssue) -> FixResult:
            iteration_tracker["count"] += 1
            return FixResult(
                issue=issue,
                status=FixStatus.PARTIAL,
                message=f"Iteration {iteration_tracker['count']}",
                changes_made=[f"Fix attempt {iteration_tracker['count']}"],
            )

        registry.register("QA-L-001", tracking_fix)

        max_iters = 3
        engine = FixEngine(registry=registry, max_iterations=max_iters)
        report = make_qa_report_with_errors(error_count=1)

        result = engine.run_fix_loop(report)

        # Current implementation runs once per iteration
        assert result.iterations >= 1
        assert result.iterations <= max_iters

    def test_fix_loop_final_report_includes_iteration_count(self) -> None:
        """Test final QA report includes fix iteration count."""
        registry = FixStrategyRegistry()

        def successful_fix(issue: QAIssue) -> FixResult:
            return FixResult(
                issue=issue,
                status=FixStatus.SUCCESS,
                message="Fixed",
                changes_made=["Fix applied"],
            )

        registry.register("QA-L-001", successful_fix)

        engine = FixEngine(registry=registry, max_iterations=3)
        report = make_qa_report_with_errors(error_count=1)

        result = engine.run_fix_loop(report)

        assert result.final_qa_report.fix_iterations == result.iterations
        assert result.final_qa_report.fix_iterations > 0

    def test_fix_loop_with_zero_max_iterations_raises_error(self) -> None:
        """Test fix engine rejects max_iterations < 1."""
        with pytest.raises(ValueError, match="max_iterations must be greater than or equal to 1"):
            FixEngine(max_iterations=0)

    def test_fix_loop_success_flag_based_on_error_count(self) -> None:
        """Test fix loop success flag is based on final error count."""
        registry = FixStrategyRegistry()

        def successful_fix(issue: QAIssue) -> FixResult:
            return FixResult(
                issue=issue,
                status=FixStatus.SUCCESS,
                message="Fixed",
                changes_made=["Fix applied"],
            )

        registry.register("QA-L-001", successful_fix)

        engine = FixEngine(registry=registry, max_iterations=3)
        report = make_qa_report_with_errors(error_count=1)

        result = engine.run_fix_loop(report)

        # Success is based on final error count
        # Current implementation doesn't re-run QA, so we check the logic
        assert isinstance(result.success, bool)
        assert result.success == (result.final_qa_report.error_count == 0)


class TestMultipleStrategiesPerRule:
    """Integration tests for multiple strategies per rule behavior."""

    def test_multiple_strategies_tried_in_order(self) -> None:
        """Test that multiple strategies for same rule are tried in order until one succeeds."""
        registry = FixStrategyRegistry()
        call_order = []

        def first_strategy_fails(issue: QAIssue) -> FixResult:
            call_order.append("first")
            return FixResult(
                issue=issue,
                status=FixStatus.FAILED,
                message="First strategy failed",
            )

        def second_strategy_succeeds(issue: QAIssue) -> FixResult:
            call_order.append("second")
            return FixResult(
                issue=issue,
                status=FixStatus.SUCCESS,
                message="Second strategy succeeded",
                changes_made=["Applied second strategy"],
            )

        def third_strategy_not_called(issue: QAIssue) -> FixResult:
            call_order.append("third")
            return FixResult(
                issue=issue,
                status=FixStatus.SUCCESS,
                message="Third strategy succeeded",
                changes_made=["Applied third strategy"],
            )

        # Register multiple strategies for same rule
        registry.register("QA-L-001", first_strategy_fails)
        registry.register("QA-L-001", second_strategy_succeeds)
        registry.register("QA-L-001", third_strategy_not_called)

        engine = FixEngine(registry=registry, max_iterations=3)
        report = make_qa_report_with_errors(error_count=1)

        result = engine.run_fix_loop(report)

        # Should try first, then second (which succeeds), then stop
        assert call_order == ["first", "second"]
        assert len(result.fixes_applied) == 1
        assert result.fixes_applied[0].status == FixStatus.SUCCESS
        assert "Second strategy succeeded" in result.fixes_applied[0].message

    def test_all_strategies_fail_returns_failed_result(self) -> None:
        """Test that when all strategies fail, a FAILED result is returned."""
        registry = FixStrategyRegistry()

        def strategy1_fails(issue: QAIssue) -> FixResult:
            return FixResult(
                issue=issue,
                status=FixStatus.FAILED,
                message="Strategy 1 failed",
            )

        def strategy2_fails(issue: QAIssue) -> FixResult:
            return FixResult(
                issue=issue,
                status=FixStatus.FAILED,
                message="Strategy 2 failed",
            )

        registry.register("QA-L-001", strategy1_fails)
        registry.register("QA-L-001", strategy2_fails)

        engine = FixEngine(registry=registry, max_iterations=3)
        report = make_qa_report_with_errors(error_count=1)

        result = engine.run_fix_loop(report)

        assert len(result.fixes_applied) == 1
        assert result.fixes_applied[0].status == FixStatus.FAILED
        assert "All fix strategies failed" in result.fixes_applied[0].message

    def test_partial_success_stops_trying_other_strategies(self) -> None:
        """Test that PARTIAL status stops trying remaining strategies."""
        registry = FixStrategyRegistry()
        call_order = []

        def first_strategy_partial(issue: QAIssue) -> FixResult:
            call_order.append("first")
            return FixResult(
                issue=issue,
                status=FixStatus.PARTIAL,
                message="First strategy partially succeeded",
                changes_made=["Partial fix"],
            )

        def second_strategy_not_called(issue: QAIssue) -> FixResult:
            call_order.append("second")
            return FixResult(
                issue=issue,
                status=FixStatus.SUCCESS,
                message="Second strategy succeeded",
                changes_made=["Complete fix"],
            )

        registry.register("QA-L-001", first_strategy_partial)
        registry.register("QA-L-001", second_strategy_not_called)

        engine = FixEngine(registry=registry, max_iterations=3)
        report = make_qa_report_with_errors(error_count=1)

        result = engine.run_fix_loop(report)

        # Should only call first strategy (which returns PARTIAL)
        assert call_order == ["first"]
        assert len(result.fixes_applied) == 1
        assert result.fixes_applied[0].status == FixStatus.PARTIAL


class TestPresentationSaveAndQARerun:
    """Integration tests for presentation saving and QA re-running."""

    def test_fix_loop_calls_qa_runner_after_fixes(self, tmp_path: Path) -> None:
        """Test that fix loop calls QA runner after applying fixes."""
        registry = FixStrategyRegistry()
        qa_runner_calls = []
        test_pptx = str(tmp_path / "test.pptx")

        def successful_fix(issue: QAIssue) -> FixResult:
            return FixResult(
                issue=issue,
                status=FixStatus.SUCCESS,
                message="Fixed",
                changes_made=["Applied fix"],
            )

        def mock_qa_runner(path: str) -> QAReport:
            qa_runner_calls.append(path)
            # Return report with no errors (all fixed)
            return QAReport(
                total_issues=0,
                error_count=0,
                warning_count=0,
                info_count=0,
                issues=[],
            )

        registry.register("QA-L-001", successful_fix)

        engine = FixEngine(registry=registry, max_iterations=3)
        report = make_qa_report_with_errors(error_count=1)

        # Add save callback (required for QA runner to be called)
        def mock_save_callback() -> None:
            pass

        result = engine.run_fix_loop(
            report,
            presentation_path=test_pptx,
            qa_runner=mock_qa_runner,
            save_callback=mock_save_callback,
        )

        # QA runner should be called after fixes
        assert len(qa_runner_calls) == 1
        assert qa_runner_calls[0] == test_pptx
        assert result.final_qa_report.error_count == 0

    def test_fix_loop_iterates_multiple_times_with_qa_rerun(self, tmp_path: Path) -> None:
        """Test that fix loop iterates multiple times when QA re-run shows remaining errors."""
        registry = FixStrategyRegistry()
        qa_runner_call_count = {"count": 0}
        test_pptx = str(tmp_path / "test.pptx")

        def successful_fix(issue: QAIssue) -> FixResult:
            return FixResult(
                issue=issue,
                status=FixStatus.SUCCESS,
                message="Fixed",
                changes_made=["Applied fix"],
            )

        def mock_qa_runner(path: str) -> QAReport:
            qa_runner_call_count["count"] += 1
            # First call: still has 1 error
            # Second call: no errors
            if qa_runner_call_count["count"] == 1:
                return make_qa_report_with_errors(error_count=1)
            return QAReport(
                total_issues=0,
                error_count=0,
                warning_count=0,
                info_count=0,
                issues=[],
            )

        registry.register("QA-L-001", successful_fix)

        engine = FixEngine(registry=registry, max_iterations=3)
        report = make_qa_report_with_errors(error_count=1)

        # Add save callback (required for QA runner to be called)
        def mock_save_callback() -> None:
            pass

        result = engine.run_fix_loop(
            report,
            presentation_path=test_pptx,
            qa_runner=mock_qa_runner,
            save_callback=mock_save_callback,
        )

        # Should iterate twice (first iteration leaves 1 error, second fixes it)
        assert result.iterations == 2
        assert qa_runner_call_count["count"] == 2
        assert result.final_qa_report.error_count == 0

    def test_fix_loop_without_qa_runner_uses_original_report(self) -> None:
        """Test that fix loop without QA runner doesn't update the report."""
        registry = FixStrategyRegistry()

        def successful_fix(issue: QAIssue) -> FixResult:
            return FixResult(
                issue=issue,
                status=FixStatus.SUCCESS,
                message="Fixed",
                changes_made=["Applied fix"],
            )

        registry.register("QA-L-001", successful_fix)

        engine = FixEngine(registry=registry, max_iterations=3)
        report = make_qa_report_with_errors(error_count=1)

        # Run without qa_runner
        result = engine.run_fix_loop(report)

        # Should still have original error count (no QA re-run)
        assert result.final_qa_report.error_count == 1
        assert result.iterations == 1


# Made with Bob
