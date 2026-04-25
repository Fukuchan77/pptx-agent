"""FastAPI REST interface for pptx-agent.

This module provides a REST API for presentation generation, template analysis,
and QA operations. It supports file uploads, async processing, and result downloads.
"""

import json
import logging
import tempfile
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from pptx_agent.cache.manager import CacheManager
from pptx_agent.pipeline import generate_presentation
from pptx_agent.pptx_wrapper.presentation import PresentationWrapper
from pptx_agent.qa.engine import QAEngine
from pptx_agent.template_parser.manifest_builder import ManifestBuilder
from pptx_agent.template_parser.parser import TemplateParser

# Setup logger
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan events.

    Args:
        _app: FastAPI application instance (unused, required by FastAPI signature)
    """
    # Startup
    logger.info("PPTX Agent API starting up")
    yield
    # Shutdown
    logger.info("PPTX Agent API shutting down")
    # Clean up temporary files
    for file_path in _file_storage.values():
        file_path.unlink(missing_ok=True)
    _file_storage.clear()


# Create FastAPI app
app = FastAPI(
    title="PPTX Agent API",
    description="AI-powered PowerPoint presentation generation and quality assurance",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# In-memory storage for generated files (in production, use proper storage)
_file_storage: dict[str, Path] = {}


# Request/Response Models
class AnalyzeTemplateRequest(BaseModel):
    """Request model for template analysis."""

    language: str = Field(
        default="en",
        description="Default language for template: 'en' or 'ja'",
        pattern="^(en|ja)$",
    )
    use_cache: bool = Field(
        default=True,
        description="Whether to use cached manifest if available",
    )


class AnalyzeTemplateResponse(BaseModel):
    """Response model for template analysis."""

    manifest: dict[str, Any] = Field(description="Template manifest data")
    cache_hit: bool = Field(description="Whether manifest was loaded from cache")
    file_id: str = Field(description="Unique identifier for the analyzed template")


class GenerateRequest(BaseModel):
    """Request model for presentation generation."""

    language: Literal["en", "ja"] | None = Field(
        default=None,
        description="Output language: 'en' or 'ja' (auto-detected if not specified)",
    )
    qa_enabled: bool = Field(
        default=True,
        description="Enable quality assurance checks after generation",
    )
    autofix_enabled: bool = Field(
        default=False,
        description="Enable automatic issue fixing (experimental)",
    )


class GenerateResponse(BaseModel):
    """Response model for presentation generation."""

    file_id: str = Field(description="Unique identifier for the generated presentation")
    output_path: str = Field(description="Path to the generated presentation file")
    qa_report: dict[str, Any] | None = Field(
        default=None,
        description="QA report if qa_enabled was true",
    )


class QARequest(BaseModel):
    """Request model for QA validation."""

    language: Literal["en", "ja"] | None = Field(
        default=None,
        description="Language override: 'en' or 'ja' (auto-detected if not specified)",
    )
    format: str = Field(
        default="json",
        description="Report format: 'json' or 'markdown'",
        pattern="^(json|markdown)$",
    )
    autofix: bool = Field(
        default=False,
        description="Enable automatic issue fixing (experimental)",
    )
    max_fix_iterations: int = Field(
        default=3,
        description="Maximum fix loop iterations",
        ge=1,
        le=10,
    )


class QAResponse(BaseModel):
    """Response model for QA validation."""

    report: dict[str, Any] | str = Field(description="QA report (JSON or Markdown)")
    passed: bool = Field(description="Whether QA validation passed")
    file_id: str | None = Field(
        default=None,
        description="File ID for fixed presentation if autofix was enabled",
    )


# API Endpoints
@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "name": "PPTX Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/analyze-template", response_model=AnalyzeTemplateResponse)
async def analyze_template(
    template: Annotated[UploadFile, File(description="Template .pptx file")],
    request: Annotated[str, Form(description="JSON-encoded AnalyzeTemplateRequest")] = "{}",
) -> AnalyzeTemplateResponse:
    """Analyze PowerPoint template and generate manifest.

    Args:
        template: Template .pptx file upload
        request: JSON-encoded request parameters

    Returns:
        Template manifest and metadata

    Raises:
        HTTPException: If template analysis fails
    """
    try:
        # Parse request parameters
        req_data = json.loads(request)
        req_model = AnalyzeTemplateRequest(**req_data)

        # Save uploaded template to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as tmp_file:
            content = await template.read()
            tmp_file.write(content)
            tmp_path = Path(tmp_file.name)

        try:
            # Initialize cache manager
            cache_manager = CacheManager()

            # Check cache first (unless disabled)
            manifest_dict = None
            cache_hit = False
            if req_model.use_cache:
                manifest_dict = cache_manager.get_manifest(tmp_path)
                if manifest_dict:
                    cache_hit = True
                    logger.info("Cache hit for template: %s", template.filename)

            # Parse template if not cached
            if manifest_dict is None:
                logger.info("Analyzing template: %s", template.filename)
                parser = TemplateParser()
                template_metadata = parser.parse_template(str(tmp_path))

                builder = ManifestBuilder()
                manifest = builder.build_manifest(
                    template_metadata,
                    template_name=template.filename or "template",
                    default_language=req_model.language,  # type: ignore[arg-type]
                )

                manifest_dict = manifest.model_dump()

                # Cache manifest (unless disabled)
                if req_model.use_cache:
                    cache_manager.set_manifest(tmp_path, manifest_dict)
                    logger.info("Cached manifest for: %s", template.filename)

            # Generate file ID and store template path
            file_id = str(uuid.uuid4())
            _file_storage[file_id] = tmp_path

            return AnalyzeTemplateResponse(
                manifest=manifest_dict,
                cache_hit=cache_hit,
                file_id=file_id,
            )

        except Exception:
            # Clean up temporary file on error
            # Note: Using sync unlink() in async context is acceptable here because:
            # 1. File operations are fast for small temp files
            # 2. This is an error path, not performance-critical
            # 3. Keeps code simple without async file I/O dependencies
            tmp_path.unlink(missing_ok=True)  # noqa: ASYNC240
            raise

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid request JSON: {e}") from e
    except Exception as e:
        logger.exception("Template analysis failed")
        raise HTTPException(status_code=500, detail=f"Template analysis failed: {e}") from e


@app.post("/api/generate", response_model=GenerateResponse)
async def generate(
    input_file: Annotated[UploadFile, File(description="Input text or Markdown file")],
    template: Annotated[UploadFile, File(description="Template .pptx file")],
    request: Annotated[str, Form(description="JSON-encoded GenerateRequest")] = "{}",
) -> GenerateResponse:
    """Generate PowerPoint presentation from text input.

    Args:
        input_file: Input text or Markdown file
        template: Template .pptx file
        request: JSON-encoded request parameters

    Returns:
        Generated presentation file ID and metadata

    Raises:
        HTTPException: If generation fails
    """
    try:
        # Parse request parameters
        req_data = json.loads(request)
        req_model = GenerateRequest(**req_data)

        # Save uploaded files to temporary files
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as input_tmp:
            input_content = await input_file.read()
            input_tmp.write(input_content)
            input_path = Path(input_tmp.name)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as template_tmp:
            template_content = await template.read()
            template_tmp.write(template_content)
            template_path = Path(template_tmp.name)

        # Create output file path
        # Use NamedTemporaryFile with delete=False instead of deprecated mktemp
        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as output_tmp:
            output_path = Path(output_tmp.name)

        try:
            # Read input text
            # Note: Using sync read_text() in async context is acceptable here because:
            # 1. Input files are typically small (text/markdown)
            # 2. Reading happens once before main processing
            # 3. Keeps code simple without async file I/O dependencies
            input_text = input_path.read_text(encoding="utf-8")  # noqa: ASYNC240

            # Generate presentation (note: generate_presentation is async, so we await it directly)
            logger.info("Generating presentation from: %s", input_file.filename)
            _, qa_report = await generate_presentation(
                input_text=input_text,
                template_path=str(template_path),
                output_path=str(output_path),
                template_manifest=None,
                output_language=req_model.language,
                qa_enabled=req_model.qa_enabled,
                autofix_enabled=req_model.autofix_enabled,
            )

            # Generate file ID and store output path
            file_id = str(uuid.uuid4())
            _file_storage[file_id] = output_path

            # Convert QA report to dict if available
            qa_report_dict = None
            if qa_report is not None:
                qa_report_dict = json.loads(qa_report.to_json())

            return GenerateResponse(
                file_id=file_id,
                output_path=str(output_path),
                qa_report=qa_report_dict,
            )

        finally:
            # Clean up input files
            # Note: Using sync unlink() in async context is acceptable here because:
            # 1. File operations are fast for small temp files
            # 2. This is cleanup code, not performance-critical
            # 3. Keeps code simple without async file I/O dependencies
            input_path.unlink(missing_ok=True)  # noqa: ASYNC240
            template_path.unlink(missing_ok=True)  # noqa: ASYNC240

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid request JSON: {e}") from e
    except Exception as e:
        logger.exception("Presentation generation failed")
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}") from e


@app.post("/api/qa", response_model=QAResponse)
async def qa(
    presentation: Annotated[UploadFile, File(description="Presentation .pptx file to validate")],
    template: Annotated[  # noqa: ARG001
        UploadFile | None,
        File(description="Optional template .pptx for style conformance validation"),
    ] = None,
    request: Annotated[str, Form(description="JSON-encoded QARequest")] = "{}",
) -> QAResponse:
    """Run quality assurance checks on PowerPoint presentation.

    Args:
        presentation: Presentation .pptx file to validate
        template: Optional template .pptx for style conformance (unused, reserved for future)
        request: JSON-encoded request parameters

    Returns:
        QA report and validation results

    Raises:
        HTTPException: If QA validation fails
    """
    try:
        # Parse request parameters
        req_data = json.loads(request)
        req_model = QARequest(**req_data)

        # Save uploaded presentation to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as pres_tmp:
            pres_content = await presentation.read()
            pres_tmp.write(pres_content)
            pres_path = Path(pres_tmp.name)

        try:
            # Load presentation
            logger.info("Running QA on: %s", presentation.filename)
            wrapper = PresentationWrapper()
            wrapper.load_template(str(pres_path))

            # Run QA validation
            engine = QAEngine(language=req_model.language)
            qa_report = engine.validate(wrapper)

            # Format report based on requested format
            if req_model.format == "markdown":
                report_language: Literal["en", "ja"] = (
                    req_model.language if req_model.language else "en"
                )
                report_content: dict[str, Any] | str = qa_report.to_markdown(
                    language=report_language
                )
            else:
                report_content = json.loads(qa_report.to_json())

            # Handle auto-fix if requested
            fixed_file_id = None
            if req_model.autofix and not qa_report.passed:
                # Note: Auto-fix integration will be fully implemented when
                # FixEngine is integrated with QA workflow
                logger.warning("Auto-fix requested but not yet fully implemented")

            return QAResponse(
                report=report_content,
                passed=qa_report.passed,
                file_id=fixed_file_id,
            )

        finally:
            # Clean up temporary file
            # Note: Using sync unlink() in async context is acceptable here because:
            # 1. File operations are fast for small temp files
            # 2. This is cleanup code, not performance-critical
            # 3. Keeps code simple without async file I/O dependencies
            pres_path.unlink(missing_ok=True)  # noqa: ASYNC240

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid request JSON: {e}") from e
    except Exception as e:
        logger.exception("QA validation failed")
        raise HTTPException(status_code=500, detail=f"QA validation failed: {e}") from e


@app.get("/api/download/{file_id}")
async def download(file_id: str) -> FileResponse:
    """Download generated or fixed presentation file.

    Args:
        file_id: Unique file identifier from previous API call

    Returns:
        Presentation file download

    Raises:
        HTTPException: If file not found
    """
    if file_id not in _file_storage:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = _file_storage[file_id]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File no longer available")

    return FileResponse(
        path=str(file_path),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=f"presentation_{file_id}.pptx",
    )


# Made with Bob
