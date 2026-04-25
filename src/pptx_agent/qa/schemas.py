"""QA schemas for quality issue reporting."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_serializer


class Severity(StrEnum):
    """Issue severity levels for QA validation.

    Attributes:
        ERROR: Blocks quality, must fix before release
        WARNING: Should fix, not blocking but affects quality
        INFO: Informational, optional improvement
    """

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class QAIssue(BaseModel):
    """Represents a single quality issue detected during QA pass.

    Attributes:
        rule_id: Unique rule identifier (e.g., QA-L-001)
        severity: Issue severity level
        slide_index: Zero-based slide index where issue was found
        shape_index: Zero-based shape index if applicable (None for slide-level issues)
        message: Human-readable issue description
        auto_fixable: Whether issue can be automatically fixed
        suggested_fix: Suggested manual fix if not auto-fixable
    """

    rule_id: str = Field(..., description="Unique rule identifier (e.g., QA-L-001)")
    severity: Severity
    slide_index: int = Field(..., ge=0, description="Zero-based slide index")
    shape_index: int | None = Field(
        default=None,
        ge=0,
        description="Zero-based shape index if applicable",
    )
    message: str = Field(..., description="Human-readable issue description")
    auto_fixable: bool = Field(
        default=False,
        description="Whether issue can be auto-fixed",
    )
    suggested_fix: str | None = Field(
        default=None,
        description="Suggested manual fix if not auto-fixable",
    )


class QAReport(BaseModel):
    """Aggregates all QA issues with summary statistics.

    Attributes:
        total_issues: Total number of issues found
        error_count: Number of ERROR severity issues
        warning_count: Number of WARNING severity issues
        info_count: Number of INFO severity issues
        issues: List of all detected issues
        fix_iterations: Number of fix loop iterations performed
        passed: True if error_count == 0 (no blocking issues)
    """

    total_issues: int = Field(default=0, ge=0)
    error_count: int = Field(default=0, ge=0)
    warning_count: int = Field(default=0, ge=0)
    info_count: int = Field(default=0, ge=0)
    issues: list[QAIssue] = Field(default_factory=list)
    fix_iterations: int = Field(
        default=0,
        ge=0,
        description="Number of fix loop iterations",
    )

    @property
    def passed(self) -> bool:
        """Check if QA passed (no errors).

        Returns:
            True if error_count == 0, False otherwise
        """
        return self.error_count == 0

    @model_serializer
    def serialize_model(self) -> dict[str, Any]:
        """Serialize model including computed properties.

        Returns:
            Dictionary with all fields including passed property
        """
        return {
            "total_issues": self.total_issues,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "issues": [issue.model_dump() for issue in self.issues],
            "fix_iterations": self.fix_iterations,
            "passed": self.passed,
        }

    def to_json(self) -> str:
        """Serialize to JSON string for machine processing.

        Returns:
            JSON string representation of the report
        """
        return self.model_dump_json(indent=2)

    def to_markdown(self) -> str:
        """Generate human-readable Markdown report.

        Returns:
            Markdown formatted report string
        """
        lines = ["# QA Report", ""]

        # Summary section
        lines.append("## Summary")
        lines.append(f"- **Status**: {'✅ PASSED' if self.passed else '❌ FAILED'}")
        lines.append(f"- **Total Issues**: {self.total_issues}")
        lines.append(f"- **Errors**: {self.error_count}")
        lines.append(f"- **Warnings**: {self.warning_count}")
        lines.append(f"- **Info**: {self.info_count}")
        if self.fix_iterations > 0:
            lines.append(f"- **Fix Iterations**: {self.fix_iterations}")
        lines.append("")

        # Issues by severity
        if self.error_count > 0:
            lines.append("## \u274c Errors")
            lines.extend(
                self._format_issue(issue)
                for issue in self.issues
                if issue.severity == Severity.ERROR
            )
            lines.append("")

        if self.warning_count > 0:
            lines.append("## \u26a0\ufe0f Warnings")
            lines.extend(
                self._format_issue(issue)
                for issue in self.issues
                if issue.severity == Severity.WARNING
            )
            lines.append("")

        if self.info_count > 0:
            lines.append("## \u2139\ufe0f Info")
            lines.extend(
                self._format_issue(issue)
                for issue in self.issues
                if issue.severity == Severity.INFO
            )
            lines.append("")

        return "\n".join(lines)

    def _format_issue(self, issue: QAIssue) -> str:
        """Format a single issue for Markdown output.

        Args:
            issue: QA issue to format

        Returns:
            Formatted issue string
        """
        location = f"Slide {issue.slide_index + 1}"
        if issue.shape_index is not None:
            location += f", Shape {issue.shape_index + 1}"

        fix_info = " (auto-fixable)" if issue.auto_fixable else ""
        result = f"- **[{issue.rule_id}]** {location}: {issue.message}{fix_info}"

        if issue.suggested_fix and not issue.auto_fixable:
            result += f"\n  - *Suggested fix*: {issue.suggested_fix}"

        return result


# Made with Bob
