"""Tests for safe XML manipulation utilities."""

from unittest.mock import Mock

import pytest

from pptx_agent.pptx_wrapper.xml_utils import safe_get_element, safe_remove_element


class TestSafeRemoveElement:
    """Tests for safe_remove_element function."""

    def test_safe_remove_element_success(self):
        """Test successful removal of element with parent."""
        # RED PHASE: Writing failing test for safe_remove_element
        parent = Mock()
        element = Mock()
        element.getparent.return_value = parent

        result = safe_remove_element(element)

        assert result is True
        parent.remove.assert_called_once_with(element)

    def test_safe_remove_element_no_parent(self):
        """Test removal fails when element has no parent."""
        # RED PHASE: Writing failing test for no parent case
        element = Mock()
        element.getparent.return_value = None

        with pytest.raises(ValueError, match="Element has no parent, cannot remove"):
            safe_remove_element(element)

    def test_safe_remove_element_attribute_error(self):
        """Test removal fails gracefully on AttributeError."""
        # RED PHASE: Writing failing test for AttributeError case
        element = Mock()
        element.getparent.side_effect = AttributeError("No getparent method")

        result = safe_remove_element(element)

        assert result is False

    def test_safe_remove_element_type_error(self):
        """Test removal fails gracefully on TypeError."""
        # RED PHASE: Writing failing test for TypeError case
        element = Mock()
        parent = Mock()
        element.getparent.return_value = parent
        parent.remove.side_effect = TypeError("Cannot remove")

        result = safe_remove_element(element)

        assert result is False


class TestSafeGetElement:
    """Tests for safe_get_element function."""

    def test_safe_get_element_success(self):
        """Test successful access to _element attribute."""
        # RED PHASE: Writing failing test for safe_get_element
        obj = Mock()
        mock_element = Mock()
        obj._element = mock_element

        result = safe_get_element(obj)

        assert result is mock_element

    def test_safe_get_element_custom_attr(self):
        """Test access to custom element attribute."""
        # RED PHASE: Writing failing test for custom attribute
        obj = Mock()
        mock_element = Mock()
        obj.custom_element = mock_element

        result = safe_get_element(obj, "custom_element")

        assert result is mock_element

    def test_safe_get_element_none(self):
        """Test when element attribute is None."""
        # RED PHASE: Writing failing test for None element
        obj = Mock()
        obj._element = None

        result = safe_get_element(obj)

        assert result is None

    def test_safe_get_element_attribute_error(self):
        """Test when object has no element attribute."""
        # RED PHASE: Writing failing test for missing attribute
        obj = Mock(spec=[])  # Mock with no attributes

        result = safe_get_element(obj)

        assert result is None

    def test_safe_get_element_with_spec(self):
        """Test with object that doesn't have the attribute in spec."""
        # RED PHASE: Writing failing test for spec-limited mock
        obj = Mock(spec=["other_attr"])

        result = safe_get_element(obj, "_element")

        assert result is None
