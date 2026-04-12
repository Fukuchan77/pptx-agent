# pyright: reportAttributeAccessIssue=false, reportUnknownParameterType=false, reportUnknownMemberType=false, reportUnusedVariable=false
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
        from lxml import etree

        # Create mock diagram data with 3 nodes (matching the test data)
        dgm_ns = "http://schemas.openxmlformats.org/drawingml/2006/diagram"
        a_ns = "http://schemas.openxmlformats.org/drawingml/2006/main"

        diagram_data = etree.Element(f"{{{dgm_ns}}}dataModel")
        for i in range(3):  # 3 nodes for the 3 steps
            pt = etree.SubElement(diagram_data, f"{{{dgm_ns}}}pt", type="node")
            t_elem = etree.SubElement(pt, f"{{{a_ns}}}t")
            t_elem.text = f"Original Step {i + 1}"

        # Create mock SmartArt shape
        mock_smartart_shape = Mock()
        mock_smartart_shape.name = "Content Placeholder"
        mock_smartart_shape._diagram_data = diagram_data  # Test mode attribute

        mock_pptx_slide = Mock()
        mock_pptx_slide.shapes = [mock_smartart_shape]
        slide = Mock()
        slide.slide = mock_pptx_slide

        smartart_block = SmartArtBlock(
            placeholder_name="Content Placeholder",
            diagram_type="process",
            nodes=[
                {"text": "Step 1", "level": 0},
                {"text": "Step 2", "level": 0},
                {"text": "Step 3", "level": 0},
            ],
        )

        # Act - Should successfully populate SmartArt
        add_smartart_to_slide(slide, smartart_block)

        # Assert - Verify text was updated in diagram data
        pt_nodes = diagram_data.findall(f".//{{{dgm_ns}}}pt[@type='node']")
        assert len(pt_nodes) == 3
        texts = []
        for pt in pt_nodes:
            t_elem = pt.find(f".//{{{a_ns}}}t")
            assert t_elem is not None
            texts.append(t_elem.text)
        assert texts == ["Step 1", "Step 2", "Step 3"]

    def test_add_smartart_hierarchy_diagram(self):
        """Test adding SmartArt with hierarchical structure."""
        # Arrange
        from lxml import etree

        # Create mock diagram data with 4 nodes (matching the test data)
        dgm_ns = "http://schemas.openxmlformats.org/drawingml/2006/diagram"
        a_ns = "http://schemas.openxmlformats.org/drawingml/2006/main"

        diagram_data = etree.Element(f"{{{dgm_ns}}}dataModel")
        original_texts = [
            "Original CEO",
            "Original Manager 1",
            "Original Manager 2",
            "Original Employee 1",
        ]
        for i in range(4):  # 4 nodes for hierarchy
            pt = etree.SubElement(diagram_data, f"{{{dgm_ns}}}pt", type="node")
            t_elem = etree.SubElement(pt, f"{{{a_ns}}}t")
            t_elem.text = original_texts[i]

        # Create mock SmartArt shape
        mock_smartart_shape = Mock()
        mock_smartart_shape.name = "Content Placeholder"
        mock_smartart_shape._diagram_data = diagram_data

        mock_pptx_slide = Mock()
        mock_pptx_slide.shapes = [mock_smartart_shape]
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

        # Act - Should successfully populate SmartArt
        add_smartart_to_slide(slide, smartart_block)

        # Assert - Verify text was updated in diagram data
        pt_nodes = diagram_data.findall(f".//{{{dgm_ns}}}pt[@type='node']")
        assert len(pt_nodes) == 4
        texts = []
        for pt in pt_nodes:
            t_elem = pt.find(f".//{{{a_ns}}}t")
            assert t_elem is not None
            texts.append(t_elem.text)
        assert texts == ["CEO", "Manager 1", "Manager 2", "Employee 1"]

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
        """Test that SmartArt implementation works with single node."""
        # Arrange
        from lxml import etree

        # Create mock diagram data with 1 node
        dgm_ns = "http://schemas.openxmlformats.org/drawingml/2006/diagram"
        a_ns = "http://schemas.openxmlformats.org/drawingml/2006/main"

        diagram_data = etree.Element(f"{{{dgm_ns}}}dataModel")
        pt = etree.SubElement(diagram_data, f"{{{dgm_ns}}}pt", type="node")
        t_elem = etree.SubElement(pt, f"{{{a_ns}}}t")
        t_elem.text = "Original Node"

        # Create mock SmartArt shape
        mock_smartart_shape = Mock()
        mock_smartart_shape.name = "Content Placeholder"
        mock_smartart_shape._diagram_data = diagram_data

        mock_pptx_slide = Mock()
        mock_pptx_slide.shapes = [mock_smartart_shape]
        slide = Mock()
        slide.slide = mock_pptx_slide

        smartart_block = SmartArtBlock(
            placeholder_name="Content Placeholder",
            diagram_type="process",
            nodes=[{"text": "Node 1", "level": 0}],
        )

        # Act - Should successfully populate SmartArt
        add_smartart_to_slide(slide, smartart_block)

        # Assert - Verify text was updated
        pt_nodes = diagram_data.findall(f".//{{{dgm_ns}}}pt[@type='node']")
        assert len(pt_nodes) == 1
        t_elem = pt_nodes[0].find(f".//{{{a_ns}}}t")
        assert t_elem is not None
        assert t_elem.text == "Node 1"
