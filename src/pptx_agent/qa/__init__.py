"""Quality Assurance module for presentation validation.

This module provides automated quality checks for generated presentations,
detecting issues like text overflow, empty placeholders, and style violations.
"""

from pptx_agent.qa.engine import QAEngine

# Import to auto-register default rules
from pptx_agent.qa.rules import (
    QARule,
    QARuleRegistry,
    get_global_registry,
    register_defaults,  # noqa: F401  # pyright: ignore[reportUnusedImport]
)
from pptx_agent.qa.schemas import QAIssue, QAReport, Severity

__all__ = [
    "QAEngine",
    "QAIssue",
    "QAReport",
    "QARule",
    "QARuleRegistry",
    "Severity",
    "get_global_registry",
]

# Made with Bob
