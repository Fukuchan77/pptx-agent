"""Enhanced CLI interface for pptx-agent with template analysis commands.

This module provides command-line interface extensions for template analysis,
cache management, and QA operations.
"""

import argparse
import json
import sys
import traceback
from pathlib import Path

from pptx_agent.cache.manager import CacheManager
from pptx_agent.pptx_wrapper.presentation import PresentationWrapper
from pptx_agent.qa.engine import QAEngine
from pptx_agent.template_parser.manifest_builder import ManifestBuilder
from pptx_agent.template_parser.parser import TemplateParser


def create_analyze_template_parser() -> argparse.ArgumentParser:
    """Create argument parser for analyze-template command.

    Returns:
        Configured ArgumentParser for template analysis
    """
    parser = argparse.ArgumentParser(
        prog="pptx-agent analyze-template",
        description="Analyze PowerPoint template and generate manifest",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -t template.pptx -o manifest.json
  %(prog)s --template corporate.pptx --output manifest.json --language ja
  %(prog)s -t template.pptx --cache-stats
        """,
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
        metavar="FILE",
        help="Output manifest JSON file path (optional, prints to stdout if not specified)",
    )

    parser.add_argument(
        "-l",
        "--language",
        type=str,
        choices=["en", "ja"],
        default="en",
        metavar="LANG",
        help="Default language for template: 'en' for English, 'ja' for Japanese (default: en)",
    )

    parser.add_argument(
        "--cache-stats",
        action="store_true",
        help="Display cache statistics after analysis",
    )

    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Skip caching the manifest (analysis only)",
    )

    parser.add_argument(
        "--invalidate-cache",
        action="store_true",
        help="Invalidate cached manifest for this template before analysis",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    return parser


def analyze_template_command(args: argparse.Namespace) -> int:
    """Execute template analysis command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code: 0 for success, non-zero for errors
    """
    try:
        template_path = Path(args.template)
        if not template_path.exists():
            print(f"Error: Template file not found: {args.template}", file=sys.stderr)
            return 1

        # Initialize cache manager
        cache_manager = CacheManager()

        # Invalidate cache if requested
        if args.invalidate_cache:
            if cache_manager.invalidate(template_path):
                if args.verbose:
                    print(f"✓ Invalidated cache for: {args.template}")
            elif args.verbose:
                print(f"i No cache entry found for: {args.template}")

        # Check cache first (unless --no-cache)
        manifest_dict = None
        cache_hit = False
        if not args.no_cache:
            manifest_dict = cache_manager.get_manifest(template_path)
            if manifest_dict:
                cache_hit = True
                if args.verbose:
                    print(f"✓ Using cached manifest for: {args.template}")

        # Parse template if not cached
        if manifest_dict is None:
            if args.verbose:
                print(f"Analyzing template: {args.template}")

            parser = TemplateParser()
            template_metadata = parser.parse_template(str(template_path))

            builder = ManifestBuilder()
            manifest = builder.build_manifest(
                template_metadata,
                template_name=template_path.stem,
                default_language=args.language,  # type: ignore[arg-type]
            )

            manifest_dict = manifest.model_dump()

            # Cache manifest (unless --no-cache)
            if not args.no_cache:
                cache_manager.set_manifest(template_path, manifest_dict)
                if args.verbose:
                    print(f"✓ Cached manifest for: {args.template}")

        # Convert to JSON
        manifest_json = json.dumps(manifest_dict, indent=2)

        # Output manifest
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(manifest_json, encoding="utf-8")
            print(f"✓ Manifest saved: {args.output}")
        else:
            print(manifest_json)

        # Display cache statistics if requested
        if args.cache_stats:
            stats = cache_manager.get_statistics()
            print("\nCache Statistics:")
            print(f"  Entries: {stats['entry_count']}")
            print(f"  Total size: {stats['total_size_mb']:.2f} MB")
            if cache_hit:
                print("  Cache hit: Yes")
            else:
                print("  Cache hit: No (template analyzed)")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc(file=sys.stderr)
        return 1
    else:
        return 0


def main_analyze_template() -> int:
    """Main entry point for analyze-template command.

    Returns:
        Exit code: 0 for success, non-zero for errors
    """
    parser = create_analyze_template_parser()
    args = parser.parse_args()
    return analyze_template_command(args)


def create_qa_parser() -> argparse.ArgumentParser:
    """Create argument parser for qa command.

    Returns:
        Configured ArgumentParser for QA operations
    """
    parser = argparse.ArgumentParser(
        prog="pptx-agent qa",
        description="Run quality assurance checks on PowerPoint presentations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -i presentation.pptx
  %(prog)s --input existing.pptx --report qa-report.json
  %(prog)s -i presentation.pptx --template corporate.pptx
  %(prog)s -i presentation.pptx --autofix --output fixed.pptx
  %(prog)s -i presentation.pptx --format markdown --report report.md
        """,
    )

    parser.add_argument(
        "-i",
        "--input",
        type=str,
        required=True,
        metavar="FILE",
        help="Input .pptx file to validate (required)",
    )

    parser.add_argument(
        "-t",
        "--template",
        type=str,
        metavar="FILE",
        help="Template .pptx file for style conformance validation (optional)",
    )

    parser.add_argument(
        "-r",
        "--report",
        type=str,
        metavar="FILE",
        help="Output QA report file path (optional, prints to stdout if not specified)",
    )

    parser.add_argument(
        "-f",
        "--format",
        type=str,
        choices=["json", "markdown"],
        default="json",
        metavar="FORMAT",
        help="Report output format: 'json' or 'markdown' (default: json)",
    )

    parser.add_argument(
        "-l",
        "--language",
        type=str,
        choices=["en", "ja"],
        metavar="LANG",
        help=(
            "Language override for capacity calculations: 'en' for English, "
            "'ja' for Japanese (auto-detected if not specified)"
        ),
    )

    parser.add_argument(
        "--autofix",
        action="store_true",
        help="Enable automatic issue fixing (experimental)",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        metavar="FILE",
        help="Output .pptx file path when using --autofix (optional)",
    )

    parser.add_argument(
        "--max-fix-iterations",
        type=int,
        default=3,
        metavar="N",
        help="Maximum fix loop iterations (default: 3)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    return parser


def qa_command(args: argparse.Namespace) -> int:
    """Execute QA validation command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code: 0 if no errors found, 1 if errors detected
    """
    try:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: Input file not found: {args.input}", file=sys.stderr)
            return 1

        if args.verbose:
            print(f"Loading presentation: {args.input}")

        # Load presentation
        wrapper = PresentationWrapper()
        wrapper.load_template(str(input_path))

        if args.verbose:
            print("Running QA validation...")
            if args.language:
                print(f"Language override: {args.language}")

        # Run QA validation with optional language override
        engine = QAEngine(language=args.language)
        report = engine.validate(wrapper)

        if args.verbose:
            print(f"QA validation complete: {report.total_issues} issues found")
            print(f"  Errors: {report.error_count}")
            print(f"  Warnings: {report.warning_count}")
            print(f"  Info: {report.info_count}")

        # Handle auto-fix if requested
        if args.autofix and args.verbose:
            print("\nAuto-fix mode is not yet fully implemented")
            print("This feature will be available in a future release")
            # Note: Auto-fix integration will be implemented in Phase 3
            # when FixEngine is fully integrated with QA workflow

        # Generate report output
        if args.format == "markdown":
            # Pass language to markdown report for localized labels
            report_language = args.language if args.language else "en"
            report_content = report.to_markdown(language=report_language)
        else:
            report_content = report.to_json()

        # Output report
        if args.report:
            report_path = Path(args.report)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(report_content, encoding="utf-8")
            if args.verbose:
                print(f"\n✓ QA report saved: {args.report}")
        else:
            print(report_content)

        # Save fixed presentation if auto-fix was used and output specified
        if args.autofix and args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            wrapper.prs.save(str(output_path))
            if args.verbose:
                print(f"✓ Fixed presentation saved: {args.output}")

        # Return exit code based on error count (0 = passed, 1 = failed)
        exit_code = 0 if report.passed else 1

        if args.verbose:
            status = "PASSED" if report.passed else "FAILED"
            print(f"\nQA Status: {status}")
            print(f"Exit code: {exit_code}")
            return exit_code
        return exit_code  # noqa: TRY300
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc(file=sys.stderr)
        return 1


def main_qa() -> int:
    """Main entry point for qa command.

    Returns:
        Exit code: 0 if no errors, 1 if errors detected or execution failed
    """
    parser = create_qa_parser()
    args = parser.parse_args()
    return qa_command(args)


if __name__ == "__main__":
    sys.exit(main_analyze_template())


# Made with Bob
