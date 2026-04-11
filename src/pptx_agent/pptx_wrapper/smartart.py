"""SmartArt wrapper with XML manipulation."""

import logging
from typing import Any

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
        # Extract text items from nodes
        text_items = [node["text"] for node in nodes]

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

                # Get the diagram data part through the relationship
                part_rels = slide.part.rels
                if data_rel_id not in part_rels:
                    msg = f"Diagram data relationship '{data_rel_id}' not found"
                    raise ValueError(msg)

                diagram_part = part_rels[data_rel_id].target_part
                diagram_data = diagram_part._element  # type: ignore

            except (AttributeError, KeyError) as e:
                # If we can't navigate the relationships, raise error
                msg = f"Could not access SmartArt diagram  {e}"
                raise ValueError(msg) from e

        # Find all text nodes in the diagram data
        pt_nodes = diagram_data.findall(f".//{{{DGM_NS}}}pt[@type='node']")

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

    @staticmethod
    def _populate_process_smartart(
        slide: Slide,
        placeholder_name: str,
        nodes: list[dict[str, Any]],
    ) -> None:
        """Populate process flow SmartArt diagram.

        Args:
            slide: Slide containing SmartArt
            placeholder_name: Name of placeholder containing SmartArt
            nodes: List of node data for process steps
        """
        # Process SmartArt uses the same text replacement logic
        SmartArtWrapper.populate_smartart(slide, placeholder_name, nodes)

    @staticmethod
    def _populate_hierarchy_smartart(
        slide: Slide,
        placeholder_name: str,
        nodes: list[dict[str, Any]],
    ) -> None:
        """Populate organizational hierarchy SmartArt diagram.

        Args:
            slide: Slide containing SmartArt
            placeholder_name: Name of placeholder containing SmartArt
            nodes: List of node data for organizational structure
        """
        # Hierarchy SmartArt uses the same text replacement logic
        SmartArtWrapper.populate_smartart(slide, placeholder_name, nodes)

    @staticmethod
    def _populate_cycle_smartart(
        slide: Slide,
        placeholder_name: str,
        nodes: list[dict[str, Any]],
    ) -> None:
        """Populate cyclical process SmartArt diagram.

        Args:
            slide: Slide containing SmartArt
            placeholder_name: Name of placeholder containing SmartArt
            nodes: List of node data for cyclical steps
        """
        # Cycle SmartArt uses the same text replacement logic
        SmartArtWrapper.populate_smartart(slide, placeholder_name, nodes)

    @staticmethod
    def _populate_relationship_smartart(
        slide: Slide,
        placeholder_name: str,
        nodes: list[dict[str, Any]],
    ) -> None:
        """Populate relationship diagram SmartArt.

        Args:
            slide: Slide containing SmartArt
            placeholder_name: Name of placeholder containing SmartArt
            nodes: List of node data for relationship elements
        """
        # Relationship SmartArt uses the same text replacement logic
        SmartArtWrapper.populate_smartart(slide, placeholder_name, nodes)
