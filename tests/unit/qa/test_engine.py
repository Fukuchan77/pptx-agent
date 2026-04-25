"""Unit tests for QA engine."""

from unittest.mock import Mock

import pytest

from pptx_agent.pptx_wrapper.presentation import PresentationWrapper
from pptx_agent.qa.engine import QAEngine
from pptx_agent.qa.rules import QARuleRegistry
from pptx_agent.qa.schemas import QAIssue, Severity


class MockRule:
    """Mock QA rule for testing."""

    def __init__(
        self,
        rule_id: str,
        description: str,
        auto_fixable: bool = False,
        issues: list[QAIssue] | None = None,
    ) -> None:
        """Initialize mock rule.

        Args:
            rule_id: Rule identifier
            description: Rule description
            auto_fixable: Whether rule supports auto-fixing
            issues: Issues to return from validate()
        """
        self.rule_id = rule_id
        self.description = description
        self.auto_fixable = auto_fixable
        self._issues = issues or []

    def validate(self, presentation: PresentationWrapper) -> list[QAIssue]:
        """Return pre-configured issues.

        Args:
            presentation: Presentation to validate (unused in mock)

        Returns:
            Pre-configured list of issues
        """
        return self._issues


@pytest.fixture
def mock_presentation() -> Mock:
    """Create mock presentation for testing.

    Returns:
        Mock PresentationWrapper instance
    """
    return Mock(spec=PresentationWrapper)


@pytest.fixture
def empty_registry() -> QARuleRegistry:
    """Create empty rule registry for testing.

    Returns:
        Empty QARuleRegistry instance
    """
    return QARuleRegistry()


@pytest.fixture
def populated_registry() -> QARuleRegistry:
    """Create registry with sample rules.

    Returns:
        QARuleRegistry with test rules
    """
    registry = QARuleRegistry()

    # Add error rule
    error_issue = QAIssue(
        rule_id="QA-L-001",
        severity=Severity.ERROR,
        slide_index=0,
        message="Critical error",
    )
    error_rule = MockRule("QA-L-001", "Error rule", issues=[error_issue])
    registry.register(error_rule, "layout")

    # Add warning rule
    warning_issue = QAIssue(
        rule_id="QA-C-001",
        severity=Severity.WARNING,
        slide_index=1,
        message="Warning message",
    )
    warning_rule = MockRule("QA-C-001", "Warning rule", issues=[warning_issue])
    registry.register(warning_rule, "content")

    # Add auto-fixable rule
    fixable_issue = QAIssue(
        rule_id="QA-L-002",
        severity=Severity.ERROR,
        slide_index=2,
        message="Auto-fixable error",
        auto_fixable=True,
    )
    fixable_rule = MockRule(
        "QA-L-002",
        "Fixable rule",
        auto_fixable=True,
        issues=[fixable_issue],
    )
    registry.register(fixable_rule, "layout")

    return registry


def test_engine_initialization_default_registry() -> None:
    """Test engine initializes with global registry by default."""
    engine = QAEngine()
    assert engine.registry is not None


def test_validate_empty_registry(
    mock_presentation: Mock,
    empty_registry: QARuleRegistry,
) -> None:
    """Test validation with no registered rules."""
    engine = QAEngine(registry=empty_registry)
    report = engine.validate(mock_presentation)

    assert report.total_issues == 0
    assert report.error_count == 0
    assert report.warning_count == 0
    assert report.info_count == 0
    assert report.passed is True


def test_validate_all_rules(
    mock_presentation: Mock,
    populated_registry: QARuleRegistry,
) -> None:
    """Test validation runs all registered rules."""
    engine = QAEngine(registry=populated_registry)
    report = engine.validate(mock_presentation)

    assert report.total_issues == 3
    assert report.error_count == 2
    assert report.warning_count == 1
    assert report.info_count == 0
    assert report.passed is False  # Has errors


def test_validate_specific_rules(
    mock_presentation: Mock,
    populated_registry: QARuleRegistry,
) -> None:
    """Test validation with specific rule IDs."""
    engine = QAEngine(registry=populated_registry)
    report = engine.validate(mock_presentation, rule_ids=["QA-L-001"])

    assert report.total_issues == 1
    assert report.error_count == 1
    assert report.issues[0].rule_id == "QA-L-001"


def test_validate_by_category(
    mock_presentation: Mock,
    populated_registry: QARuleRegistry,
) -> None:
    """Test validation filtered by category."""
    engine = QAEngine(registry=populated_registry)
    report = engine.validate(mock_presentation, categories=["layout"])

    assert report.total_issues == 2  # Two layout rules
    assert all(issue.rule_id in ["QA-L-001", "QA-L-002"] for issue in report.issues)


def test_validate_with_categories_method(
    mock_presentation: Mock,
    populated_registry: QARuleRegistry,
) -> None:
    """Test validate_with_categories convenience method."""
    engine = QAEngine(registry=populated_registry)
    report = engine.validate_with_categories(mock_presentation, ["content"])

    assert report.total_issues == 1
    assert report.issues[0].rule_id == "QA-C-001"


def test_validate_auto_fixable_only(
    mock_presentation: Mock,
    populated_registry: QARuleRegistry,
) -> None:
    """Test validation of only auto-fixable rules."""
    engine = QAEngine(registry=populated_registry)
    report = engine.validate_auto_fixable_only(mock_presentation)

    assert report.total_issues == 1
    assert report.issues[0].rule_id == "QA-L-002"
    assert report.issues[0].auto_fixable is True


def test_validate_rule_exception_handling(
    mock_presentation: Mock,
    empty_registry: QARuleRegistry,
) -> None:
    """Test engine handles rule exceptions gracefully."""

    class FailingRule:
        """Rule that raises exception."""

        rule_id = "QA-FAIL-001"
        description = "Failing rule"
        auto_fixable = False

        def validate(self, presentation: PresentationWrapper) -> list[QAIssue]:
            """Raise exception during validation.

            Args:
                presentation: Presentation to validate

            Raises:
                RuntimeError: Always raises
            """
            msg = "Rule failed"
            raise RuntimeError(msg)

    empty_registry.register(FailingRule(), "test")
    engine = QAEngine(registry=empty_registry)

    # Should not raise, should return empty report
    report = engine.validate(mock_presentation)
    assert report.total_issues == 0
    assert report.passed is True


def test_validate_nonexistent_rule_id(
    mock_presentation: Mock,
    populated_registry: QARuleRegistry,
) -> None:
    """Test validation with nonexistent rule ID."""
    engine = QAEngine(registry=populated_registry)
    report = engine.validate(mock_presentation, rule_ids=["QA-NONEXISTENT"])

    assert report.total_issues == 0


def test_validate_nonexistent_category(
    mock_presentation: Mock,
    populated_registry: QARuleRegistry,
) -> None:
    """Test validation with nonexistent category."""
    engine = QAEngine(registry=populated_registry)
    report = engine.validate(mock_presentation, categories=["nonexistent"])

    assert report.total_issues == 0


def test_report_passed_status(
    mock_presentation: Mock,
    empty_registry: QARuleRegistry,
) -> None:
    """Test report passed status based on error count."""
    # Add warning-only rule
    warning_issue = QAIssue(
        rule_id="QA-W-001",
        severity=Severity.WARNING,
        slide_index=0,
        message="Warning only",
    )
    warning_rule = MockRule("QA-W-001", "Warning rule", issues=[warning_issue])
    empty_registry.register(warning_rule)

    engine = QAEngine(registry=empty_registry)
    report = engine.validate(mock_presentation)

    assert report.warning_count == 1
    assert report.error_count == 0
    assert report.passed is True  # Warnings don't fail


def test_report_failed_status(
    mock_presentation: Mock,
    empty_registry: QARuleRegistry,
) -> None:
    """Test report failed status with errors."""
    error_issue = QAIssue(
        rule_id="QA-E-001",
        severity=Severity.ERROR,
        slide_index=0,
        message="Error",
    )
    error_rule = MockRule("QA-E-001", "Error rule", issues=[error_issue])
    empty_registry.register(error_rule)

    engine = QAEngine(registry=empty_registry)
    report = engine.validate(mock_presentation)

    assert report.error_count == 1
    assert report.passed is False


# Made with Bob
