"""Tests for ImageBlock handling in slide_builder module.

Following TDD methodology: These tests are written BEFORE implementation.
RED PHASE: All tests should FAIL initially because ImageBlock handling is not implemented.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from pptx_agent.pptx_wrapper.slide_builder import build_presentation, rebuild_slide_with_layout
from pptx_agent.schemas import PresentationSchema, SlideSchema
from pptx_agent.schemas.visual_assets import ImageBlock


class TestImageBlockInBuildPresentation:
    """Test suite for ImageBlock handling in build_presentation().

    RED PHASE: These tests should FAIL because ImageBlock handling is not implemented yet.
    """

    def test_build_presentation_with_valid_png_image(self, tmp_path: Path) -> None:
        """Test building presentation with valid PNG ImageBlock.

        RED PHASE: This test should FAIL because ImageBlock is not handled in build_presentation().
        """
        # Arrange - create a test PNG image
        test_image = tmp_path / "test_image.png"
        test_image.write_bytes(b"fake png data")  # Create dummy file

        content = PresentationSchema(
            title="Test Presentation with Image",
            slides=[
                SlideSchema(
                    layout_name="Title and Content",
                    title="Image Slide",
                    content=[
                        ImageBlock(
                            placeholder_name="Content Placeholder 1",
                            image_path=str(test_image),
                            alt_text="Test image",
                        )
                    ],
                )
            ],
        )

        template_path = "templates/basic-template.pptx"
        output_path = str(tmp_path / "with_image.pptx")

        # Mock ImageWrapper.add_image to verify it's called
        with patch("pptx_agent.pptx_wrapper.slide_builder.ImageWrapper") as mock_wrapper:
            # Act
            result_path = build_presentation(content, template_path, output_path)

            # Assert
            assert result_path == output_path
            assert Path(output_path).exists()

            # Verify ImageWrapper.add_image was called with correct arguments
            mock_wrapper.add_image.assert_called_once()
            call_args = mock_wrapper.add_image.call_args
            # Check positional arguments: (slide, placeholder_name, image_path, alt_text)
            assert call_args[0][1] == "Content Placeholder 1"  # placeholder_name
            assert call_args[0][2] == str(test_image)  # image_path
            assert call_args[0][3] == "Test image"  # alt_text

    def test_build_presentation_with_valid_jpeg_image(self, tmp_path: Path) -> None:
        """Test building presentation with valid JPEG ImageBlock.

        RED PHASE: This test should FAIL because ImageBlock is not handled.
        """
        # Arrange
        test_image = tmp_path / "test_image.jpg"
        test_image.write_bytes(b"fake jpeg data")

        content = PresentationSchema(
            title="JPEG Test",
            slides=[
                SlideSchema(
                    layout_name="Title and Content",
                    title="JPEG Slide",
                    content=[
                        ImageBlock(
                            placeholder_name="Content Placeholder 1",
                            image_path=str(test_image),
                            alt_text="JPEG image",
                        )
                    ],
                )
            ],
        )

        template_path = "templates/basic-template.pptx"
        output_path = str(tmp_path / "with_jpeg.pptx")

        with patch("pptx_agent.pptx_wrapper.slide_builder.ImageWrapper") as mock_wrapper:
            # Act
            result_path = build_presentation(content, template_path, output_path)

            # Assert
            assert result_path == output_path
            mock_wrapper.add_image.assert_called_once()

    def test_build_presentation_with_nonexistent_image_raises_error(self, tmp_path: Path) -> None:
        """Test that FileNotFoundError is raised for non-existent image path.

        RED PHASE: This test should FAIL because ImageBlock handler is not implemented.
        """
        # Arrange
        nonexistent_path = str(tmp_path / "nonexistent.png")

        content = PresentationSchema(
            title="Missing Image Test",
            slides=[
                SlideSchema(
                    layout_name="Title and Content",
                    title="Missing Image",
                    content=[
                        ImageBlock(
                            placeholder_name="Content Placeholder 1",
                            image_path=nonexistent_path,
                            alt_text="Missing",
                        )
                    ],
                )
            ],
        )

        template_path = "templates/basic-template.pptx"
        output_path = str(tmp_path / "should_fail.pptx")

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            build_presentation(content, template_path, output_path)

    def test_build_presentation_with_unsupported_image_format_raises_error(
        self, tmp_path: Path
    ) -> None:
        """Test that ValueError is raised for unsupported image format.

        RED PHASE: This test should FAIL because format validation is not implemented.

        Supported formats: PNG, JPEG, GIF, BMP, TIFF
        Unsupported: TXT, PDF, SVG, etc.
        """
        # Arrange
        unsupported_file = tmp_path / "document.txt"
        unsupported_file.write_text("not an image")

        content = PresentationSchema(
            title="Unsupported Format Test",
            slides=[
                SlideSchema(
                    layout_name="Title and Content",
                    title="Bad Format",
                    content=[
                        ImageBlock(
                            placeholder_name="Content Placeholder 1",
                            image_path=str(unsupported_file),
                            alt_text="Unsupported",
                        )
                    ],
                )
            ],
        )

        template_path = "templates/basic-template.pptx"
        output_path = str(tmp_path / "bad_format.pptx")

        # Act & Assert
        with pytest.raises(ValueError, match="Unsupported image format"):
            build_presentation(content, template_path, output_path)

    def test_build_presentation_with_multiple_images(self, tmp_path: Path) -> None:
        """Test building presentation with multiple ImageBlocks in one slide.

        RED PHASE: This test should FAIL because ImageBlock handling is not implemented.
        """
        # Arrange
        image1 = tmp_path / "image1.png"
        image2 = tmp_path / "image2.jpg"
        image1.write_bytes(b"fake png")
        image2.write_bytes(b"fake jpg")

        content = PresentationSchema(
            title="Multiple Images",
            slides=[
                SlideSchema(
                    layout_name="Two Content",
                    title="Two Images",
                    content=[
                        ImageBlock(
                            placeholder_name="Content Placeholder 1",
                            image_path=str(image1),
                            alt_text="First image",
                        ),
                        ImageBlock(
                            placeholder_name="Content Placeholder 2",
                            image_path=str(image2),
                            alt_text="Second image",
                        ),
                    ],
                )
            ],
        )

        template_path = "templates/basic-template.pptx"
        output_path = str(tmp_path / "multiple_images.pptx")

        with patch("pptx_agent.pptx_wrapper.slide_builder.ImageWrapper") as mock_wrapper:
            # Act
            result_path = build_presentation(content, template_path, output_path)

            # Assert
            assert result_path == output_path
            # Should be called twice (once for each image)
            assert mock_wrapper.add_image.call_count == 2

    def test_build_presentation_supports_gif_format(self, tmp_path: Path) -> None:
        """Test that GIF format is supported.

        RED PHASE: This test should FAIL.
        """
        # Arrange
        gif_image = tmp_path / "animation.gif"
        gif_image.write_bytes(b"fake gif")

        content = PresentationSchema(
            title="GIF Test",
            slides=[
                SlideSchema(
                    layout_name="Title and Content",
                    title="GIF Slide",
                    content=[
                        ImageBlock(
                            placeholder_name="Content Placeholder 1",
                            image_path=str(gif_image),
                            alt_text="GIF",
                        )
                    ],
                )
            ],
        )

        template_path = "templates/basic-template.pptx"
        output_path = str(tmp_path / "with_gif.pptx")

        with patch("pptx_agent.pptx_wrapper.slide_builder.ImageWrapper"):
            # Act - should not raise ValueError
            result_path = build_presentation(content, template_path, output_path)

            # Assert
            assert result_path == output_path

    def test_build_presentation_supports_bmp_format(self, tmp_path: Path) -> None:
        """Test that BMP format is supported.

        RED PHASE: This test should FAIL.
        """
        # Arrange
        bmp_image = tmp_path / "bitmap.bmp"
        bmp_image.write_bytes(b"fake bmp")

        content = PresentationSchema(
            title="BMP Test",
            slides=[
                SlideSchema(
                    layout_name="Title and Content",
                    title="BMP Slide",
                    content=[
                        ImageBlock(
                            placeholder_name="Content Placeholder 1",
                            image_path=str(bmp_image),
                            alt_text="BMP",
                        )
                    ],
                )
            ],
        )

        template_path = "templates/basic-template.pptx"
        output_path = str(tmp_path / "with_bmp.pptx")

        with patch("pptx_agent.pptx_wrapper.slide_builder.ImageWrapper"):
            # Act
            result_path = build_presentation(content, template_path, output_path)

            # Assert
            assert result_path == output_path

    def test_build_presentation_supports_tiff_format(self, tmp_path: Path) -> None:
        """Test that TIFF format is supported.

        RED PHASE: This test should FAIL.
        """
        # Arrange
        tiff_image = tmp_path / "photo.tiff"
        tiff_image.write_bytes(b"fake tiff")

        content = PresentationSchema(
            title="TIFF Test",
            slides=[
                SlideSchema(
                    layout_name="Title and Content",
                    title="TIFF Slide",
                    content=[
                        ImageBlock(
                            placeholder_name="Content Placeholder 1",
                            image_path=str(tiff_image),
                            alt_text="TIFF",
                        )
                    ],
                )
            ],
        )

        template_path = "templates/basic-template.pptx"
        output_path = str(tmp_path / "with_tiff.pptx")

        with patch("pptx_agent.pptx_wrapper.slide_builder.ImageWrapper"):
            # Act
            result_path = build_presentation(content, template_path, output_path)

            # Assert
            assert result_path == output_path

    def test_build_presentation_with_url_in_image_path_not_supported(self, tmp_path: Path) -> None:
        """Test that URL paths in image_path are not supported.

        ImageBlock currently only supports local file paths via image_path field.
        Remote URLs (http://, https://) are not supported in the current version.
        This test documents this limitation.

        RED PHASE: This test should FAIL because URL handling is not implemented.
        """
        # Arrange - use a URL in image_path field
        content = PresentationSchema(
            title="URL Test",
            slides=[
                SlideSchema(
                    layout_name="Title and Content",
                    title="URL Image",
                    content=[
                        ImageBlock(
                            placeholder_name="Content Placeholder 1",
                            image_path="https://example.com/image.png",
                            alt_text="Remote image",
                        )
                    ],
                )
            ],
        )

        template_path = "templates/basic-template.pptx"
        output_path = str(tmp_path / "with_url.pptx")

        # Act & Assert - URL paths should not be supported
        # This could raise FileNotFoundError (file doesn't exist locally)
        # or ValueError (unsupported format if we add URL validation)
        with pytest.raises((FileNotFoundError, ValueError)):
            build_presentation(content, template_path, output_path)


class TestImageBlockInRebuildSlide:
    """Test suite for ImageBlock handling in rebuild_slide_with_layout().

    RED PHASE: These tests should FAIL because ImageBlock handling is not implemented yet.
    """

    def test_rebuild_slide_with_imageblock(self, tmp_path: Path) -> None:
        """Test rebuilding slide with ImageBlock content.

        RED PHASE: This test should FAIL because ImageBlock is not handled in rebuild_slide_with_layout().
        """
        # Arrange - create initial presentation
        test_image = tmp_path / "rebuild_test.png"
        test_image.write_bytes(b"fake png")

        pptx_path = str(tmp_path / "test.pptx")

        # Create initial presentation with one slide
        initial_content = PresentationSchema(
            title="Initial",
            slides=[
                SlideSchema(
                    layout_name="Title Slide",
                    title="Original",
                    content=[],
                )
            ],
        )
        build_presentation(initial_content, "templates/basic-template.pptx", pptx_path)

        # Prepare slide data with ImageBlock
        slide_data = SlideSchema(
            layout_name="Title and Content",
            title="Rebuilt with Image",
            content=[
                ImageBlock(
                    placeholder_name="Content Placeholder 1",
                    image_path=str(test_image),
                    alt_text="Rebuilt image",
                )
            ],
        )

        with patch("pptx_agent.pptx_wrapper.slide_builder.ImageWrapper") as mock_wrapper:
            # Act
            rebuild_slide_with_layout(pptx_path, 0, "Title and Content", slide_data)

            # Assert - ImageWrapper.add_image should be called
            mock_wrapper.add_image.assert_called_once()
            call_args = mock_wrapper.add_image.call_args
            # Check positional arguments: (slide, placeholder_name, image_path, alt_text)
            assert call_args[0][2] == str(test_image)  # image_path
            assert call_args[0][3] == "Rebuilt image"  # alt_text

    def test_rebuild_slide_with_imageblock_validates_format(self, tmp_path: Path) -> None:
        """Test that rebuild_slide_with_layout validates image format.

        RED PHASE: This test should FAIL because format validation is not implemented.
        """
        # Arrange
        invalid_file = tmp_path / "document.pdf"
        invalid_file.write_bytes(b"fake pdf")

        pptx_path = str(tmp_path / "test.pptx")

        # Create initial presentation
        initial_content = PresentationSchema(
            title="Initial",
            slides=[
                SlideSchema(
                    layout_name="Title Slide",
                    title="Original",
                    content=[],
                )
            ],
        )
        build_presentation(initial_content, "templates/basic-template.pptx", pptx_path)

        # Prepare slide data with invalid image format
        slide_data = SlideSchema(
            layout_name="Title and Content",
            title="Invalid Format",
            content=[
                ImageBlock(
                    placeholder_name="Content Placeholder 1",
                    image_path=str(invalid_file),
                    alt_text="Invalid",
                )
            ],
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Unsupported image format"):
            rebuild_slide_with_layout(pptx_path, 0, "Title and Content", slide_data)
