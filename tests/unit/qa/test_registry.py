"""Unit tests for QA rule registry."""

import pytest

from pptx_agent.qa.rules.layout_checks import EmptyPlaceholderRule, TextOverflowRule
from pptx_agent.qa.rules.registry import QARuleRegistry


def test_registry_register_rule() -> None:
    """Test registering a single rule."""
    registry = QARuleRegistry()
    rule = TextOverflowRule()

    registry.register(rule)

    assert len(registry.get_all_rules()) == 1
    assert registry.get_all_rules()[0].rule_id == "QA-L-001"


def test_registry_get_rule_by_id() -> None:
    """Test retrieving a rule by ID."""
    registry = QARuleRegistry()
    rule = TextOverflowRule()
    registry.register(rule)

    retrieved = registry.get_rule("QA-L-001")

    assert retrieved is not None
    assert retrieved.rule_id == "QA-L-001"


def test_registry_get_nonexistent_rule() -> None:
    """Test retrieving a non-existent rule returns None."""
    registry = QARuleRegistry()

    retrieved = registry.get_rule("NONEXISTENT")

    assert retrieved is None


def test_registry_get_all_rules() -> None:
    """Test getting all registered rules."""
    registry = QARuleRegistry()
    rule1 = TextOverflowRule()
    rule2 = EmptyPlaceholderRule()  # Different type

    registry.register(rule1)
    registry.register(rule2)

    # Should have 2 rules (different types)
    assert len(registry.get_all_rules()) == 2


def test_registry_clear() -> None:
    """Test clearing all rules from registry."""
    registry = QARuleRegistry()
    rule = TextOverflowRule()
    registry.register(rule)

    assert len(registry.get_all_rules()) == 1

    registry.clear()

    assert len(registry.get_all_rules()) == 0


def test_registry_duplicate_registration() -> None:
    """Test that registering the same rule_id twice raises ValueError."""
    registry = QARuleRegistry()
    rule1 = TextOverflowRule()
    rule2 = TextOverflowRule()  # Same rule_id, different instance

    registry.register(rule1)

    # Registering another rule with same rule_id should raise ValueError
    with pytest.raises(ValueError, match="Rule QA-L-001 already registered"):
        registry.register(rule2)


# Made with Bob
