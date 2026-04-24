"""Quality Assurance module for presentation validation.

This module provides automated quality checks for generated presentations,
detecting issues like text overflow, empty placeholders, and style violations.
"""

from pptx_agent.qa.schemas import QAIssue, QAReport, Severity

__all__ = ["QAIssue", "QAReport", "Severity"]

# Made with Bob
