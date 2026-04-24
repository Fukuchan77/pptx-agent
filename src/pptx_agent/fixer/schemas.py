"""Fixer schemas for automatic issue remediation."""

from enum import StrEnum

from pydantic import BaseModel, Field

from pptx_agent.qa.schemas import QAIssue, QAReport


class FixStatus(StrEnum):
    """Fix operation status.

    Attributes:
        SUCCESS: Fix successfully applied
        PARTIAL: Some issues fixed, some remain
        FAILED: Fix operation failed
        SKIPPED: Issue not auto-fixable, skipped
    """

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"


class FixResult(BaseModel):
    """Result of a single fix operation.

    Attributes:
        issue: The QA issue that was addressed
        status: Fix operation status
        message: Fix operation outcome description
        changes_made: List of specific changes applied
    """

    issue: QAIssue
    status: FixStatus
    message: str = Field(..., description="Fix operation outcome")
    changes_made: list[str] = Field(
        default_factory=list,
        description="List of changes applied",
    )


class FixLoopResult(BaseModel):
    """Result of complete fix loop with multiple iterations.

    Attributes:
        iterations: Number of fix loop iterations performed
        fixes_applied: List of all fix results from all iterations
        final_qa_report: QA report after final iteration
        success: True if all errors resolved (error_count == 0)
    """

    iterations: int = Field(..., ge=0, description="Number of iterations performed")
    fixes_applied: list[FixResult] = Field(
        default_factory=list,
        description="All fix results",
    )
    final_qa_report: QAReport
    success: bool = Field(..., description="True if all errors resolved")


# Made with Bob
