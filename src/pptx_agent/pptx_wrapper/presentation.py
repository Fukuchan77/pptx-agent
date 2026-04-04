"""Presentation-level wrapper for python-pptx."""

from typing import TYPE_CHECKING

from pptx import Presentation as PresentationFactory

if TYPE_CHECKING:
    from pptx.presentation import Presentation

from pptx_agent.validators.file_validator import validate_output_path, validate_template_path

from .slide import SlideWrapper


class PresentationWrapper:
    """Wrapper for python-pptx Presentation with type hints."""

    def __init__(self) -> None:
        """Initialize empty presentation wrapper."""
        self._prs: Presentation | None = None
        self._template_path: str | None = None

    def load_template(self, path: str) -> None:
        """Load PPTX template file.

        Args:
            path: Path to PPTX template file

        Raises:
            InvalidFileError: If file doesn't exist, has wrong extension, or is not valid PPTX
            SecurityValidationError: If path contains symlinks
            FileSizeLimitError: If file size exceeds limits
            CompressionRatioError: If compression ratio is suspicious
        """
        # Validate template path (includes existence, extension, symlinks, ZIP structure)
        validated_path = validate_template_path(path)

        self._prs = PresentationFactory(str(validated_path))
        self._template_path = str(validated_path)

    def add_slide(self, layout_name: str) -> SlideWrapper:
        """Add slide with specified layout.

        Args:
            layout_name: Name of the slide layout to use

        Returns:
            SlideWrapper instance for the new slide

        Raises:
            ValueError: If template not loaded or layout not found
        """
        if self._prs is None:
            msg = "Template must be loaded before adding slides"
            raise ValueError(msg)

        # Find layout by name
        layout = None
        for slide_layout in self._prs.slide_layouts:
            if slide_layout.name == layout_name:
                layout = slide_layout
                break

        if layout is None:
            msg = f"Layout '{layout_name}' not found in template"
            raise ValueError(msg)

        # Add slide with layout
        slide = self._prs.slides.add_slide(layout)
        return SlideWrapper(slide)

    def get_layouts(self) -> list[str]:
        """Return list of available layout names.

        Returns:
            List of layout names from the template

        Raises:
            ValueError: If template not loaded
        """
        if self._prs is None:
            msg = "Template must be loaded before getting layouts"
            raise ValueError(msg)

        return [layout.name for layout in self._prs.slide_layouts]

    def save(self, output_path: str, base_dir: str | None = None) -> None:
        """Save presentation to file with path validation.

        Args:
            output_path: Path where presentation should be saved
            base_dir: Base directory for output files (optional, defaults to ./output)

        Raises:
            ValueError: If template not loaded
            PathTraversalError: If path is outside allowed directory
        """
        if self._prs is None:
            msg = "Template must be loaded before saving"
            raise ValueError(msg)

        # Validate and resolve output path
        output = validate_output_path(output_path, base_dir)

        # Create parent directory if needed
        output.parent.mkdir(parents=True, exist_ok=True)

        # Save presentation
        self._prs.save(str(output))
