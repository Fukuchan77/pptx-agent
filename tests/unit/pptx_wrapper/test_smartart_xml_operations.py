"""Unit tests for SmartArt XML manipulation operations.

Tests the populate_smartart method that performs direct XML manipulation
to replace text in existing SmartArt diagrams.
"""

from unittest.mock import Mock

import pytest
from lxml import etree


class TestSmartArtXMLOperations:
    """Tests for SmartArt XML manipulation."""

    def create_mock_smartart_xml(self, num_nodes: int) -> tuple[Mock, etree.Element]:
        """Create a mock slide with SmartArt XML structure.

        Args:
            num_nodes: Number of text nodes to create in the SmartArt

        Returns:
            Tuple of (mock_slide, diagram_data_element)
        """
        # Define XML namespaces
        DGM_NS = "http://schemas.openxmlformats.org/drawingml/2006/diagram"
        A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
        P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
        R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

        # Create diagram data XML structure
        nsmap = {
            "dgm": DGM_NS,
            "a": A_NS,
            "r": R_NS,
        }

        data_model = etree.Element(f"{{{DGM_NS}}}dataModel", nsmap=nsmap)
        pt_list = etree.SubElement(data_model, f"{{{DGM_NS}}}ptLst")

        # Create text nodes
        for i in range(num_nodes):
            pt = etree.SubElement(pt_list, f"{{{DGM_NS}}}pt", modelId=f"node_{i}", type="node")
            t_elem = etree.SubElement(pt, f"{{{DGM_NS}}}t")
            a_t = etree.SubElement(t_elem, f"{{{A_NS}}}t")
            a_t.text = f"Original text {i}"

        # Create mock slide with graphicFrame
        mock_slide = Mock()
        mock_slide._element = etree.Element(f"{{{P_NS}}}sld")
        sp_tree = etree.SubElement(mock_slide._element, f"{{{P_NS}}}spTree")
        graphic_frame = etree.SubElement(sp_tree, f"{{{P_NS}}}graphicFrame")

        # Set name attribute for placeholder identification
        nv_graphic_frame_pr = etree.SubElement(graphic_frame, f"{{{P_NS}}}nvGraphicFramePr")
        # Mock shapes to contain our graphic frame
        mock_shape = Mock()
        mock_shape._element = graphic_frame
        mock_shape.name = "SmartArt Test"

        # CRITICAL: Store diagram data directly on the mock shape
        # This allows the implementation's fallback mechanism to access it for testing
        mock_shape._diagram_data = data_model

        mock_slide.shapes = [mock_shape]

        return mock_slide, data_model

    def test_populate_smartart_process_basic_text_replacement(self):
        """Test basic text replacement in process SmartArt."""
        # Arrange
        mock_slide, diagram_data = self.create_mock_smartart_xml(3)

        text_items = [
            {"text": "Step 1", "level": 0},
            {"text": "Step 2", "level": 0},
            {"text": "Step 3", "level": 0},
        ]

        # Act
        from pptx_agent.pptx_wrapper.smartart import SmartArtWrapper

        SmartArtWrapper.populate_smartart(mock_slide, "SmartArt Test", text_items)

        # Assert - Verify text was replaced in XML
        DGM_NS = "http://schemas.openxmlformats.org/drawingml/2006/diagram"
        A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"

        pt_nodes = diagram_data.findall(f".//{{{DGM_NS}}}pt[@type='node']")
        assert len(pt_nodes) == 3

        for i, pt_node in enumerate(pt_nodes):
            a_t = pt_node.find(f".//{{{A_NS}}}t")
            assert a_t is not None
            assert a_t.text == text_items[i]["text"]

    def test_populate_smartart_hierarchy_multiple_levels(self):
        """Test hierarchy SmartArt with multiple organizational levels."""
        # Arrange
        mock_slide, diagram_data = self.create_mock_smartart_xml(4)

        text_items = [
            {"text": "CEO", "level": 0},
            {"text": "Manager 1", "level": 1},
            {"text": "Manager 2", "level": 1},
            {"text": "Employee", "level": 2},
        ]

        # Act
        from pptx_agent.pptx_wrapper.smartart import SmartArtWrapper

        SmartArtWrapper.populate_smartart(mock_slide, "SmartArt Test", text_items)

        # Assert
        DGM_NS = "http://schemas.openxmlformats.org/drawingml/2006/diagram"
        A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"

        pt_nodes = diagram_data.findall(f".//{{{DGM_NS}}}pt[@type='node']")
        assert len(pt_nodes) == 4

        for i, pt_node in enumerate(pt_nodes):
            a_t = pt_node.find(f".//{{{A_NS}}}t")
            assert a_t.text == text_items[i]["text"]

    def test_populate_smartart_cycle_circular_process(self):
        """Test cycle SmartArt for iterative processes."""
        # Arrange
        mock_slide, diagram_data = self.create_mock_smartart_xml(5)

        text_items = [
            {"text": "Plan", "level": 0},
            {"text": "Do", "level": 0},
            {"text": "Check", "level": 0},
            {"text": "Act", "level": 0},
            {"text": "Improve", "level": 0},
        ]

        # Act
        from pptx_agent.pptx_wrapper.smartart import SmartArtWrapper

        SmartArtWrapper.populate_smartart(mock_slide, "SmartArt Test", text_items)

        # Assert
        DGM_NS = "http://schemas.openxmlformats.org/drawingml/2006/diagram"
        A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"

        pt_nodes = diagram_data.findall(f".//{{{DGM_NS}}}pt[@type='node']")
        assert len(pt_nodes) == 5

        for i, pt_node in enumerate(pt_nodes):
            a_t = pt_node.find(f".//{{{A_NS}}}t")
            assert a_t.text == text_items[i]["text"]

    def test_populate_smartart_relationship_interconnections(self):
        """Test relationship SmartArt showing connections."""
        # Arrange
        mock_slide, diagram_data = self.create_mock_smartart_xml(4)

        text_items = [
            {"text": "Customer", "level": 0},
            {"text": "Product", "level": 0},
            {"text": "Service", "level": 0},
            {"text": "Support", "level": 0},
        ]

        # Act
        from pptx_agent.pptx_wrapper.smartart import SmartArtWrapper

        SmartArtWrapper.populate_smartart(mock_slide, "SmartArt Test", text_items)

        # Assert
        DGM_NS = "http://schemas.openxmlformats.org/drawingml/2006/diagram"
        A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"

        pt_nodes = diagram_data.findall(f".//{{{DGM_NS}}}pt[@type='node']")
        assert len(pt_nodes) == 4

        for i, pt_node in enumerate(pt_nodes):
            a_t = pt_node.find(f".//{{{A_NS}}}t")
            assert a_t.text == text_items[i]["text"]

    def test_populate_smartart_preserves_xml_structure(self):
        """Test that only text content is modified, structure is preserved."""
        # Arrange
        mock_slide, diagram_data = self.create_mock_smartart_xml(2)

        # Store original XML structure
        DGM_NS = "http://schemas.openxmlformats.org/drawingml/2006/diagram"
        original_pt_nodes = diagram_data.findall(f".//{{{DGM_NS}}}pt[@type='node']")
        original_model_ids = [pt.get("modelId") for pt in original_pt_nodes]

        text_items = [
            {"text": "New Text 1", "level": 0},
            {"text": "New Text 2", "level": 0},
        ]

        # Act
        from pptx_agent.pptx_wrapper.smartart import SmartArtWrapper

        SmartArtWrapper.populate_smartart(mock_slide, "SmartArt Test", text_items)

        # Assert - Structure preserved
        new_pt_nodes = diagram_data.findall(f".//{{{DGM_NS}}}pt[@type='node']")
        new_model_ids = [pt.get("modelId") for pt in new_pt_nodes]

        assert len(new_pt_nodes) == len(original_pt_nodes)
        assert new_model_ids == original_model_ids

    def test_populate_smartart_single_node(self):
        """Test SmartArt with single node."""
        # Arrange
        mock_slide, diagram_data = self.create_mock_smartart_xml(1)

        text_items = [{"text": "Single Item", "level": 0}]

        # Act
        from pptx_agent.pptx_wrapper.smartart import SmartArtWrapper

        SmartArtWrapper.populate_smartart(mock_slide, "SmartArt Test", text_items)

        # Assert
        DGM_NS = "http://schemas.openxmlformats.org/drawingml/2006/diagram"
        A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"

        pt_nodes = diagram_data.findall(f".//{{{DGM_NS}}}pt[@type='node']")
        assert len(pt_nodes) == 1

        a_t = pt_nodes[0].find(f".//{{{A_NS}}}t")
        assert a_t.text == "Single Item"

    def test_populate_smartart_large_node_count(self):
        """Test SmartArt with many nodes (stress test)."""
        # Arrange
        num_nodes = 10
        mock_slide, diagram_data = self.create_mock_smartart_xml(num_nodes)

        text_items = [{"text": f"Item {i + 1}", "level": 0} for i in range(num_nodes)]

        # Act
        from pptx_agent.pptx_wrapper.smartart import SmartArtWrapper

        SmartArtWrapper.populate_smartart(mock_slide, "SmartArt Test", text_items)

        # Assert
        DGM_NS = "http://schemas.openxmlformats.org/drawingml/2006/diagram"
        A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"

        pt_nodes = diagram_data.findall(f".//{{{DGM_NS}}}pt[@type='node']")
        assert len(pt_nodes) == num_nodes

        for i, pt_node in enumerate(pt_nodes):
            a_t = pt_node.find(f".//{{{A_NS}}}t")
            assert a_t.text == f"Item {i + 1}"

    def test_populate_smartart_placeholder_not_found(self):
        """Test error when SmartArt placeholder name doesn't match any shape."""
        # Arrange
        mock_slide, _ = self.create_mock_smartart_xml(3)
        text_items = [
            {"text": "Step 1", "level": 0},
            {"text": "Step 2", "level": 0},
            {"text": "Step 3", "level": 0},
        ]

        # Act & Assert - Should raise ValueError for non-existent placeholder
        from pptx_agent.pptx_wrapper.smartart import SmartArtWrapper

        with pytest.raises(
            ValueError, match="SmartArt placeholder 'InvalidName' not found in slide"
        ):
            SmartArtWrapper.populate_smartart(mock_slide, "InvalidName", text_items)

    def test_populate_smartart_node_count_mismatch_too_few(self):
        """Test error when fewer text items provided than SmartArt nodes."""
        # Arrange - Create SmartArt with 5 nodes
        mock_slide, _ = self.create_mock_smartart_xml(5)

        # Provide only 3 text items (too few)
        text_items = [
            {"text": "Item 1", "level": 0},
            {"text": "Item 2", "level": 0},
            {"text": "Item 3", "level": 0},
        ]

        # Act & Assert - Should raise ValueError for mismatch
        from pptx_agent.pptx_wrapper.smartart import SmartArtWrapper

        with pytest.raises(ValueError, match="SmartArt has 5 nodes but 3 text items provided"):
            SmartArtWrapper.populate_smartart(mock_slide, "SmartArt Test", text_items)

    def test_populate_smartart_node_count_mismatch_too_many(self):
        """Test error when more text items provided than SmartArt nodes."""
        # Arrange - Create SmartArt with 3 nodes
        mock_slide, _ = self.create_mock_smartart_xml(3)

        # Provide 5 text items (too many)
        text_items = [
            {"text": "Item 1", "level": 0},
            {"text": "Item 2", "level": 0},
            {"text": "Item 3", "level": 0},
            {"text": "Item 4", "level": 0},
            {"text": "Item 5", "level": 0},
        ]

        # Act & Assert - Should raise ValueError for mismatch
        from pptx_agent.pptx_wrapper.smartart import SmartArtWrapper

        with pytest.raises(ValueError, match="SmartArt has 3 nodes but 5 text items provided"):
            SmartArtWrapper.populate_smartart(mock_slide, "SmartArt Test", text_items)

    def test_populate_smartart_skips_non_node_dgm_elements(self):
        """Test that SmartArt correctly processes only dgm:pt elements with type='node'."""
        # Arrange - Create mock with mixed dgm:pt types
        from lxml import etree

        DGM_NS = "http://schemas.openxmlformats.org/drawingml/2006/diagram"
        A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
        P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
        R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

        nsmap = {"dgm": DGM_NS, "a": A_NS, "r": R_NS}
        data_model = etree.Element(f"{{{DGM_NS}}}dataModel", nsmap=nsmap)
        pt_list = etree.SubElement(data_model, f"{{{DGM_NS}}}ptLst")

        # Create nodes with type="node" (should be processed)
        for i in range(3):
            pt = etree.SubElement(pt_list, f"{{{DGM_NS}}}pt", modelId=f"node_{i}", type="node")
            t_elem = etree.SubElement(pt, f"{{{DGM_NS}}}t")
            a_t = etree.SubElement(t_elem, f"{{{A_NS}}}t")
            a_t.text = f"Original text {i}"

        # Create non-node elements (should be skipped)
        for i in range(2):
            pt = etree.SubElement(pt_list, f"{{{DGM_NS}}}pt", modelId=f"doc_{i}", type="doc")
            t_elem = etree.SubElement(pt, f"{{{DGM_NS}}}t")
            a_t = etree.SubElement(t_elem, f"{{{A_NS}}}t")
            a_t.text = f"Document text {i}"

        # Create mock slide
        from unittest.mock import Mock

        mock_slide = Mock()
        mock_slide._element = etree.Element(f"{{{P_NS}}}sld")
        sp_tree = etree.SubElement(mock_slide._element, f"{{{P_NS}}}spTree")
        graphic_frame = etree.SubElement(sp_tree, f"{{{P_NS}}}graphicFrame")

        mock_shape = Mock()
        mock_shape._element = graphic_frame
        mock_shape.name = "SmartArt Test"
        mock_shape._diagram_data = data_model
        mock_slide.shapes = [mock_shape]

        # Provide text items matching only type="node" elements (3 items)
        text_items = [
            {"text": "New Node 1", "level": 0},
            {"text": "New Node 2", "level": 0},
            {"text": "New Node 3", "level": 0},
        ]

        # Act - Should succeed with 3 text items for 3 nodes (ignoring doc types)
        from pptx_agent.pptx_wrapper.smartart import SmartArtWrapper

        SmartArtWrapper.populate_smartart(mock_slide, "SmartArt Test", text_items)

        # Assert - Only type="node" elements should be updated
        pt_nodes = data_model.findall(f".//{{{DGM_NS}}}pt[@type='node']")
        assert len(pt_nodes) == 3

        for i, pt_node in enumerate(pt_nodes):
            a_t = pt_node.find(f".//{{{A_NS}}}t")
            assert a_t.text == text_items[i]["text"]

        # Verify doc type elements were not modified
        pt_docs = data_model.findall(f".//{{{DGM_NS}}}pt[@type='doc']")
        assert len(pt_docs) == 2
        for i, pt_doc in enumerate(pt_docs):
            a_t = pt_doc.find(f".//{{{A_NS}}}t")
            assert a_t.text == f"Document text {i}"  # Original text preserved
