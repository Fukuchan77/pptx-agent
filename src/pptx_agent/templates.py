"""Template generation and validation for PPTX files.

Provides functions to generate minimal PPTX template files and validate
that required templates exist at application startup.

Note on path resolution:
    The default ``templates_dir`` in :func:`validate_templates` is derived
    from ``__file__`` via ``Path(__file__).parent.parent / "templates"``.
    This assumes the package is run **from a source checkout** (editable
    install or direct invocation).  If the package is installed as a
    wheel into ``site-packages``, the resolved path will NOT point to a
    valid project root.  Callers in non-development environments should
    always pass an explicit ``templates_dir``.
"""

import logging
from pathlib import Path

from pptx import Presentation

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Template generation
# ---------------------------------------------------------------------------


def _generate_template(output_path: Path, *, name: str) -> None:
    """Generate a minimal PPTX template file.

    Creates a blank presentation with default layouts that can be used
    as a fallback when the template file is missing.

    Args:
        output_path: Path where the template should be saved.
        name: Human-readable template name used in log / error messages
              (e.g. ``"basic"`` or ``"japanese"``).

    Raises:
        OSError: If the template cannot be written to disk.
        RuntimeError: If template generation fails for any reason.
    """
    try:
        prs = Presentation()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        prs.save(str(output_path))
        logger.info("Generated %s template: %s", name, output_path)
    except Exception as e:
        msg = f"Failed to generate {name} template at {output_path}: {e}"
        logger.exception(msg)
        raise RuntimeError(msg) from e


def generate_basic_template(output_path: Path) -> None:
    """Generate a minimal basic (English) template file.

    Creates a simple presentation with default layouts that can be used
    as a fallback when the template file is missing.

    Args:
        output_path: Path where the template should be saved

    Raises:
        OSError: If the template cannot be written to disk
        RuntimeError: If template generation fails for any reason
    """
    _generate_template(output_path, name="basic")


def generate_japanese_template(output_path: Path) -> None:
    """Generate a minimal Japanese template file.

    Creates a simple presentation with default layouts that can be used
    as a fallback when the template file is missing.

    Args:
        output_path: Path where the template should be saved

    Raises:
        OSError: If the template cannot be written to disk
        RuntimeError: If template generation fails for any reason
    """
    _generate_template(output_path, name="japanese")


# ---------------------------------------------------------------------------
# Template validation
# ---------------------------------------------------------------------------


def validate_templates(templates_dir: Path | None = None, auto_generate: bool = False) -> None:
    """Validate that required template files exist.

    Checks for the existence of required template files in the templates directory.
    This should be called at application startup to ensure the application can
    function properly.

    .. warning::

        When *templates_dir* is ``None`` the default path is derived from
        ``__file__`` and assumes a **source-tree layout** (editable install).
        Pass an explicit path for production / site-packages installs.

    Args:
        templates_dir: Optional path to the templates directory. If not provided,
            defaults to the ``templates/`` directory at the project root
            (derived from ``__file__``; see module-level note).
        auto_generate: If True, automatically generate missing templates instead
            of raising an error. Default is False.

    Raises:
        FileNotFoundError: If any required template file is missing and auto_generate
            is False, with a detailed error message including the file path and
            resolution guidance.
        RuntimeError: If auto_generate is True but template generation fails.

    Required templates:
        - basic-template.pptx: English presentation template
        - japanese-template.pptx: Japanese presentation template
    """
    if templates_dir is None:
        # Derive project root from source layout: src/pptx_agent/templates.py → ../../..
        # WARNING: This only works for editable / source-tree installs.
        # For site-packages installs, callers must supply templates_dir explicitly.
        project_root = Path(__file__).parent.parent.parent
        templates_dir = project_root / "templates"

    # Ensure templates directory exists if auto_generate is enabled
    if auto_generate and not templates_dir.exists():
        templates_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Created templates directory: %s", templates_dir)

    required_templates = {
        "basic-template.pptx": generate_basic_template,
        "japanese-template.pptx": generate_japanese_template,
    }

    missing_templates = []
    for template_name in required_templates:
        template_path = templates_dir / template_name
        if not template_path.exists():
            missing_templates.append((template_name, template_path))

    if missing_templates:
        if auto_generate:
            # Try to generate missing templates
            logger.info("Auto-generating %d missing template(s)...", len(missing_templates))
            generation_errors = []

            for template_name, template_path in missing_templates:
                try:
                    generator_func = required_templates[template_name]
                    generator_func(template_path)
                except Exception as e:
                    generation_errors.append((template_name, str(e)))
                    logger.exception("Failed to generate %s", template_name)

            if generation_errors:
                # Build detailed error message
                error_details = "\n  - ".join(
                    f"{name}: {error}" for name, error in generation_errors
                )
                msg = (
                    f"Failed to generate {len(generation_errors)} template(s):\n"
                    f"  - {error_details}\n\n"
                    "Please check:\n"
                    "1. Disk space availability\n"
                    "2. Write permissions for the templates directory\n"
                    "3. That the templates directory path is correct"
                )
                raise RuntimeError(msg)

            # All templates generated successfully
            logger.info("Successfully generated all missing templates")
        else:
            # Build error message with file paths and resolution guidance
            missing_files_str = "\n  - ".join(str(path) for _, path in missing_templates)
            error_msg = (
                f"Required template file(s) not found:\n  - {missing_files_str}\n\n"
                "Please ensure the following:\n"
                "1. Template files are placed in the 'templates/' directory\n"
                "2. Files have the correct names (basic-template.pptx, japanese-template.pptx)\n"
                "3. Template directory is available at application startup\n\n"
                "Alternatively, use the --generate-templates option to auto-generate "
                "missing templates.\n\n"
                f"テンプレートファイルが見つかりません:\n  - {missing_files_str}\n\n"
                "以下を確認してください:\n"
                "1. テンプレートファイルが 'templates/' ディレクトリに配置されていること\n"
                "2. ファイル名が正しいこと (basic-template.pptx, japanese-template.pptx)\n"
                "3. アプリケーション起動時にテンプレートディレクトリが利用可能であること\n\n"
                "または、--generate-templates オプションを使用してテンプレートを自動生成できます。"
            )
            raise FileNotFoundError(error_msg)

    logger.info("Template validation successful: All required templates found")
