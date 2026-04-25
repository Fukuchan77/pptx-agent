"""Fixer engine for orchestrating automatic issue remediation."""

from collections.abc import Callable

from pptx_agent.fixer.schemas import FixLoopResult, FixResult, FixStatus
from pptx_agent.qa.schemas import QAIssue, QAReport


class FixStrategyRegistry:
    """Registry for managing fix strategies by QA rule identifier.

    The registry provides a simple mapping from QA rule IDs to callable fix
    strategies. This allows the fix engine to look up the appropriate strategy
    for each issue without hard-coding rule-specific behavior.
    """

    def __init__(self) -> None:
        """Initialize an empty strategy registry."""
        self._strategies: dict[str, Callable[[QAIssue], FixResult]] = {}

    def register(
        self,
        rule_id: str,
        strategy: Callable[[QAIssue], FixResult],
    ) -> None:
        """Register a fix strategy for a QA rule.

        Args:
            rule_id: QA rule identifier handled by the strategy
            strategy: Callable that attempts to resolve the issue

        Raises:
            ValueError: If a strategy is already registered for the rule ID
        """
        if rule_id in self._strategies:
            msg = f"Strategy for rule {rule_id} already registered"
            raise ValueError(msg)

        self._strategies[rule_id] = strategy

    def unregister(self, rule_id: str) -> bool:
        """Remove a strategy from the registry.

        Args:
            rule_id: QA rule identifier to remove

        Returns:
            True if the strategy existed and was removed, otherwise False
        """
        if rule_id not in self._strategies:
            return False

        del self._strategies[rule_id]
        return True

    def get_strategy(
        self,
        rule_id: str,
    ) -> Callable[[QAIssue], FixResult] | None:
        """Get the registered strategy for a rule ID.

        Args:
            rule_id: QA rule identifier

        Returns:
            Registered strategy or None if no strategy exists
        """
        return self._strategies.get(rule_id)

    def clear(self) -> None:
        """Remove all registered strategies."""
        self._strategies.clear()

    def __len__(self) -> int:
        """Return the number of registered strategies."""
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
        """Apply a single fix strategy for an issue.

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

        strategy = self.registry.get_strategy(issue.rule_id)
        if strategy is None:
            return FixResult(
                issue=issue,
                status=FixStatus.SKIPPED,
                message=f"No fix strategy registered for {issue.rule_id}",
            )

        try:
            return strategy(issue)
        except Exception as exc:
            return FixResult(
                issue=issue,
                status=FixStatus.FAILED,
                message=f"Fix strategy failed: {exc}",
            )

    def run_fix_loop(self, report: QAReport) -> FixLoopResult:
        """Run a bounded fix loop over the report's issues.

        The foundational implementation applies strategies to the current set of
        issues once per iteration. A future phase can re-run QA between
        iterations and update the report incrementally.

        Args:
            report: QA report containing issues to remediate

        Returns:
            Aggregated fix loop result
        """
        remaining_report = report.model_copy(deep=True)
        fixes_applied: list[FixResult] = []
        iterations = 0

        while iterations < self.max_iterations and remaining_report.error_count > 0:
            fixable_issues = [issue for issue in remaining_report.issues if issue.auto_fixable]
            if not fixable_issues:
                break

            iteration_results = [self.apply_fix(issue) for issue in fixable_issues]
            fixes_applied.extend(iteration_results)
            iterations += 1

            if all(
                result.status in {FixStatus.SKIPPED, FixStatus.FAILED}
                for result in iteration_results
            ):
                break

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
