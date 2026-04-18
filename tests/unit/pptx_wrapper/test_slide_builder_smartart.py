"""Tests for SmartArt integration in slide builder.

RED PHASE: These tests should FAIL because SmartArt handling is not yet
integrated into slide_builder.py.

Following TDD methodology for T069: Integrate SmartArt builder into slide builder.
"""

from pathlib import Path
from unittest.mock import patch

from pptx_agent.pptx_wrapper.slide_builder import build_presentation, rebuild_slide_with_layout
from pptx_agent.schemas import PresentationSchema, SlideSchema
from pptx_agent.schemas.text import TextBlock
from pptx_agent.schemas.visual_assets import ChartBlock, SmartArtBlock


class TestSmartArtIntegration:
    """Test suite for SmartArt integration in build_presentation.

    RED PHASE: These tests verify that SmartArtBlock is properly handled
    when building presentations.
    """

    def test_build_presentation_with_smartart_block(
        self, tmp_path: Path, template_path: str
    ) -> None:
        """Test that build_presentation handles SmartArtBlock content.

        RED PHASE: This test should FAIL because SmartArtBlock is not yet
        handled in the content block loop.
        """
        # Arrange
        smartart_block = SmartArtBlock(
            placeholder_name="Content Placeholder",
            diagram_type="process",
            nodes=[
                {"text": "Step 1", "level": 0},
                {"text": "Step 2", "level": 0},
                {"text": "Step 3", "level": 0},
            ],
        )

        content = PresentationSchema(
            title="SmartArt Test",
            slides=[
                SlideSchema(
                    layout_name="Title and Content",
                    title="Process Flow",
                    content=[smartart_block],
                )
            ],
        )

        output_path = str(tmp_path / "smartart_test.pptx")

        # Mock the add_smartart_to_slide function to verify it's called
        with patch("pptx_agent.pptx_wrapper.slide_builder.add_smartart_to_slide") as mock_add:
            # Act
            result_path = build_presentation(content, template_path, output_path)

            # Assert
            assert result_path == output_path
            assert Path(result_path).exists()

            # Verify add_smartart_to_slide was called with correct arguments
            mock_add.assert_called_once()
            call_args = mock_add.call_args

            # First argument should be the slide wrapper
            assert call_args[0][0] is not None

            # Second argument should be the SmartArtBlock
            assert call_args[0][1] == smartart_block

    def test_build_presentation_with_mixed_content_including_smartart(
        self, tmp_path: Path, template_path: str
    ) -> None:
        """Test that SmartArt works alongside other content types.

        RED PHASE: This test should FAIL because SmartArtBlock is not handled.
        """
        # Arrange
        content = PresentationSchema(
            title="Mixed Content Test",
            slides=[
                SlideSchema(
                    layout_name="Title and Content",
                    title="Mixed Content Slide",
                    content=[
                        TextBlock(
                            placeholder_name="Title 1",
                            text="Introduction",
                            language="en",
                        ),
                        SmartArtBlock(
                            placeholder_name="SmartArt Placeholder",
                            diagram_type="hierarchy",
                            nodes=[{"text": "Node 1", "level": 0}],
                        ),
                        ChartBlock(
                            placeholder_name="Chart Placeholder",
                            chart_type="bar",
                            data={"categories": ["A"], "series": [{"name": "S1", "values": [10]}]},
                            title="Chart Title",
                        ),
                    ],
                )
            ],
        )

        output_path = str(tmp_path / "mixed_content.pptx")

        # Act
        with patch("pptx_agent.pptx_wrapper.slide_builder.add_smartart_to_slide"):
            result_path = build_presentation(content, template_path, output_path)

            # Assert
            assert Path(result_path).exists()

    def test_build_presentation_calls_add_smartart_correctly(
        self, tmp_path: Path, template_path: str
    ) -> None:
        """Test that add_smartart_to_slide is called with correct parameters.

        RED PHASE: This test should FAIL - SmartArt not integrated yet.
        """
        # Arrange
        smartart_block = SmartArtBlock(
            placeholder_name="SmartArt Placeholder",
            diagram_type="cycle",
            nodes=[
                {"text": "Phase 1", "level": 0},
                {"text": "Phase 2", "level": 0},
            ],
        )

        content = PresentationSchema(
            title="Test",
            slides=[
                SlideSchema(
                    layout_name="Title and Content",
                    title="Test Slide",
                    content=[smartart_block],
                )
            ],
        )

        output_path = str(tmp_path / "smartart_call_test.pptx")

        # Act
        with patch("pptx_agent.pptx_wrapper.slide_builder.add_smartart_to_slide") as mock_add:
            build_presentation(content, template_path, output_path)

            # Assert - verify function was called exactly once
            assert mock_add.call_count == 1

            # Verify the SmartArtBlock passed is the same object
            _, smartart_arg = mock_add.call_args[0]
            assert smartart_arg.diagram_type == "cycle"
            assert len(smartart_arg.nodes) == 2


class TestRebuildSlideWithSmartArt:
    """Test suite for SmartArt support in rebuild_slide_with_layout.

    RED PHASE: These tests verify that rebuild_slide_with_layout properly
    handles SmartArtBlock when rebuilding slides.
    """

    def test_rebuild_slide_preserves_smartart_content(
        self, tmp_path: Path, template_path: str
    ) -> None:
        """Test that rebuild_slide_with_layout handles SmartArtBlock.

        RED PHASE: This test should FAIL because rebuild function doesn't
        handle SmartArtBlock in the content restoration loop.
        """
        # Arrange - create initial presentation
        initial_content = PresentationSchema(
            title="Initial",
            slides=[
                SlideSchema(
                    layout_name="Title and Content",
                    title="Original",
                    content=[
                        TextBlock(
                            placeholder_name="Content Placeholder 1",
                            text="Original text",
                            language="en",
                        )
                    ],
                )
            ],
        )

        pptx_path = str(tmp_path / "rebuild_test.pptx")

        # Create initial presentation
        build_presentation(initial_content, template_path, pptx_path)

        # Prepare slide data with SmartArt for rebuild
        slide_data = SlideSchema(
            layout_name="Two Content",
            title="Rebuilt Slide",
            content=[
                SmartArtBlock(
                    placeholder_name="Content Placeholder",
                    diagram_type="process",
                    nodes=[
                        {"text": "Step A", "level": 0},
                        {"text": "Step B", "level": 0},
                    ],
                )
            ],
        )

        # Act
        with patch("pptx_agent.pptx_wrapper.slide_builder.add_smartart_to_slide") as mock_add:
            rebuild_slide_with_layout(
                pptx_path=pptx_path,
                slide_index=0,
                new_layout="Two Content",
                slide_data=slide_data,
            )

            # Assert - verify add_smartart_to_slide was called
            mock_add.assert_called_once()

            # Verify SmartArtBlock was passed correctly
            _, smartart_arg = mock_add.call_args[0]
            assert smartart_arg.diagram_type == "process"
            assert len(smartart_arg.nodes) == 2

    def test_rebuild_slide_with_mixed_content_including_smartart(
        self, tmp_path: Path, template_path: str
    ) -> None:
        """Test rebuild with multiple block types including SmartArt.

        RED PHASE: This test should FAIL - SmartArt not handled in rebuild.
        """
        # Arrange
        initial_content = PresentationSchema(
            title="Initial",
            slides=[
                SlideSchema(
                    layout_name="Title and Content",
                    title="Initial",
                    content=[],
                )
            ],
        )

        pptx_path = str(tmp_path / "rebuild_mixed.pptx")
        build_presentation(initial_content, template_path, pptx_path)

        # Slide data with mixed content
        slide_data = SlideSchema(
            layout_name="Two Content",
            title="Mixed Content",
            content=[
                TextBlock(
                    placeholder_name="Left Placeholder",
                    text="Text content",
                    language="en",
                ),
                SmartArtBlock(
                    placeholder_name="Right Placeholder",
                    diagram_type="hierarchy",
                    nodes=[{"text": "Root", "level": 0}],
                ),
            ],
        )

        # Act
        with patch("pptx_agent.pptx_wrapper.slide_builder.add_smartart_to_slide"):
            rebuild_slide_with_layout(
                pptx_path=pptx_path,
                slide_index=0,
                new_layout="Two Content",
                slide_data=slide_data,
            )

            # Assert - file should still exist and be valid
            assert Path(pptx_path).exists()


class TestSmartArtImportPresence:
    """Test that necessary imports are present for SmartArt integration.

    RED PHASE: This test verifies that SmartArtBlock and add_smartart_to_slide
    are imported at the module level.
    """

    def test_smartart_block_imported_in_slide_builder(self) -> None:
        """Test that SmartArtBlock is imported in slide_builder module.

        RED PHASE: This test should FAIL because SmartArtBlock is not yet
        imported in slide_builder.py.
        """
        # Import the module
        import pptx_agent.pptx_wrapper.slide_builder as slide_builder_module

        # Check if SmartArtBlock is available in module namespace
        assert hasattr(slide_builder_module, "SmartArtBlock"), (
            "SmartArtBlock should be imported in slide_builder.py"
        )

    def test_add_smartart_to_slide_imported_in_slide_builder(self) -> None:
        """Test that add_smartart_to_slide is imported in slide_builder module.

        RED PHASE: This test should FAIL because add_smartart_to_slide is not
        yet imported in slide_builder.py.
        """
        # Import the module
        import pptx_agent.pptx_wrapper.slide_builder as slide_builder_module

        # Check if function is available
        assert hasattr(slide_builder_module, "add_smartart_to_slide"), (
            "add_smartart_to_slide should be imported in slide_builder.py"
        )
