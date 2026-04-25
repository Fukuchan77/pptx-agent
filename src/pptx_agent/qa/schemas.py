"""QA schemas for quality issue reporting."""

from enum import StrEnum
from typing import Any, Literal

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


# Translation dictionaries for common QA messages
_TRANSLATIONS = {
    "en": {
        "qa_report": "QA Report",
        "summary": "Summary",
        "status": "Status",
        "passed": "PASSED",
        "failed": "FAILED",
        "total_issues": "Total Issues",
        "errors": "Errors",
        "warnings": "Warnings",
        "info": "Info",
        "fix_iterations": "Fix Iterations",
        "slide": "Slide",
        "shape": "Shape",
        "auto_fixable": "auto-fixable",
        "suggested_fix": "Suggested fix",
    },
    "ja": {
        "qa_report": "品質保証レポート",
        "summary": "概要",
        "status": "ステータス",
        "passed": "合格",
        "failed": "不合格",
        "total_issues": "問題総数",
        "errors": "エラー",
        "warnings": "警告",
        "info": "情報",
        "fix_iterations": "修正回数",
        "slide": "スライド",
        "shape": "図形",
        "auto_fixable": "自動修正可能",
        "suggested_fix": "推奨される修正",
    },
}


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

    def to_markdown(self, language: Literal["ja", "en"] = "en") -> str:
        """Generate human-readable Markdown report with language support.

        Args:
            language: Language for report labels ("en" or "ja")

        Returns:
            Markdown formatted report string
        """
        t = _TRANSLATIONS[language]
        lines = [f"# {t['qa_report']}", ""]

        # Summary section
        lines.append(f"## {t['summary']}")
        status_text = t["passed"] if self.passed else t["failed"]
        status_emoji = "✅" if self.passed else "❌"
        lines.append(f"- **{t['status']}**: {status_emoji} {status_text}")
        lines.append(f"- **{t['total_issues']}**: {self.total_issues}")
        lines.append(f"- **{t['errors']}**: {self.error_count}")
        lines.append(f"- **{t['warnings']}**: {self.warning_count}")
        lines.append(f"- **{t['info']}**: {self.info_count}")
        if self.fix_iterations > 0:
            lines.append(f"- **{t['fix_iterations']}**: {self.fix_iterations}")
        lines.append("")

        # Issues by severity
        if self.error_count > 0:
            lines.append(f"## \u274c {t['errors']}")
            lines.extend(
                self._format_issue(issue, language)
                for issue in self.issues
                if issue.severity == Severity.ERROR
            )
            lines.append("")

        if self.warning_count > 0:
            lines.append(f"## \u26a0\ufe0f {t['warnings']}")
            lines.extend(
                self._format_issue(issue, language)
                for issue in self.issues
                if issue.severity == Severity.WARNING
            )
            lines.append("")

        if self.info_count > 0:
            lines.append(f"## \u2139\ufe0f {t['info']}")
            lines.extend(
                self._format_issue(issue, language)
                for issue in self.issues
                if issue.severity == Severity.INFO
            )
            lines.append("")

        return "\n".join(lines)

    def _format_issue(self, issue: QAIssue, language: Literal["ja", "en"] = "en") -> str:
        """Format a single issue for Markdown output with language support.

        Args:
            issue: QA issue to format
            language: Language for labels ("en" or "ja")

        Returns:
            Formatted issue string
        """
        t = _TRANSLATIONS[language]
        location = f"{t['slide']} {issue.slide_index + 1}"
        if issue.shape_index is not None:
            location += f", {t['shape']} {issue.shape_index + 1}"

        fix_info = f" ({t['auto_fixable']})" if issue.auto_fixable else ""
        result = f"- **[{issue.rule_id}]** {location}: {issue.message}{fix_info}"

        if issue.suggested_fix and not issue.auto_fixable:
            result += f"\n  - *{t['suggested_fix']}*: {issue.suggested_fix}"

        return result


# Made with Bob
