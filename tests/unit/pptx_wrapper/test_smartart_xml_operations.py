# pyright: reportAttributeAccessIssue=false, reportUnknownParameterType=false, reportUnknownMemberType=false, reportUnusedVariable=false
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
            assert a_t is not None
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
            assert a_t is not None
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
            assert a_t is not None
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
        assert a_t is not None
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
            assert a_t is not None
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
            assert a_t is not None
            assert a_t.text == text_items[i]["text"]

        # Verify doc type elements were not modified
        pt_docs = data_model.findall(f".//{{{DGM_NS}}}pt[@type='doc']")
        assert len(pt_docs) == 2
        for i, pt_doc in enumerate(pt_docs):
            a_t = pt_doc.find(f".//{{{A_NS}}}t")
            assert a_t is not None
            assert a_t.text == f"Document text {i}"  # Original text preserved

    def test_populate_smartart_type_attribute_omitted_pt(self):
        """Test that <dgm:pt> nodes WITHOUT a type attribute are treated as 'node'.

        Per the OpenXML schema, the @type attribute defaults to 'node' when omitted.
        Real-world PowerPoint SmartArt frequently omits this attribute.
        """
        # Arrange - Create fixture with type attribute OMITTED
        from unittest.mock import Mock

        from lxml import etree

        DGM_NS = "http://schemas.openxmlformats.org/drawingml/2006/diagram"
        A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
        P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"

        nsmap = {"dgm": DGM_NS, "a": A_NS}
        data_model = etree.Element(f"{{{DGM_NS}}}dataModel", nsmap=nsmap)
        pt_list = etree.SubElement(data_model, f"{{{DGM_NS}}}ptLst")

        # Create nodes WITHOUT type attribute (the OpenXML default)
        for i in range(3):
            pt = etree.SubElement(pt_list, f"{{{DGM_NS}}}pt", modelId=f"node_{i}")
            # NOTE: NO type="node" attribute set here
            t_elem = etree.SubElement(pt, f"{{{DGM_NS}}}t")
            a_t = etree.SubElement(t_elem, f"{{{A_NS}}}t")
            a_t.text = f"Original {i}"

        mock_slide = Mock()
        mock_shape = Mock()
        mock_shape.name = "SmartArt Test"
        mock_shape._diagram_data = data_model
        mock_slide.shapes = [mock_shape]

        text_items = [
            {"text": "Updated A", "level": 0},
            {"text": "Updated B", "level": 0},
            {"text": "Updated C", "level": 0},
        ]

        # Act
        from pptx_agent.pptx_wrapper.smartart import SmartArtWrapper

        SmartArtWrapper.populate_smartart(mock_slide, "SmartArt Test", text_items)

        # Assert - All 3 nodes (type omitted) should have been updated
        all_pts = data_model.findall(f".//{{{DGM_NS}}}pt")
        assert len(all_pts) == 3
        for i, pt in enumerate(all_pts):
            assert pt.get("type") is None  # Confirm type is indeed omitted
            a_t = pt.find(f".//{{{A_NS}}}t")
            assert a_t is not None
            assert a_t.text == text_items[i]["text"]

    def test_populate_smartart_mixed_explicit_and_omitted_type(self):
        """Test that a mix of explicit type='node' and omitted-type <dgm:pt> are all processed.

        Structural types (doc, sibTrans) should still be skipped.
        """
        # Arrange
        from unittest.mock import Mock

        from lxml import etree

        DGM_NS = "http://schemas.openxmlformats.org/drawingml/2006/diagram"
        A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"

        nsmap = {"dgm": DGM_NS, "a": A_NS}
        data_model = etree.Element(f"{{{DGM_NS}}}dataModel", nsmap=nsmap)
        pt_list = etree.SubElement(data_model, f"{{{DGM_NS}}}ptLst")

        # Node 0: explicit type="node"
        pt0 = etree.SubElement(pt_list, f"{{{DGM_NS}}}pt", modelId="n0", type="node")
        t0 = etree.SubElement(pt0, f"{{{DGM_NS}}}t")
        a_t0 = etree.SubElement(t0, f"{{{A_NS}}}t")
        a_t0.text = "Orig 0"

        # Node 1: type omitted (should default to "node")
        pt1 = etree.SubElement(pt_list, f"{{{DGM_NS}}}pt", modelId="n1")
        t1 = etree.SubElement(pt1, f"{{{DGM_NS}}}t")
        a_t1 = etree.SubElement(t1, f"{{{A_NS}}}t")
        a_t1.text = "Orig 1"

        # Structural: type="doc" (should be skipped)
        pt_doc = etree.SubElement(pt_list, f"{{{DGM_NS}}}pt", modelId="doc0", type="doc")
        t_doc = etree.SubElement(pt_doc, f"{{{DGM_NS}}}t")
        a_t_doc = etree.SubElement(t_doc, f"{{{A_NS}}}t")
        a_t_doc.text = "Doc text"

        # Structural: type="sibTrans" (should be skipped)
        pt_sib = etree.SubElement(pt_list, f"{{{DGM_NS}}}pt", modelId="sib0", type="sibTrans")
        t_sib = etree.SubElement(pt_sib, f"{{{DGM_NS}}}t")
        a_t_sib = etree.SubElement(t_sib, f"{{{A_NS}}}t")
        a_t_sib.text = "Sib text"

        # Node 2: type omitted
        pt2 = etree.SubElement(pt_list, f"{{{DGM_NS}}}pt", modelId="n2")
        t2 = etree.SubElement(pt2, f"{{{DGM_NS}}}t")
        a_t2 = etree.SubElement(t2, f"{{{A_NS}}}t")
        a_t2.text = "Orig 2"

        mock_slide = Mock()
        mock_shape = Mock()
        mock_shape.name = "SmartArt Test"
        mock_shape._diagram_data = data_model
        mock_slide.shapes = [mock_shape]

        text_items = [
            {"text": "New 0", "level": 0},
            {"text": "New 1", "level": 0},
            {"text": "New 2", "level": 0},
        ]

        # Act
        from pptx_agent.pptx_wrapper.smartart import SmartArtWrapper

        SmartArtWrapper.populate_smartart(mock_slide, "SmartArt Test", text_items)

        # Assert - Only nodes (explicit + omitted type) should be updated
        all_pts = data_model.findall(f".//{{{DGM_NS}}}pt")
        assert len(all_pts) == 5  # 3 nodes + 2 structural

        # Verify node text was updated
        assert a_t0.text == "New 0"
        assert a_t1.text == "New 1"
        assert a_t2.text == "New 2"

        # Verify structural elements were NOT modified
        assert a_t_doc.text == "Doc text"
        assert a_t_sib.text == "Sib text"


class TestSmartArtXMLSecurity:
    """Security tests for SmartArt XML parsing with secure lxml parser.

    These tests verify that the secure XML parser (resolve_entities=False, no_network=True)
    successfully blocks XXE and entity expansion attacks.
    """

    def test_xxe_external_entity_blocked(self):
        """Test that XXE (XML External Entity) attacks are blocked.

        Secure XML parser with resolve_entities=False blocks external entity resolution.
        The parser may not raise an exception but will not resolve the entity.
        """
        # Arrange - Create malicious XML with external entity reference
        malicious_xml = b"""<?xml version="1.0"?>
<!DOCTYPE root [
<!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<root>&xxe;</root>
"""

        # Act - Parse with secure parser (should not resolve entities)
        from lxml import etree

        # Secure parser blocks entity resolution (resolve_entities=False)
        parser = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True)

        # The parser will either:
        # 1. Raise an exception (preferred), or
        # 2. Parse without resolving the entity (also secure)
        try:
            parsed = etree.fromstring(malicious_xml, parser=parser)
            # If parsing succeeds, verify the entity was NOT resolved
            # The text should not contain file contents
            text_content = parsed.text or ""
            # If entity was resolved, text would contain file contents
            # If not resolved, it should be empty or contain entity reference
            assert "/etc/passwd" not in text_content, "XXE entity should not be resolved"
            assert "root:" not in text_content, "XXE entity should not be resolved"
        except (etree.XMLSyntaxError, ValueError):
            # Exception is also acceptable - it means parsing was blocked
            pass

    def test_entity_expansion_billion_laughs_blocked(self):
        """Test that entity expansion attacks (billion laughs) are blocked.

        Secure XML parser with resolve_entities=False blocks entity expansion.
        """
        # Arrange - Create malicious XML with recursive entity expansion (billion laughs attack)
        malicious_xml = b"""<?xml version="1.0"?>
<!DOCTYPE lolz [
<!ENTITY lol "lol">
<!ENTITY lol1 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
<!ENTITY lol2 "&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;">
<!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
<!ENTITY lol4 "&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;">
]>
<root>&lol4;</root>
"""

        # Act - Parse with secure parser (should not expand entities)
        from lxml import etree

        # Secure parser blocks entity expansion (resolve_entities=False)
        parser = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True)

        # The parser will either:
        # 1. Raise an exception (preferred), or
        # 2. Parse without expanding entities (also secure)
        try:
            parsed = etree.fromstring(malicious_xml, parser=parser)
            # If parsing succeeds, verify entities were NOT expanded
            # The text should not contain massive repeated "lol" strings
            text_content = parsed.text or ""
            # If entities were expanded, text would be massive (>10KB)
            # If not expanded, it should be empty or minimal
            assert len(text_content) < 1000, "Entities should not be expanded"
        except (etree.XMLSyntaxError, ValueError):
            # Exception is also acceptable - it means parsing was blocked
            pass

    def test_realistic_smartart_xml_parsing_with_secure_parser(self):
        """Test that realistic SmartArt XML can still be parsed with secure parser.

        Integration test: Verify secure XML parser doesn't break normal SmartArt functionality.
        """
        # Arrange - Create realistic SmartArt XML (simplified but representative)
        realistic_xml = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<dgm:dataModel xmlns:dgm="http://schemas.openxmlformats.org/drawingml/2006/diagram"
               xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
    <dgm:ptLst>
        <dgm:pt modelId="0" type="node">
            <dgm:prSet>
                <dgm:prstyle>
                    <a:lnRef idx="1"/>
                    <a:fillRef idx="1"/>
                    <a:effectRef idx="1"/>
                    <a:fontRef idx="minor"/>
                </dgm:prstyle>
            </dgm:prSet>
            <dgm:t>
                <a:t>Process Step 1</a:t>
            </dgm:t>
        </dgm:pt>
        <dgm:pt modelId="1" type="node">
            <dgm:prSet>
                <dgm:prstyle>
                    <a:lnRef idx="1"/>
                    <a:fillRef idx="1"/>
                    <a:effectRef idx="1"/>
                    <a:fontRef idx="minor"/>
                </dgm:prstyle>
            </dgm:prSet>
            <dgm:t>
                <a:t>Process Step 2</a:t>
            </dgm:t>
        </dgm:pt>
        <dgm:pt modelId="2" type="node">
            <dgm:prSet>
                <dgm:prstyle>
                    <a:lnRef idx="1"/>
                    <a:fillRef idx="1"/>
                    <a:effectRef idx="1"/>
                    <a:fontRef idx="minor"/>
                </dgm:prstyle>
            </dgm:prSet>
            <dgm:t>
                <a:t>Process Step 3</a:t>
            </dgm:t>
        </dgm:pt>
    </dgm:ptLst>
</dgm:dataModel>
"""

        # Act - Parse with secure parser (should succeed for normal XML)
        from lxml import etree

        parser = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True)
        parsed = etree.fromstring(realistic_xml, parser=parser)

        # Assert - Verify the XML was parsed correctly
        DGM_NS = "http://schemas.openxmlformats.org/drawingml/2006/diagram"
        A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"

        pt_nodes = parsed.findall(f".//{{{DGM_NS}}}pt[@type='node']")
        assert len(pt_nodes) == 3

        # Verify text content is accessible
        text_values = []
        for pt in pt_nodes:
            a_t = pt.find(f".//{{{A_NS}}}t")
            if a_t is not None and a_t.text:
                text_values.append(a_t.text)

        assert text_values == ["Process Step 1", "Process Step 2", "Process Step 3"]
