"""
Unit tests for placeholder operations module.

Tests for placeholder search, bounds extraction, and removal operations
that are shared across ChartWrapper, TableWrapper, and ImageWrapper.

RED Phase: These tests should FAIL before implementation.
"""

from unittest.mock import MagicMock, patch

import pytest

from pptx_agent.pptx_wrapper.placeholder_ops import (
    find_placeholder,
    get_placeholder_bounds,
    remove_placeholder_safely,
)


class TestFindPlaceholder:
    """Tests for find_placeholder function."""

    def test_find_by_shape_name(self):
        """Should find placeholder by exact shape name match."""
        # Create mock slide with shapes
        slide = MagicMock()

        # Mock placeholder shape
        placeholder = MagicMock()
        placeholder.is_placeholder = True
        placeholder.name = "Content"
        placeholder.placeholder_format.type.name = "BODY"

        # Mock non-placeholder shape
        other_shape = MagicMock()
        other_shape.is_placeholder = False

        slide.shapes = [other_shape, placeholder]

        # Should find by name
        result = find_placeholder(slide, "Content")
        assert result == placeholder

    def test_find_by_placeholder_type(self):
        """Should find placeholder by placeholder type name."""
        slide = MagicMock()

        placeholder = MagicMock()
        placeholder.is_placeholder = True
        placeholder.name = "SomeOtherName"
        placeholder.placeholder_format.type.name = "TITLE"

        slide.shapes = [placeholder]

        # Should find by type name
        result = find_placeholder(slide, "TITLE")
        assert result == placeholder

    def test_placeholder_not_found(self):
        """Should return None when placeholder doesn't exist."""
        slide = MagicMock()

        shape = MagicMock()
        shape.is_placeholder = True
        shape.name = "Content"
        shape.placeholder_format.type.name = "BODY"

        slide.shapes = [shape]

        # Should return None for non-existent placeholder
        result = find_placeholder(slide, "NonexistentPlaceholder")
        assert result is None

    def test_ignores_non_placeholder_shapes(self):
        """Should skip shapes that are not placeholders."""
        slide = MagicMock()

        non_placeholder = MagicMock()
        non_placeholder.is_placeholder = False
        non_placeholder.name = "Content"

        slide.shapes = [non_placeholder]

        result = find_placeholder(slide, "Content")
        assert result is None

    def test_find_by_partial_match_with_fuzzy_disabled(self):
        """Should NOT find placeholder by partial match when fuzzy_match=False."""
        slide = MagicMock()

        placeholder = MagicMock()
        placeholder.is_placeholder = True
        placeholder.name = "Content Placeholder 1"
        placeholder.placeholder_format.type.name = "BODY"

        slide.shapes = [placeholder]

        # Should NOT find with fuzzy_match=False (default)
        result = find_placeholder(slide, "Content", fuzzy_match=False)
        assert result is None

    def test_find_by_partial_match_with_fuzzy_enabled(self):
        """Should find placeholder by partial match when fuzzy_match=True."""
        slide = MagicMock()

        placeholder = MagicMock()
        placeholder.is_placeholder = True
        placeholder.name = "Content Placeholder 1"
        placeholder.placeholder_format.type.name = "BODY"

        slide.shapes = [placeholder]

        # Should find with fuzzy_match=True
        result = find_placeholder(slide, "Content", fuzzy_match=True)
        assert result == placeholder

    def test_find_by_case_insensitive_match_with_fuzzy(self):
        """Should find placeholder by case-insensitive match when fuzzy_match=True."""
        slide = MagicMock()

        placeholder = MagicMock()
        placeholder.is_placeholder = True
        placeholder.name = "CONTENT Placeholder"
        placeholder.placeholder_format.type.name = "BODY"

        slide.shapes = [placeholder]

        # Should find with case-insensitive fuzzy match
        result = find_placeholder(slide, "content", fuzzy_match=True)
        assert result == placeholder

    def test_handles_attribute_error_gracefully(self):
        """Should handle AttributeError when accessing placeholder_format.type.name."""
        slide = MagicMock()

        placeholder = MagicMock()
        placeholder.is_placeholder = True
        placeholder.name = "Content"
        # Simulate AttributeError when accessing placeholder_format.type.name
        placeholder.placeholder_format.type.name = MagicMock(
            side_effect=AttributeError("type has no attribute name")
        )

        slide.shapes = [placeholder]

        # Should not crash and still find by name
        result = find_placeholder(slide, "Content")
        assert result == placeholder

    def test_generic_fallback_for_content(self):
        """Should find first non-title placeholder when searching for 'content'."""
        slide = MagicMock()

        title_placeholder = MagicMock()
        title_placeholder.is_placeholder = True
        title_placeholder.name = "Title 1"
        title_placeholder.placeholder_format.type.name = "TITLE"
        title_placeholder.text_frame = MagicMock()

        content_placeholder = MagicMock()
        content_placeholder.is_placeholder = True
        content_placeholder.name = "Text Placeholder 2"
        content_placeholder.placeholder_format.type.name = "BODY"
        content_placeholder.text_frame = MagicMock()

        slide.shapes = [title_placeholder, content_placeholder]

        # Should find content placeholder, skipping title
        result = find_placeholder(slide, "content", fuzzy_match=True)
        assert result == content_placeholder

    def test_generic_fallback_for_body(self):
        """Should find first non-title placeholder when searching for 'body'."""
        slide = MagicMock()

        title_placeholder = MagicMock()
        title_placeholder.is_placeholder = True
        title_placeholder.name = "Title 1"
        title_placeholder.placeholder_format.type.name = "TITLE"

        body_placeholder = MagicMock()
        body_placeholder.is_placeholder = True
        body_placeholder.name = "Body Placeholder"
        body_placeholder.placeholder_format.type.name = "BODY"
        body_placeholder.text_frame = MagicMock()

        slide.shapes = [title_placeholder, body_placeholder]

        # Should find body placeholder
        result = find_placeholder(slide, "body", fuzzy_match=True)
        assert result == body_placeholder

    def test_generic_fallback_with_attribute_error(self):
        """Should handle AttributeError during generic fallback."""
        slide = MagicMock()

        placeholder = MagicMock()
        placeholder.is_placeholder = True
        placeholder.name = "Some Placeholder"
        placeholder.text_frame = MagicMock()
        # Simulate AttributeError when accessing placeholder_format.type.name
        type(placeholder.placeholder_format).type = property(
            lambda _: MagicMock(name=MagicMock(side_effect=AttributeError))
        )

        slide.shapes = [placeholder]

        # Should use placeholder as fallback despite AttributeError
        result = find_placeholder(slide, "content", fuzzy_match=True)
        assert result == placeholder


class TestGetPlaceholderBounds:
    """Tests for get_placeholder_bounds function."""

    def test_extract_bounds(self):
        """Should extract left, top, width, height from placeholder."""
        placeholder = MagicMock()
        placeholder.left = 100
        placeholder.top = 200
        placeholder.width = 300
        placeholder.height = 400

        left, top, width, height = get_placeholder_bounds(placeholder)

        assert left == 100
        assert top == 200
        assert width == 300
        assert height == 400

    def test_bounds_with_different_values(self):
        """Should work with various dimension values."""
        placeholder = MagicMock()
        placeholder.left = 914400  # EMUs (English Metric Units)
        placeholder.top = 1828800
        placeholder.width = 7315200
        placeholder.height = 4572000

        left, top, width, height = get_placeholder_bounds(placeholder)

        assert left == 914400
        assert top == 1828800
        assert width == 7315200
        assert height == 4572000


class TestRemovePlaceholderSafely:
    """Tests for remove_placeholder_safely function."""

    def test_remove_placeholder_success(self):
        """Should safely remove placeholder using xml_utils."""
        placeholder = MagicMock()
        element = MagicMock()
        placeholder.element = element

        # Mock successful removal
        with (
            patch("pptx_agent.pptx_wrapper.placeholder_ops.safe_get_element") as mock_get,
            patch("pptx_agent.pptx_wrapper.placeholder_ops.safe_remove_element") as mock_remove,
        ):
            mock_get.return_value = element
            mock_remove.return_value = True

            # Should not raise exception
            remove_placeholder_safely(placeholder)

            mock_get.assert_called_once_with(placeholder, "element")
            mock_remove.assert_called_once_with(element)

    def test_remove_placeholder_failure(self):
        """Should raise ValueError when removal fails."""
        placeholder = MagicMock()
        element = MagicMock()
        placeholder.element = element

        with (
            patch("pptx_agent.pptx_wrapper.placeholder_ops.safe_get_element") as mock_get,
            patch("pptx_agent.pptx_wrapper.placeholder_ops.safe_remove_element") as mock_remove,
        ):
            mock_get.return_value = element
            mock_remove.return_value = False  # Removal failed

            with pytest.raises(ValueError, match="Placeholder removal failed"):
                remove_placeholder_safely(placeholder)

    def test_remove_placeholder_no_element(self):
        """Should raise ValueError when element cannot be accessed."""
        placeholder = MagicMock()

        with patch("pptx_agent.pptx_wrapper.placeholder_ops.safe_get_element") as mock_get:
            mock_get.return_value = None  # Element not found

            with pytest.raises(ValueError, match="Placeholder removal failed"):
                remove_placeholder_safely(placeholder)
