"""QA validation rules and registry."""

from pptx_agent.qa.rules.base import QARule
from pptx_agent.qa.rules.registry import QARuleRegistry, get_global_registry

__all__ = [
    "QARule",
    "QARuleRegistry",
    "get_global_registry",
]

# Made with Bob
