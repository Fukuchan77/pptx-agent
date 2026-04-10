"""Unit tests for SmartArt builder functionality.

Tests the add_smartart_to_slide function that populates SmartArt diagrams
with node text content.
"""

from unittest.mock import Mock, patch

import pytest

from pptx_agent.pptx_wrapper.smartart_builder import add_smartart_to_slide
from pptx_agent.schemas.visual_assets import SmartArtBlock


class TestAddSmartArtToSlide:
    """Tests for add_smartart_to_slide function."""

    def test_add_smartart_basic_process_diagram(self):
        """Test adding SmartArt to slide with basic process diagram."""
        # Arrange
        mock_pptx_slide = Mock()
        mock_pptx_slide.shapes = []  # Empty shapes list
        slide = Mock()
        slide.slide = mock_pptx_slide  # SlideWrapper has public slide property

        smartart_block = SmartArtBlock(
            placeholder_name="Content Placeholder",
            diagram_type="process",
            nodes=[
                {"text": "Step 1", "level": 0},
                {"text": "Step 2", "level": 0},
                {"text": "Step 3", "level": 0},
            ],
        )

        # Act & Assert - Should raise NotImplementedError (SmartArt not yet implemented)
        with pytest.raises(NotImplementedError, match="SmartArt manipulation requires"):
            add_smartart_to_slide(slide, smartart_block)

    def test_add_smartart_hierarchy_diagram(self):
        """Test adding SmartArt with hierarchical structure."""
        # Arrange
        mock_pptx_slide = Mock()
        mock_pptx_slide.shapes = []  # Empty shapes list
        slide = Mock()
        slide.slide = mock_pptx_slide

        smartart_block = SmartArtBlock(
            placeholder_name="Content Placeholder",
            diagram_type="hierarchy",
            nodes=[
                {"text": "CEO", "level": 0},
                {"text": "Manager 1", "level": 1},
                {"text": "Manager 2", "level": 1},
                {"text": "Employee 1", "level": 2},
            ],
        )

        # Act & Assert - Should raise NotImplementedError (SmartArt not yet implemented)
        with pytest.raises(NotImplementedError, match="SmartArt manipulation requires"):
            add_smartart_to_slide(slide, smartart_block)

    def test_add_smartart_calls_wrapper_with_correct_params(self):
        """Test that smartart builder calls SmartArtWrapper with correct parameters."""
        # Arrange
        mock_pptx_slide = Mock()
        slide = Mock()
        slide.slide = mock_pptx_slide

        placeholder_name = "SmartArt Placeholder"
        nodes = [
            {"text": "Node 1", "level": 0},
            {"text": "Node 2", "level": 0},
        ]
        smartart_block = SmartArtBlock(
            placeholder_name=placeholder_name,
            diagram_type="process",
            nodes=nodes,
        )

        # Act
        with patch("pptx_agent.pptx_wrapper.smartart_builder.SmartArtWrapper") as mock_wrapper:
            add_smartart_to_slide(slide, smartart_block)

            # Assert - Should pass underlying slide object
            mock_wrapper.populate_smartart.assert_called_once_with(
                mock_pptx_slide, placeholder_name, nodes
            )

    def test_add_smartart_with_empty_nodes_list(self):
        """Test that adding SmartArt with empty nodes raises appropriate error."""
        # Act & Assert - SmartArtBlock validation should prevent empty nodes
        with pytest.raises(ValueError, match="at least 1 item"):
            SmartArtBlock(
                placeholder_name="Content Placeholder",
                diagram_type="process",
                nodes=[],  # Empty nodes should fail Pydantic validation
            )

    def test_add_smartart_not_implemented_warning(self):
        """Test that SmartArt implementation acknowledges complexity limitations."""
        # Arrange
        mock_pptx_slide = Mock()
        mock_pptx_slide.shapes = []  # Empty shapes causes ValueError
        slide = Mock()
        slide.slide = mock_pptx_slide

        smartart_block = SmartArtBlock(
            placeholder_name="Content Placeholder",
            diagram_type="process",
            nodes=[{"text": "Node 1", "level": 0}],
        )

        # Act & Assert - Should raise NotImplementedError per FR-039 specification
        with pytest.raises(NotImplementedError, match="SmartArt manipulation requires"):
            add_smartart_to_slide(slide, smartart_block)
