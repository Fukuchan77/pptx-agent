"""Registry for managing QA validation rules."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pptx_agent.qa.rules.base import QARule


class QARuleRegistry:
    """Registry for managing and accessing QA validation rules.

    Provides centralized registration and retrieval of QA rules. Rules are
    organized by category and can be filtered by various criteria.

    Example:
        >>> registry = QARuleRegistry()
        >>> registry.register(MyLayoutRule())
        >>> rules = registry.get_all_rules()
        >>> layout_rules = registry.get_rules_by_category("layout")
    """

    def __init__(self) -> None:
        """Initialize empty rule registry."""
        self._rules: dict[str, QARule] = {}
        self._categories: dict[str, list[str]] = {}

    def register(self, rule: "QARule", category: str = "general") -> None:
        """Register a QA rule with the registry.

        Args:
            rule: QA rule instance to register
            category: Category for organizing rules (e.g., "layout", "content")

        Raises:
            ValueError: If rule_id already registered
        """
        if rule.rule_id in self._rules:
            msg = f"Rule {rule.rule_id} already registered"
            raise ValueError(msg)

        self._rules[rule.rule_id] = rule

        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(rule.rule_id)

    def unregister(self, rule_id: str) -> bool:
        """Unregister a rule from the registry.

        Args:
            rule_id: ID of rule to unregister

        Returns:
            True if rule was unregistered, False if not found
        """
        if rule_id not in self._rules:
            return False

        # Remove from rules
        del self._rules[rule_id]

        # Remove from categories
        for category_rules in self._categories.values():
            if rule_id in category_rules:
                category_rules.remove(rule_id)

        return True

    def get_rule(self, rule_id: str) -> "QARule | None":
        """Get a specific rule by ID.

        Args:
            rule_id: ID of rule to retrieve

        Returns:
            Rule instance if found, None otherwise
        """
        return self._rules.get(rule_id)

    def get_all_rules(self) -> list["QARule"]:
        """Get all registered rules.

        Returns:
            List of all registered rule instances
        """
        return list(self._rules.values())

    def get_rules_by_category(self, category: str) -> list["QARule"]:
        """Get all rules in a specific category.

        Args:
            category: Category name to filter by

        Returns:
            List of rules in the specified category
        """
        rule_ids = self._categories.get(category, [])
        return [self._rules[rule_id] for rule_id in rule_ids]

    def get_auto_fixable_rules(self) -> list["QARule"]:
        """Get all rules that support auto-fixing.

        Returns:
            List of auto-fixable rules
        """
        return [rule for rule in self._rules.values() if rule.auto_fixable]

    def get_categories(self) -> list[str]:
        """Get list of all registered categories.

        Returns:
            List of category names
        """
        return list(self._categories.keys())

    def clear(self) -> None:
        """Clear all registered rules and categories."""
        self._rules.clear()
        self._categories.clear()

    def __len__(self) -> int:
        """Get number of registered rules.

        Returns:
            Count of registered rules
        """
        return len(self._rules)

    def __contains__(self, rule_id: str) -> bool:
        """Check if rule is registered.

        Args:
            rule_id: ID of rule to check

        Returns:
            True if rule is registered, False otherwise
        """
        return rule_id in self._rules


# Global registry instance
_global_registry = QARuleRegistry()


def get_global_registry() -> QARuleRegistry:
    """Get the global QA rule registry instance.

    Returns:
        Global registry instance
    """
    return _global_registry


# Made with Bob
