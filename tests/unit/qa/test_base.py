"""Unit tests for QA rule base protocol."""

from pptx_agent.qa.rules.base import QARule


def test_qa_rule_protocol_exists() -> None:
    """Test that QARule protocol is defined."""
    # QARule is a Protocol, so we just verify it exists and has expected attributes
    assert hasattr(QARule, "__annotations__")

    # Verify protocol defines expected attributes
    annotations = QARule.__annotations__
    assert "rule_id" in annotations
    assert "description" in annotations
    assert "auto_fixable" in annotations
    # Note: severity is not in the protocol, only in implementations


# Made with Bob
