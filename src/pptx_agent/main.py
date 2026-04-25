"""CLI entry point for PowerPoint presentation generator.

This module provides the command-line interface for generating presentations
from text input using the AI-powered pipeline.
"""

import argparse
import asyncio
import json
import logging
import sys
import traceback
from pathlib import Path

from pptx_agent.pipeline import generate_presentation
from pptx_agent.schemas.template_manifest import TemplateManifest
from pptx_agent.templates import validate_templates
from pptx_agent.validators.exceptions import InvalidFileError, SecurityValidationError
from pptx_agent.validators.input_validator import InputValidationError

# Setup logger
logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser.

    Returns:
        Configured ArgumentParser instance with all CLI arguments
    """
    parser = argparse.ArgumentParser(
        prog="pptx-agent",
        description="Generate PowerPoint presentations from text input using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -i story.txt -t template.pptx -o output.pptx
  %(prog)s --input story.txt --template template.pptx --output presentation.pptx \\
      --manifest manifest.json
        """,
    )

    parser.add_argument(
        "-i",
        "--input",
        type=str,
        required=True,
        metavar="FILE",
        help="Input text file path (required)",
    )

    parser.add_argument(
        "-t",
        "--template",
        type=str,
        required=True,
        metavar="FILE",
        help="Template .pptx file path (required)",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=True,
        metavar="FILE",
        help="Output .pptx file path (required)",
    )

    parser.add_argument(
        "-m",
        "--manifest",
        type=str,
        required=False,
        metavar="FILE",
        help="Template manifest JSON file (optional)",
    )

    parser.add_argument(
        "-l",
        "--language",
        type=str,
        required=False,
        choices=["en", "ja"],
        metavar="LANG",
        help=(
            "Output language: 'en' for English, 'ja' for Japanese "
            "(optional, auto-detected if not specified)"
        ),
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output including full tracebacks",
    )

    parser.add_argument(
        "--generate-templates",
        action="store_true",
        help="Automatically generate missing template files instead of raising an error",
    )

    parser.add_argument(
        "--qa",
        dest="qa_enabled",
        action="store_true",
        default=True,
        help="Enable QA validation pass (default: enabled)",
    )

    parser.add_argument(
        "--no-qa",
        dest="qa_enabled",
        action="store_false",
        help="Disable QA validation pass",
    )

    parser.add_argument(
        "--autofix",
        dest="autofix_enabled",
        action="store_true",
        default=False,
        help="Enable automatic issue fixing (default: disabled)",
    )

    parser.add_argument(
        "--max-fix-iterations",
        type=int,
        default=3,
        metavar="N",
        help="Maximum number of fix loop iterations (default: 3)",
    )

    parser.add_argument(
        "--qa-report",
        type=str,
        metavar="FILE",
        help="Output QA report to specified file (JSON format)",
    )

    return parser


def _validate_and_read_input(input_path: str) -> str:
    """Validate and read input text file.

    Args:
        input_path: Path to the input text file

    Returns:
        Contents of the input file

    Raises:
        FileNotFoundError: If file doesn't exist
        OSError, UnicodeDecodeError: If file cannot be read
    """
    path = Path(input_path)
    if not path.exists():
        msg = f"Input file not found: {input_path}"
        raise FileNotFoundError(msg)

    return path.read_text(encoding="utf-8")


def _validate_template(template_path: str) -> Path:
    """Validate template file exists.

    Args:
        template_path: Path to the template file

    Returns:
        Validated Path object

    Raises:
        FileNotFoundError: If template file doesn't exist
    """
    path = Path(template_path)
    if not path.exists():
        msg = f"Template file not found: {template_path}"
        raise FileNotFoundError(msg)
    return path


def _load_manifest(manifest_path: str | None) -> TemplateManifest | None:
    """Load and validate optional manifest file.

    Args:
        manifest_path: Path to the manifest file, or None

    Returns:
        Validated TemplateManifest or None if no manifest provided

    Raises:
        FileNotFoundError: If manifest file doesn't exist
        json.JSONDecodeError, ValueError: If manifest is invalid
    """
    if not manifest_path:
        return None

    path = Path(manifest_path)
    if not path.exists():
        msg = f"Manifest file not found: {manifest_path}"
        raise FileNotFoundError(msg)

    manifest_data = json.loads(path.read_text(encoding="utf-8"))
    return TemplateManifest.model_validate(manifest_data)


def validate_cli_inputs(args: argparse.Namespace) -> tuple[str, Path, TemplateManifest | None]:
    """Validate all CLI inputs, return validated objects or raise."""
    validate_templates(auto_generate=args.generate_templates)
    input_text = _validate_and_read_input(args.input)
    template_path = _validate_template(args.template)
    template_manifest = _load_manifest(args.manifest)
    return input_text, template_path, template_manifest


def main() -> int:
    """Main CLI entry point.

    Parses command-line arguments, validates inputs, and generates presentation.

    Returns:
        Exit code: 0 for success, non-zero for errors

    """
    parser = create_parser()
    args = parser.parse_args()

    try:
        # Validate all CLI inputs
        input_text, template_path, template_manifest = validate_cli_inputs(args)

        # Resolve output path to absolute
        # Note: Path traversal validation is intentionally not performed here for CLI flexibility
        # CLI users are trusted to specify output paths (validated in tests)
        output_path = Path(args.output).resolve()
        # Ensure output directory exists (after path resolution, not before)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate presentation (async)
        result_path, qa_report = asyncio.run(
            generate_presentation(
                input_text=input_text,
                template_path=str(template_path),
                output_path=str(output_path),
                template_manifest=template_manifest,
                output_language=args.language,  # Pass language parameter (can be None)
                qa_enabled=args.qa_enabled,
                autofix_enabled=args.autofix_enabled,
                max_fix_iterations=args.max_fix_iterations,
            )
        )

        # Save QA report if requested
        if qa_report and args.qa_report:
            qa_report_path = Path(args.qa_report)
            qa_report_path.parent.mkdir(parents=True, exist_ok=True)
            qa_report_path.write_text(qa_report.to_json(), encoding="utf-8")
            print(f"✓ QA report saved: {args.qa_report}")

        # Success message
        print(f"✓ Presentation generated successfully: {result_path}")

        # Print QA summary if enabled
        if qa_report:
            if qa_report.passed:
                print(f"✓ QA passed: {qa_report.total_issues} issues found (0 errors)")
            else:
                print(
                    f"⚠ QA failed: {qa_report.error_count} errors, "
                    f"{qa_report.warning_count} warnings, {qa_report.info_count} info"
                )
                if args.autofix_enabled:
                    print(f"  Fix iterations: {qa_report.fix_iterations}")
    except InputValidationError as e:
        print(f"Error: Input validation failed: {e}", file=sys.stderr)
        return 1
    except (InvalidFileError, SecurityValidationError) as e:
        print(f"Error: File validation failed: {e}", file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except (OSError, UnicodeDecodeError) as e:
        print(f"Error: Cannot read input file: {e}", file=sys.stderr)
        return 1
    except RuntimeError as e:
        logger.exception("Unexpected error")
        if args.verbose:
            # Show full traceback in verbose mode
            traceback.print_exc(file=sys.stderr)
        else:
            print(f"Error: {e}", file=sys.stderr)
        return 1
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error: Invalid manifest file or input: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        logger.exception("Unexpected error")
        if args.verbose:
            # Show full traceback in verbose mode
            traceback.print_exc(file=sys.stderr)
        else:
            print(f"Error: Unexpected error occurred: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
