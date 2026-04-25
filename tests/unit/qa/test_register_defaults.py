"""Unit tests for QA rule registration."""

from pptx_agent.qa.engine import QAEngine
from pptx_agent.qa.rules.register_defaults import register_default_rules


def test_register_default_rules_populates_registry() -> None:
    """Test that register_default_rules adds all expected rules to the registry."""
    engine = QAEngine()

    # Note: Registry may already have rules from module import
    # Just verify we have the expected rules after registration
    register_default_rules()

    # Registry should contain all default rules
    rules = engine.registry.get_all_rules()
    assert len(rules) >= 16  # At least 16 default rules

    # Verify we have rules from all categories
    rule_ids = {rule.rule_id for rule in rules}

    # Layout rules (QA-L-001 through QA-L-006)
    assert "QA-L-001" in rule_ids  # TextOverflowRule
    assert "QA-L-002" in rule_ids  # EmptyPlaceholderRule
    assert "QA-L-003" in rule_ids  # UnpopulatedPlaceholderRule
    assert "QA-L-004" in rule_ids  # OverlappingObjectsRule
    assert "QA-L-005" in rule_ids  # BoundaryOverflowRule
    assert "QA-L-006" in rule_ids  # MinimumFontSizeRule

    # Content rules (QA-C-001 through QA-C-006)
    assert "QA-C-001" in rule_ids  # BulletLengthRule
    assert "QA-C-002" in rule_ids  # DuplicateTitleRule
    assert "QA-C-003" in rule_ids  # UnpopulatedImagePlaceholderRule
    assert "QA-C-004" in rule_ids  # PathologicalTableDimensionRule
    assert "QA-C-005" in rule_ids  # MissingChartDataRule
    assert "QA-C-006" in rule_ids  # SpeakerNotesVerificationRule

    # Style rules (QA-S-001 through QA-S-004)
    assert "QA-S-001" in rule_ids  # OffTemplateFontRule
    assert "QA-S-002" in rule_ids  # OffTemplateColorRule
    assert "QA-S-003" in rule_ids  # InvalidBulletIndentRule
    assert "QA-S-004" in rule_ids  # TemplateConformanceRule


def test_register_default_rules_idempotent() -> None:
    """Test that calling register_default_rules multiple times doesn't duplicate rules."""
    engine = QAEngine()

    # Register rules twice
    register_default_rules()
    first_count = len(engine.registry.get_all_rules())

    register_default_rules()
    second_count = len(engine.registry.get_all_rules())

    # Count should be the same (no duplicates)
    assert first_count == second_count


def test_all_registered_rules_have_required_attributes() -> None:
    """Test that all registered rules have required attributes."""
    engine = QAEngine()
    register_default_rules()

    rules = engine.registry.get_all_rules()

    for rule in rules:
        # Required attributes
        assert hasattr(rule, "rule_id"), "Rule missing rule_id attribute"
        assert hasattr(rule, "severity"), f"Rule {rule.rule_id} missing severity attribute"
        assert hasattr(rule, "auto_fixable"), f"Rule {rule.rule_id} missing auto_fixable attribute"
        assert hasattr(rule, "validate"), f"Rule {rule.rule_id} missing validate method"

        # Verify severity is valid
        severity_value = getattr(rule, "severity", None)
        assert severity_value in ["error", "warning", "info"], (
            f"Rule {rule.rule_id} has invalid severity {severity_value}"
        )

        # Verify auto_fixable is boolean
        assert isinstance(rule.auto_fixable, bool), (
            f"Rule {rule.rule_id} auto_fixable is not boolean"
        )


def test_registered_rules_have_unique_ids() -> None:
    """Test that all registered rules have unique rule IDs."""
    engine = QAEngine()
    register_default_rules()

    rules = engine.registry.get_all_rules()
    rule_ids = [rule.rule_id for rule in rules]

    # Check for duplicates
    assert len(rule_ids) == len(set(rule_ids)), "Duplicate rule IDs found"


# Made with Bob
