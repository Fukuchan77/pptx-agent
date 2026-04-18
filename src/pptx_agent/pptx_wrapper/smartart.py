"""SmartArt wrapper with XML manipulation.

Version Compatibility Note:
    This module requires python-pptx>=1.0,<2.0 due to dependency on the
    private Part._blob attribute for SmartArt XML manipulation. The version
    constraint in pyproject.toml ensures compatibility. Runtime validation
    occurs in populate_smartart() when _blob is actually accessed.
"""

import logging
from typing import Any

from defusedxml.lxml import fromstring
from lxml import etree
from pptx.slide import Slide

# XML Namespaces for OpenXML diagram manipulation
DGM_NS = "http://schemas.openxmlformats.org/drawingml/2006/diagram"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

logger = logging.getLogger(__name__)


class SmartArtWrapper:
    """Wrapper for SmartArt diagram population.

    Note: SmartArt manipulation through python-pptx is complex due to
    the underlying XML structure. This implementation provides basic
    text-only replacement functionality for existing SmartArt diagrams.
    """

    @staticmethod
    def populate_smartart(slide: Slide, placeholder_name: str, nodes: list[dict[str, Any]]) -> None:
        """Populate SmartArt diagram with node data via XML manipulation.

        This implementation performs direct XML manipulation to replace text
        in existing SmartArt shapes. It preserves the SmartArt structure,
        layout, colors, and styling - only text content is modified.

        Args:
            slide: Slide containing SmartArt
            placeholder_name: Name of placeholder containing SmartArt
            nodes: List of node data, each with structure:
                {"text": str, "level": int}

        Raises:
            ValueError: If SmartArt placeholder not found or node count mismatch

        Example:
            >>> nodes = [
            ...     {"text": "Main Item", "level": 0},
            ...     {"text": "Sub Item 1", "level": 1},
            ...     {"text": "Sub Item 2", "level": 1},
            ... ]
            >>> SmartArtWrapper.populate_smartart(slide, "SmartArt", nodes)
        """
        # Extract text items from nodes with validation
        try:
            text_items = [node["text"] for node in nodes]
        except KeyError as e:
            msg = "Each node must have a 'text' key"
            raise ValueError(msg) from e

        if any(not text for text in text_items):
            msg = "Empty text is not allowed in SmartArt nodes"
            raise ValueError(msg)

        # Find the SmartArt shape by name
        smartart_shape = None
        for shape in slide.shapes:
            if hasattr(shape, "name") and shape.name == placeholder_name:
                smartart_shape = shape
                break

        if smartart_shape is None:
            msg = f"SmartArt placeholder '{placeholder_name}' not found in slide"
            raise ValueError(msg)

        # Check for test mode first: if shape has _diagram_data, use it directly
        # This allows tests to bypass the complex relationship navigation
        diagram_part = None
        if hasattr(smartart_shape, "_diagram_data"):
            diagram_data = smartart_shape._diagram_data  # type: ignore[attr-defined]
            logger.debug("Using direct diagram data access (test mode)")
        else:
            # Production mode: Navigate through relationships to get diagram data
            # Access the underlying XML element
            shape_elem = smartart_shape._element  # type: ignore[attr-defined]

            # Find the graphicFrame element (SmartArt is represented as a graphicFrame)
            graphic_frame = shape_elem
            if graphic_frame.tag != f"{{{P_NS}}}graphicFrame":
                # If the shape element itself is not a graphicFrame, search for it
                graphic_frames = shape_elem.findall(f".//{{{P_NS}}}graphicFrame")
                if graphic_frames:
                    graphic_frame = graphic_frames[0]

            # Navigate to diagram data through relationships
            # SmartArt diagrams reference external diagram data parts
            try:
                # Get the graphic element
                graphic = graphic_frame.find(f".//{{{A_NS}}}graphic")
                if graphic is None:
                    msg = "Could not find graphic element in SmartArt shape"
                    raise ValueError(msg)

                # Get the graphicData element
                graphic_data = graphic.find(f".//{{{A_NS}}}graphicData")
                if graphic_data is None:
                    msg = "Could not find graphicData element in SmartArt shape"
                    raise ValueError(msg)

                # Find the relationship to the diagram data part
                rel_elem = graphic_data.find(f".//{{{DGM_NS}}}relIds")
                if rel_elem is None:
                    msg = "Could not find diagram relationship element"
                    raise ValueError(msg)

                # Get the data relationship ID
                data_rel_id = rel_elem.get(f"{{{R_NS}}}dm")
                if not data_rel_id:
                    msg = "Could not find diagram data relationship ID"
                    raise ValueError(msg)

                # Get the diagram data part through the relationship.
                # python-pptx has no registered factory for SmartArt diagram
                # data parts, so they load as a base Part — which exposes only
                # `blob`, not `_element`. Parse the blob ourselves and write
                # the modified XML back via `_blob` after mutation.
                part_rels = slide.part.rels
                if data_rel_id not in part_rels:
                    msg = f"Diagram data relationship '{data_rel_id}' not found"
                    raise ValueError(msg)

                diagram_part = part_rels[data_rel_id].target_part
                diagram_data = fromstring(diagram_part.blob)

            except (AttributeError, KeyError, etree.XMLSyntaxError) as e:
                msg = f"Could not access SmartArt diagram data (XML parse may have failed): {e}"
                raise ValueError(msg) from e

        # Find all content nodes in the diagram data. The dgm:pt @type
        # attribute defaults to "node" when omitted (per the OpenXML schema),
        # so real-world SmartArt rarely sets it explicitly. Match both forms
        # while skipping structural types: doc, parTrans, sibTrans, pres, asst.
        all_pts = diagram_data.findall(f".//{{{DGM_NS}}}pt")
        pt_nodes = [pt for pt in all_pts if pt.get("type") in (None, "node")]

        if len(pt_nodes) != len(text_items):
            msg = f"SmartArt has {len(pt_nodes)} nodes but {len(text_items)} text items provided"
            raise ValueError(msg)

        # Replace text in each node
        for i, pt_node in enumerate(pt_nodes):
            # Find the text element within this point node
            a_t = pt_node.find(f".//{{{A_NS}}}t")
            if a_t is not None:
                # Replace the text content
                a_t.text = text_items[i]
                logger.debug("Updated SmartArt node %d: '%s'", i, text_items[i])
            else:
                logger.warning("No text element found in SmartArt node %d", i)

        # Persist the modified XML back to the diagram data part. The base
        # Part class has no `blob` setter, so we write `_blob` directly.
        if diagram_part is not None:
            if not hasattr(diagram_part, "_blob"):
                msg = (
                    "diagram_part has no '_blob' attribute. "
                    "This may indicate an incompatible python-pptx version."
                )
                raise AttributeError(msg)
            diagram_part._blob = etree.tostring(  # type: ignore[attr-defined]
                diagram_data,
                xml_declaration=True,
                encoding="UTF-8",
                standalone=True,
            )
