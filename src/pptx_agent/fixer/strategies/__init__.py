"""Fix strategy interfaces for automatic issue remediation."""

from typing import Protocol

from pptx_agent.fixer.schemas import FixResult
from pptx_agent.qa.schemas import QAIssue


class FixStrategy(Protocol):
    """Protocol defining the interface for automatic fix strategies.

    Strategies are stateless callables that attempt to resolve a single
    auto-fixable QA issue and report the outcome as a structured result.
    """

    rule_id: str
    description: str

    def apply(self, issue: QAIssue) -> FixResult:
        """Attempt to resolve a QA issue.

        Args:
            issue: QA issue targeted by the strategy

        Returns:
            Structured fix result describing the outcome
        """
        ...


__all__ = ["FixStrategy"]

# Made with Bob
