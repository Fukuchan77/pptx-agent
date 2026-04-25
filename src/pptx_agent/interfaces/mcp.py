"""MCP (Model Context Protocol) server interface for pptx-agent.

This module provides an MCP server that exposes pptx-agent functionality
as tools that can be used by AI assistants and other MCP clients.

Note: This is a basic implementation. Full MCP integration would require
the mcp package and proper server setup.
"""

import json
import logging
from pathlib import Path
from typing import Any, Literal

from pptx_agent.cache.manager import CacheManager
from pptx_agent.pipeline import generate_presentation
from pptx_agent.pptx_wrapper.presentation import PresentationWrapper
from pptx_agent.qa.engine import QAEngine
from pptx_agent.template_parser.manifest_builder import ManifestBuilder
from pptx_agent.template_parser.parser import TemplateParser

logger = logging.getLogger(__name__)


# MCP Tool Definitions
MCP_TOOLS = [
    {
        "name": "analyze_template",
        "description": (
            "Analyze a PowerPoint template and generate a manifest with layout information"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "template_path": {
                    "type": "string",
                    "description": "Path to the PowerPoint template file (.pptx)",
                },
                "language": {
                    "type": "string",
                    "enum": ["en", "ja"],
                    "description": "Default language for the template (en or ja)",
                    "default": "en",
                },
                "use_cache": {
                    "type": "boolean",
                    "description": "Whether to use cached manifest if available",
                    "default": True,
                },
            },
            "required": ["template_path"],
        },
    },
    {
        "name": "generate_presentation",
        "description": "Generate a PowerPoint presentation from text input using AI",
        "input_schema": {
            "type": "object",
            "properties": {
                "input_text": {
                    "type": "string",
                    "description": "Input text or markdown content to convert into presentation",
                },
                "template_path": {
                    "type": "string",
                    "description": "Path to the PowerPoint template file (.pptx)",
                },
                "output_path": {
                    "type": "string",
                    "description": "Path where the generated presentation should be saved",
                },
                "language": {
                    "type": "string",
                    "enum": ["en", "ja"],
                    "description": "Output language (auto-detected if not specified)",
                },
                "qa_enabled": {
                    "type": "boolean",
                    "description": "Enable quality assurance checks after generation",
                    "default": True,
                },
                "autofix_enabled": {
                    "type": "boolean",
                    "description": "Enable automatic issue fixing (experimental)",
                    "default": False,
                },
            },
            "required": ["input_text", "template_path", "output_path"],
        },
    },
    {
        "name": "validate_presentation",
        "description": "Run quality assurance checks on a PowerPoint presentation",
        "input_schema": {
            "type": "object",
            "properties": {
                "presentation_path": {
                    "type": "string",
                    "description": "Path to the PowerPoint presentation file to validate",
                },
                "language": {
                    "type": "string",
                    "enum": ["en", "ja"],
                    "description": (
                        "Language for capacity calculations (auto-detected if not specified)"
                    ),
                },
                "format": {
                    "type": "string",
                    "enum": ["json", "markdown"],
                    "description": "Report output format",
                    "default": "json",
                },
            },
            "required": ["presentation_path"],
        },
    },
]


# MCP Tool Handlers
async def handle_analyze_template(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle analyze_template tool call.

    Args:
        arguments: Tool arguments containing template_path, language, use_cache

    Returns:
        Dictionary with manifest data and metadata
    """
    template_path = Path(arguments["template_path"])
    language: Literal["en", "ja"] = arguments.get("language", "en")  # type: ignore[assignment]
    use_cache = arguments.get("use_cache", True)

    # Note: Using sync Path.exists() in async context is acceptable here because:
    # 1. File existence check is fast
    # 2. This is a validation step before main processing
    # 3. Keeps code simple without async file I/O dependencies
    if not template_path.exists():  # noqa: ASYNC240
        return {
            "success": False,
            "error": f"Template file not found: {template_path}",
        }

    try:
        # Initialize cache manager
        cache_manager = CacheManager()

        # Check cache first (unless disabled)
        manifest_dict = None
        cache_hit = False
        if use_cache:
            manifest_dict = cache_manager.get_manifest(template_path)
            if manifest_dict:
                cache_hit = True
                logger.info("Cache hit for template: %s", template_path)

        # Parse template if not cached
        if manifest_dict is None:
            logger.info("Analyzing template: %s", template_path)
            parser = TemplateParser()
            template_metadata = parser.parse_template(str(template_path))

            builder = ManifestBuilder()
            manifest = builder.build_manifest(
                template_metadata,
                template_name=template_path.stem,
                default_language=language,
            )

            manifest_dict = manifest.model_dump()

            # Cache manifest (unless disabled)
            if use_cache:
                cache_manager.set_manifest(template_path, manifest_dict)
                logger.info("Cached manifest for: %s", template_path)

        return {
            "success": True,
            "manifest": manifest_dict,
            "cache_hit": cache_hit,
        }

    except Exception as e:
        logger.exception("Template analysis failed")
        return {
            "success": False,
            "error": str(e),
        }


async def handle_generate_presentation(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle generate_presentation tool call.

    Args:
        arguments: Tool arguments containing input_text, template_path, output_path, etc.

    Returns:
        Dictionary with generation results and QA report
    """
    input_text = arguments["input_text"]
    template_path = arguments["template_path"]
    output_path = arguments["output_path"]
    language: Literal["en", "ja"] | None = arguments.get("language")  # type: ignore[assignment]
    qa_enabled = arguments.get("qa_enabled", True)
    autofix_enabled = arguments.get("autofix_enabled", False)

    try:
        logger.info("Generating presentation: %s", output_path)

        # Generate presentation
        _, qa_report = await generate_presentation(
            input_text=input_text,
            template_path=template_path,
            output_path=output_path,
            template_manifest=None,
            output_language=language,
            qa_enabled=qa_enabled,
            autofix_enabled=autofix_enabled,
        )

        # Convert QA report to dict if available
        qa_report_dict = None
        if qa_report is not None:
            qa_report_dict = json.loads(qa_report.to_json())

        return {
            "success": True,
            "output_path": output_path,
            "qa_report": qa_report_dict,
        }

    except Exception as e:
        logger.exception("Presentation generation failed")
        return {
            "success": False,
            "error": str(e),
        }


async def handle_validate_presentation(arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle validate_presentation tool call.

    Args:
        arguments: Tool arguments containing presentation_path, language, format

    Returns:
        Dictionary with QA report and validation results
    """
    presentation_path = Path(arguments["presentation_path"])
    language: Literal["en", "ja"] | None = arguments.get("language")  # type: ignore[assignment]
    report_format = arguments.get("format", "json")

    # Note: Using sync Path.exists() in async context is acceptable here because:
    # 1. File existence check is fast
    # 2. This is a validation step before main processing
    # 3. Keeps code simple without async file I/O dependencies
    if not presentation_path.exists():  # noqa: ASYNC240
        return {
            "success": False,
            "error": f"Presentation file not found: {presentation_path}",
        }

    try:
        logger.info("Running QA on: %s", presentation_path)

        # Load presentation
        wrapper = PresentationWrapper()
        wrapper.load_template(str(presentation_path))

        # Run QA validation
        engine = QAEngine(language=language)
        qa_report = engine.validate(wrapper)

        # Format report based on requested format
        if report_format == "markdown":
            report_language: Literal["en", "ja"] = language if language else "en"
            report_content: dict[str, Any] | str = qa_report.to_markdown(language=report_language)
        else:
            report_content = json.loads(qa_report.to_json())

        return {
            "success": True,
            "report": report_content,
            "passed": qa_report.passed,
        }

    except Exception as e:
        logger.exception("QA validation failed")
        return {
            "success": False,
            "error": str(e),
        }


# MCP Tool Router
async def handle_tool_call(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Route MCP tool calls to appropriate handlers.

    Args:
        tool_name: Name of the tool to execute
        arguments: Tool-specific arguments

    Returns:
        Tool execution result

    Raises:
        ValueError: If tool name is not recognized
    """
    handlers = {
        "analyze_template": handle_analyze_template,
        "generate_presentation": handle_generate_presentation,
        "validate_presentation": handle_validate_presentation,
    }

    if tool_name not in handlers:
        msg = f"Unknown tool: {tool_name}"
        raise ValueError(msg)

    return await handlers[tool_name](arguments)


def get_tool_definitions() -> list[dict[str, Any]]:
    """Get list of available MCP tool definitions.

    Returns:
        List of tool definition dictionaries
    """
    return MCP_TOOLS


# Note: Full MCP server implementation would require:
# 1. Installing the mcp package
# 2. Creating an MCP server instance
# 3. Registering tools with the server
# 4. Handling server lifecycle and communication
#
# Example pseudocode for MCP server setup:
#   - Import: from mcp import Server
#   - Create: server = Server("pptx-agent")
#   - Register: @server.tool() decorator on async functions
#   - Run: server.run() in main block


# Made with Bob
