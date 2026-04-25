"""Base protocol and interfaces for QA rules."""

from typing import Protocol

from pptx_agent.pptx_wrapper.presentation import PresentationWrapper
from pptx_agent.qa.schemas import QAIssue


class QARule(Protocol):
    """Protocol defining the interface for QA validation rules.

    All QA rules must implement this protocol to be registered and executed
    by the QA engine. Rules are stateless and should be reusable across
    multiple validation runs.

    Attributes:
        rule_id: Unique identifier for the rule (e.g., "QA-L-001")
        description: Human-readable description of what the rule checks
        auto_fixable: Whether issues from this rule can be automatically fixed
    """

    rule_id: str
    description: str
    auto_fixable: bool

    def validate(self, presentation: PresentationWrapper) -> list[QAIssue]:
        """Validate presentation against this rule.

        Args:
            presentation: Wrapped PowerPoint presentation to validate

        Returns:
            List of QA issues found (empty list if no issues)

        Note:
            Rules should be defensive and handle edge cases gracefully.
            If validation cannot be performed, return empty list rather
            than raising exceptions.
        """
        ...


# Made with Bob
