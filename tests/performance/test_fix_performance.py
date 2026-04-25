"""Performance profiling tests for fix loop operations.

Tests fix loop convergence time and iteration efficiency to ensure
the system meets performance targets for automatic remediation.
"""

import time

import pytest

from pptx_agent.fixer.engine import FixEngine, FixStrategyRegistry
from pptx_agent.fixer.schemas import FixResult, FixStatus
from pptx_agent.qa.schemas import QAIssue, QAReport, Severity


def make_qa_report_with_errors(error_count: int = 10) -> QAReport:
    """Create a QA report with specified number of auto-fixable errors.

    Args:
        error_count: Number of error-level issues to include

    Returns:
        QA report with auto-fixable errors
    """
    issues = [
        QAIssue(
            rule_id=f"QA-L-00{(i % 6) + 1}",  # Cycle through 6 rule types
            severity=Severity.ERROR,
            slide_index=i,
            shape_index=0,
            message=f"Error {i + 1}: Text overflow detected",
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


@pytest.fixture
def fix_engine_with_strategies() -> FixEngine:
    """Create fix engine with mock strategies registered."""
    registry = FixStrategyRegistry()

    def successful_fix(issue: QAIssue) -> FixResult:
        """Mock fix strategy that always succeeds."""
        # Simulate some work
        time.sleep(0.01)  # 10ms per fix
        return FixResult(
            issue=issue,
            status=FixStatus.SUCCESS,
            message="Fixed successfully",
            changes_made=["Applied fix"],
        )

    # Register strategies for common QA rules
    for i in range(1, 7):
        registry.register(f"QA-L-00{i}", successful_fix)

    return FixEngine(registry=registry, max_iterations=5)


def test_fix_loop_convergence_time_small(
    fix_engine_with_strategies: FixEngine,
) -> None:
    """Profile fix loop convergence time for small number of issues.

    Expected: Should complete in <1 second for 5 issues.
    """
    report = make_qa_report_with_errors(error_count=5)

    start_time = time.perf_counter()
    result = fix_engine_with_strategies.run_fix_loop(report)
    elapsed = time.perf_counter() - start_time

    # Log convergence metrics
    print("\n=== Fix Loop Convergence (5 issues) ===")
    print(f"Total Time: {elapsed:.3f}s")
    print(f"Iterations: {result.iterations}")
    print(f"Fixes Applied: {len(result.fixes_applied)}")
    print(f"Success: {result.success}")
    print(f"Time per Fix: {elapsed / len(result.fixes_applied):.3f}s")

    # Performance assertion
    assert elapsed < 1.0, f"Fix loop took {elapsed:.3f}s, expected <1s for 5 issues"


def test_fix_loop_convergence_time_medium(
    fix_engine_with_strategies: FixEngine,
) -> None:
    """Profile fix loop convergence time for medium number of issues.

    Expected: Should complete in <5 seconds for 20 issues.
    """
    report = make_qa_report_with_errors(error_count=20)

    start_time = time.perf_counter()
    result = fix_engine_with_strategies.run_fix_loop(report)
    elapsed = time.perf_counter() - start_time

    # Log convergence metrics
    print("\n=== Fix Loop Convergence (20 issues) ===")
    print(f"Total Time: {elapsed:.3f}s")
    print(f"Iterations: {result.iterations}")
    print(f"Fixes Applied: {len(result.fixes_applied)}")
    print(f"Success: {result.success}")
    print(f"Time per Fix: {elapsed / len(result.fixes_applied):.3f}s")

    # Performance assertion
    assert elapsed < 5.0, f"Fix loop took {elapsed:.3f}s, expected <5s for 20 issues"


def test_fix_loop_convergence_time_large(
    fix_engine_with_strategies: FixEngine,
) -> None:
    """Profile fix loop convergence time for large number of issues.

    Expected: Should complete in <10 seconds for 50 issues.
    """
    report = make_qa_report_with_errors(error_count=50)

    start_time = time.perf_counter()
    result = fix_engine_with_strategies.run_fix_loop(report)
    elapsed = time.perf_counter() - start_time

    # Log convergence metrics
    print("\n=== Fix Loop Convergence (50 issues) ===")
    print(f"Total Time: {elapsed:.3f}s")
    print(f"Iterations: {result.iterations}")
    print(f"Fixes Applied: {len(result.fixes_applied)}")
    print(f"Success: {result.success}")
    print(f"Time per Fix: {elapsed / len(result.fixes_applied):.3f}s")

    # Performance assertion
    assert elapsed < 10.0, f"Fix loop took {elapsed:.3f}s, expected <10s for 50 issues"


def test_fix_loop_max_iterations_performance() -> None:
    """Profile fix loop behavior when max iterations is reached.

    Ensures the loop terminates gracefully without excessive overhead.
    """
    registry = FixStrategyRegistry()

    def slow_partial_fix(issue: QAIssue) -> FixResult:
        """Mock fix strategy that partially fixes (never fully succeeds)."""
        time.sleep(0.02)  # 20ms per attempt
        return FixResult(
            issue=issue,
            status=FixStatus.PARTIAL,
            message="Partially fixed",
            changes_made=["Partial fix applied"],
        )

    registry.register("QA-L-001", slow_partial_fix)
    engine = FixEngine(registry=registry, max_iterations=3)

    report = make_qa_report_with_errors(error_count=5)

    start_time = time.perf_counter()
    result = engine.run_fix_loop(report)
    elapsed = time.perf_counter() - start_time

    # Log max iterations behavior
    print("\n=== Max Iterations Performance ===")
    print(f"Total Time: {elapsed:.3f}s")
    print(f"Iterations: {result.iterations}")
    print("Max Iterations: 3")
    print(f"Fixes Applied: {len(result.fixes_applied)}")

    # Should stop at max iterations
    assert result.iterations <= 3, "Should not exceed max iterations"

    # Should complete quickly even with max iterations
    assert elapsed < 2.0, f"Fix loop took {elapsed:.3f}s, expected <2s"


def test_fix_loop_no_progress_detection() -> None:
    """Profile fix loop behavior when no progress is made.

    Ensures the loop detects stagnation and terminates early.
    """
    registry = FixStrategyRegistry()

    def failing_fix(issue: QAIssue) -> FixResult:
        """Mock fix strategy that always fails."""
        time.sleep(0.01)  # 10ms per attempt
        return FixResult(
            issue=issue,
            status=FixStatus.FAILED,
            message="Fix failed",
        )

    registry.register("QA-L-001", failing_fix)
    engine = FixEngine(registry=registry, max_iterations=5)

    report = make_qa_report_with_errors(error_count=3)

    start_time = time.perf_counter()
    result = engine.run_fix_loop(report)
    elapsed = time.perf_counter() - start_time

    # Log no-progress detection
    print("\n=== No Progress Detection ===")
    print(f"Total Time: {elapsed:.3f}s")
    print(f"Iterations: {result.iterations}")
    print(f"Fixes Applied: {len(result.fixes_applied)}")
    print(f"Success: {result.success}")

    # Should detect no progress and terminate early (after 1 iteration)
    assert result.iterations == 1, "Should terminate after first iteration when all fixes fail"

    # Should complete quickly
    assert elapsed < 1.0, f"Fix loop took {elapsed:.3f}s, expected <1s for no-progress case"


def test_fix_loop_memory_usage() -> None:
    """Profile memory usage during fix loop iterations.

    Ensures fix operations don't leak memory across iterations.
    """
    import tracemalloc

    registry = FixStrategyRegistry()

    def successful_fix(issue: QAIssue) -> FixResult:
        """Mock fix strategy that succeeds."""
        return FixResult(
            issue=issue,
            status=FixStatus.SUCCESS,
            message="Fixed successfully",
            changes_made=["Applied fix"],
        )

    for i in range(1, 7):
        registry.register(f"QA-L-00{i}", successful_fix)

    engine = FixEngine(registry=registry, max_iterations=5)
    report = make_qa_report_with_errors(error_count=50)

    # Start memory tracking
    tracemalloc.start()

    # Run fix loop
    result = engine.run_fix_loop(report)

    # Get memory statistics
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Log memory metrics
    print("\n=== Fix Loop Memory Usage ===")
    print(f"Current Memory: {current / 1024 / 1024:.2f} MB")
    print(f"Peak Memory: {peak / 1024 / 1024:.2f} MB")
    print(f"Iterations: {result.iterations}")
    print(f"Fixes Applied: {len(result.fixes_applied)}")

    # Memory assertion: should not exceed 50 MB for fix loop operations
    assert peak < 50 * 1024 * 1024, f"Peak memory {peak / 1024 / 1024:.2f} MB exceeded 50 MB"


@pytest.mark.parametrize("issue_count", [5, 10, 20, 50])
def test_fix_loop_scalability(issue_count: int) -> None:
    """Test fix loop scalability across different issue counts.

    Verifies that performance scales linearly with issue count.
    """
    registry = FixStrategyRegistry()

    def successful_fix(issue: QAIssue) -> FixResult:
        """Mock fix strategy that succeeds."""
        time.sleep(0.01)  # 10ms per fix
        return FixResult(
            issue=issue,
            status=FixStatus.SUCCESS,
            message="Fixed successfully",
            changes_made=["Applied fix"],
        )

    for i in range(1, 7):
        registry.register(f"QA-L-00{i}", successful_fix)

    engine = FixEngine(registry=registry, max_iterations=5)
    report = make_qa_report_with_errors(error_count=issue_count)

    # Profile fix loop
    start_time = time.perf_counter()
    result = engine.run_fix_loop(report)
    elapsed = time.perf_counter() - start_time

    # Log scalability metrics
    time_per_issue = elapsed / issue_count
    print(f"\n=== Scalability Test ({issue_count} issues) ===")
    print(f"Total Time: {elapsed:.3f}s")
    print(f"Time per Issue: {time_per_issue:.3f}s")
    print(f"Iterations: {result.iterations}")
    print(f"Fixes Applied: {len(result.fixes_applied)}")

    # Performance should scale linearly: ~0.02s per issue max (including overhead)
    assert time_per_issue < 0.05, f"Time per issue {time_per_issue:.3f}s exceeded 0.05s"


# Made with Bob
