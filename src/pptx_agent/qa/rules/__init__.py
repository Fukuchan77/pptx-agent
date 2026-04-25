"""QA validation rules."""

from pptx_agent.qa.rules.base import QARule
from pptx_agent.qa.rules.layout_checks import (
    BoundaryOverflowRule,
    EmptyPlaceholderRule,
    MinimumFontSizeRule,
    OverlappingObjectsRule,
    TextOverflowRule,
    UnpopulatedPlaceholderRule,
)
from pptx_agent.qa.rules.registry import QARuleRegistry, get_global_registry

__all__ = [
    "BoundaryOverflowRule",
    "EmptyPlaceholderRule",
    "MinimumFontSizeRule",
    "OverlappingObjectsRule",
    "QARule",
    "QARuleRegistry",
    "TextOverflowRule",
    "UnpopulatedPlaceholderRule",
    "get_global_registry",
]


# Made with Bob
