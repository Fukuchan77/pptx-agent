"""Fixer engine for orchestrating automatic issue remediation."""

import logging
from collections.abc import Callable

from pptx_agent.fixer.schemas import FixLoopResult, FixResult, FixStatus
from pptx_agent.qa.schemas import QAIssue, QAReport

logger = logging.getLogger(__name__)


class FixStrategyRegistry:
    """Registry for managing fix strategies by QA rule identifier.

    The registry provides a simple mapping from QA rule IDs to callable fix
    strategies. This allows the fix engine to look up the appropriate strategy
    for each issue without hard-coding rule-specific behavior.
    """

    def __init__(self) -> None:
        """Initialize an empty strategy registry."""
        self._strategies: dict[str, list[Callable[[QAIssue], FixResult]]] = {}

    def register(
        self,
        rule_id: str,
        strategy: Callable[[QAIssue], FixResult],
    ) -> None:
        """Register a fix strategy for a QA rule.

        Multiple strategies can be registered for the same rule ID.
        They will be tried in order until one succeeds.

        Args:
            rule_id: QA rule identifier handled by the strategy
            strategy: Callable that attempts to resolve the issue
        """
        if rule_id not in self._strategies:
            self._strategies[rule_id] = []

        self._strategies[rule_id].append(strategy)

    def unregister(
        self, rule_id: str, strategy: Callable[[QAIssue], FixResult] | None = None
    ) -> bool:
        """Remove strategy(ies) from the registry.

        Args:
            rule_id: QA rule identifier
            strategy: Specific strategy to remove. If None, removes all strategies for the rule.

        Returns:
            True if strategy/strategies existed and were removed, otherwise False
        """
        if rule_id not in self._strategies:
            return False

        if strategy is None:
            # Remove all strategies for this rule
            del self._strategies[rule_id]
            return True

        # Remove specific strategy
        try:
            self._strategies[rule_id].remove(strategy)
        except ValueError:
            return False
        else:
            # Clean up empty list
            if not self._strategies[rule_id]:
                del self._strategies[rule_id]
            return True

    def get_strategies(
        self,
        rule_id: str,
    ) -> list[Callable[[QAIssue], FixResult]]:
        """Get all registered strategies for a rule ID.

        Args:
            rule_id: QA rule identifier

        Returns:
            List of registered strategies (empty if none exist)
        """
        return self._strategies.get(rule_id, [])

    def clear(self) -> None:
        """Remove all registered strategies."""
        self._strategies.clear()

    def __len__(self) -> int:
        """Return the number of rule IDs with registered strategies.

        Note: This counts unique rule IDs, not the total number of strategies.
        A rule with multiple strategies counts as 1.
        """
        return len(self._strategies)

    def __contains__(self, rule_id: str) -> bool:
        """Return whether a strategy is registered for the rule ID."""
        return rule_id in self._strategies


_global_registry = FixStrategyRegistry()


def get_global_registry() -> FixStrategyRegistry:
    """Return the shared global fix strategy registry."""
    return _global_registry


class FixEngine:
    """Apply registered fix strategies to QA issues using a bounded loop."""

    def __init__(
        self,
        registry: FixStrategyRegistry | None = None,
        max_iterations: int = 3,
    ) -> None:
        """Initialize the fix engine.

        Args:
            registry: Registry to use for strategy lookup
            max_iterations: Maximum number of fix loop iterations

        Raises:
            ValueError: If max_iterations is less than 1
        """
        if max_iterations < 1:
            msg = "max_iterations must be greater than or equal to 1"
            raise ValueError(msg)

        self.registry = registry or get_global_registry()
        self.max_iterations = max_iterations

    def apply_fix(self, issue: QAIssue) -> FixResult:
        """Apply fix strategies for an issue, trying each in order until one succeeds.

        Args:
            issue: QA issue to remediate

        Returns:
            Fix result describing the remediation outcome
        """
        if not issue.auto_fixable:
            return FixResult(
                issue=issue,
                status=FixStatus.SKIPPED,
                message="Issue is not marked as auto-fixable",
            )

        strategies = self.registry.get_strategies(issue.rule_id)
        if not strategies:
            return FixResult(
                issue=issue,
                status=FixStatus.SKIPPED,
                message=f"No fix strategy registered for {issue.rule_id}",
            )

        # Try each strategy in order until one succeeds
        last_error = None
        any_failed = False
        for strategy in strategies:
            try:
                result = strategy(issue)
                # If strategy succeeded or partially succeeded, return immediately
                if result.status in {FixStatus.SUCCESS, FixStatus.PARTIAL}:
                    return result
                # Track if any strategy actually failed (vs skipped)
                if result.status == FixStatus.FAILED:
                    any_failed = True
                # If strategy was skipped or failed, try next one
                last_error = result.message
            except Exception as exc:
                logger.warning("Fix strategy raised exception: %s", exc, exc_info=True)
                last_error = str(exc)
                any_failed = True
                continue

        # All strategies failed or were skipped - return appropriate status
        final_status = FixStatus.FAILED if any_failed else FixStatus.SKIPPED
        status_text = "failed" if any_failed else "skipped"
        return FixResult(
            issue=issue,
            status=final_status,
            message=f"All fix strategies {status_text}. Last error: {last_error}",
        )

    def run_fix_loop(
        self,
        report: QAReport,
        presentation_path: str | None = None,
        qa_runner: Callable[[str], QAReport] | None = None,
        save_callback: Callable[[], None] | None = None,
    ) -> FixLoopResult:
        """Run a bounded fix loop over the report's issues.

        After each iteration, if save_callback and qa_runner are provided,
        the presentation is saved via the callback and QA is re-run to get updated issues.

        Args:
            report: Initial QA report containing issues to remediate
            presentation_path: Optional path to presentation (for qa_runner)
            qa_runner: Optional callable to re-run QA and get fresh report
            save_callback: Optional callable to save presentation changes to disk

        Returns:
            Aggregated fix loop result with final QA report
        """
        remaining_report = report.model_copy(deep=True)
        fixes_applied: list[FixResult] = []
        iterations = 0

        while iterations < self.max_iterations and remaining_report.error_count > 0:
            fixable_issues = [issue for issue in remaining_report.issues if issue.auto_fixable]
            if not fixable_issues:
                # No fixable issues remain
                break

            iteration_results = [self.apply_fix(issue) for issue in fixable_issues]
            fixes_applied.extend(iteration_results)
            iterations += 1

            # Check if all fixes failed or were skipped
            if all(
                result.status in {FixStatus.SKIPPED, FixStatus.FAILED}
                for result in iteration_results
            ):
                # No progress made, stop iterating
                break

            # Save in-memory edits to disk (independent of QA runner)
            if save_callback:
                try:
                    save_callback()
                except Exception:
                    logger.exception("Failed to save presentation changes")
                    remaining_report.fix_iterations = iterations
                    break

            # Optionally re-run QA to get updated issue list
            if qa_runner and presentation_path:
                try:
                    remaining_report = qa_runner(presentation_path)
                except Exception as exc:
                    logger.warning("QA re-run failed: %s", exc, exc_info=True)
                    # Keep current report and stop iterating
                    remaining_report.fix_iterations = iterations
                    break
            else:
                # Without QA runner, we can't verify if fixes worked, so stop after one iteration
                break

        remaining_report.fix_iterations = iterations
        success = remaining_report.error_count == 0

        return FixLoopResult(
            iterations=iterations,
            fixes_applied=fixes_applied,
            final_qa_report=remaining_report,
            success=success,
        )


# Made with Bob
