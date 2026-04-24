"""Auto-fix module for automatic issue remediation.

This module provides automatic correction strategies for fixable quality issues
detected by the QA engine.
"""

from pptx_agent.fixer.schemas import FixLoopResult, FixResult, FixStatus

__all__ = ["FixLoopResult", "FixResult", "FixStatus"]

# Made with Bob
