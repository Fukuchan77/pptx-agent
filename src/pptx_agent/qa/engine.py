"""QA engine for orchestrating validation rules."""

from typing import Literal, cast

from pptx_agent.pptx_wrapper.presentation import PresentationWrapper
from pptx_agent.qa.rules.base import QARule
from pptx_agent.qa.rules.registry import QARuleRegistry, get_global_registry
from pptx_agent.qa.schemas import QAIssue, QAReport, Severity
from pptx_agent.utils.language_detector import detect_language


class QAEngine:
    """Orchestrates QA validation by running registered rules.

    The QA engine coordinates the execution of validation rules against
    presentations, aggregates results, and generates comprehensive reports.

    Example:
        >>> engine = QAEngine()
        >>> report = engine.validate(presentation)
        >>> if not report.passed:
        ...     print(report.to_markdown())
    """

    def __init__(
        self,
        registry: QARuleRegistry | None = None,
        language: Literal["ja", "en"] | None = None,
    ) -> None:
        """Initialize QA engine with rule registry and optional language override.

        Args:
            registry: Rule registry to use (defaults to global registry)
            language: Optional language override for capacity calculations.
                     If None, language is auto-detected from presentation content.
        """
        self.registry = registry or get_global_registry()
        self.language = language

    def validate(
        self,
        presentation: PresentationWrapper,
        rule_ids: list[str] | None = None,
        categories: list[str] | None = None,
    ) -> QAReport:
        """Validate presentation against registered rules with language-aware checks.

        Args:
            presentation: Presentation to validate
            rule_ids: Specific rule IDs to run (None = all rules)
            categories: Specific categories to run (None = all categories)

        Returns:
            QA report with all detected issues and statistics
        """
        # Determine which rules to run
        rules = self._select_rules(rule_ids, categories)

        # Detect language from presentation if not overridden
        detected_language = self._detect_presentation_language(presentation)

        # Run all rules and collect issues
        all_issues: list[QAIssue] = []
        for rule in rules:
            try:
                # Pass language context to rules that support it
                if hasattr(rule, "language"):
                    rule.language = detected_language  # type: ignore[attr-defined]

                issues = rule.validate(presentation)
                all_issues.extend(issues)
            except Exception:  # noqa: S110
                # Rules should be defensive, but catch any unexpected errors
                # and continue with other rules
                pass

        # Build report
        return self._build_report(all_issues)

    def validate_with_categories(
        self,
        presentation: PresentationWrapper,
        categories: list[str],
    ) -> QAReport:
        """Validate presentation using rules from specific categories.

        Args:
            presentation: Presentation to validate
            categories: List of category names to include

        Returns:
            QA report with issues from specified categories
        """
        return self.validate(presentation, categories=categories)

    def validate_auto_fixable_only(
        self,
        presentation: PresentationWrapper,
    ) -> QAReport:
        """Validate using only auto-fixable rules.

        Useful for identifying issues that can be automatically resolved
        without manual intervention.

        Args:
            presentation: Presentation to validate

        Returns:
            QA report with only auto-fixable issues
        """
        rules = self.registry.get_auto_fixable_rules()
        all_issues: list[QAIssue] = []

        for rule in rules:
            try:
                issues = rule.validate(presentation)
                all_issues.extend(issues)
            except Exception:  # noqa: S110
                pass

        return self._build_report(all_issues)

    def _select_rules(
        self,
        rule_ids: list[str] | None,
        categories: list[str] | None,
    ) -> list[QARule]:
        """Select rules to run based on filters.

        Args:
            rule_ids: Specific rule IDs to include
            categories: Specific categories to include

        Returns:
            List of rules to execute
        """
        if rule_ids is not None:
            # Run specific rules by ID
            rules = []
            for rule_id in rule_ids:
                rule = self.registry.get_rule(rule_id)
                if rule is not None:
                    rules.append(rule)
            return rules

        if categories is not None:
            # Run rules from specific categories
            rules = []
            for category in categories:
                rules.extend(self.registry.get_rules_by_category(category))
            return rules

        # Run all rules
        return self.registry.get_all_rules()

    def _build_report(self, issues: list[QAIssue]) -> QAReport:
        """Build QA report from collected issues.

        Args:
            issues: List of all detected issues

        Returns:
            Complete QA report with statistics
        """
        # Count issues by severity
        error_count = sum(1 for issue in issues if issue.severity == Severity.ERROR)
        warning_count = sum(1 for issue in issues if issue.severity == Severity.WARNING)
        info_count = sum(1 for issue in issues if issue.severity == Severity.INFO)

        return QAReport(
            total_issues=len(issues),
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
            issues=issues,
        )

    def _detect_presentation_language(
        self,
        presentation: PresentationWrapper,
    ) -> Literal["ja", "en"]:
        """Detect the dominant language of the presentation.

        Args:
            presentation: Presentation to analyze

        Returns:
            Detected language code ("ja" or "en")
        """
        # Use language override if provided
        if self.language is not None:
            return cast("Literal['ja', 'en']", self.language)

        # Collect text from all slides
        all_text = ""
        if presentation.is_loaded:
            for slide in presentation.prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text:  # type: ignore[attr-defined]
                        all_text += shape.text + " "  # type: ignore[attr-defined]

        # Detect language from collected text
        return detect_language(all_text) if all_text.strip() else "en"


# Made with Bob
