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


if __name__ == "__main__":
    sys.exit(main_analyze_template())


# Made with Bob
