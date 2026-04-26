# API Reference - AI PowerPoint Presentation Generator

> **Language**: This document is available in English only.
> **言語**: このドキュメントは英語版のみ提供されています。

## Table of Contents

1. [Main Entry Points](#main-entry-points)
2. [Pipeline](#pipeline)
3. [Agents](#agents)
4. [Schemas](#schemas)
5. [Validators](#validators)
6. [Template Parser](#template-parser)
7. [Utilities](#utilities)
8. [Configuration](#configuration)

## Main Entry Points

### CLI Interface

**Module**: `pptx_agent.main`

#### `main() -> int`

Main CLI entry point.

**Returns**:

- `int`: Exit code (0 for success, non-zero for errors)

**Example**:

```python
import sys
from pptx_agent.main import main

sys.exit(main())
```

**Command Line Usage**:

```bash
uv run python -m pptx_agent.main \
  --input input.txt \
  --template template.pptx \
  --output output.pptx \
  [--language en|ja] \
  [--manifest manifest.json] \
  [--verbose]
```

## Pipeline

### `generate_presentation()`

**Module**: `pptx_agent.pipeline`

Main pipeline function that orchestrates the complete presentation generation workflow.

```python
async def generate_presentation(
    input_text: str,
    template_path: str,
    output_path: str,
    template_manifest: TemplateManifest | None = None,
    output_language: Literal["en", "ja"] | None = None,
    *,
    use_llm: bool = True,
) -> str
```

**Parameters**:

- `input_text` (`str`): Input text content to convert into presentation
- `template_path` (`str`): Path to PowerPoint template file (.pptx)
- `output_path` (`str`): Path where generated presentation should be saved
- `template_manifest` (`TemplateManifest | None`): Optional pre-parsed template manifest for validation
- `output_language` (`Literal["en", "ja"] | None`): Optional explicit output language

**Returns**:

- `str`: Path to the generated .pptx file (same as output_path)

**Raises**:

- `ValueError`: If input text is invalid or cannot be analyzed
- `InvalidFileError`: If validation fails at any stage
- `FileNotFoundError`: If template file doesn't exist

**Example**:

```python
import asyncio
from pathlib import Path
from pptx_agent.pipeline import generate_presentation

async def main():
    input_text = Path("input.txt").read_text()
    result = await generate_presentation(
        input_text=input_text,
        template_path="templates/basic-template.pptx",
        output_path="output.pptx",
        output_language="en"
    )
    print(f"Generated: {result}")

# Run the async function
asyncio.run(main())
```

## Agents

### Story Analyzer

**Module**: `pptx_agent.agents.story_analyzer`

#### `analyze_story(text: str, *, use_llm: bool = True) -> StoryAnalysis`

Analyzes input text to extract story elements.

**Signature**:

```python
async def analyze_story(text: str, *, use_llm: bool = True) -> StoryAnalysis
```

**Parameters**:

- `text` (`str`): Input text to analyze (plain text or Markdown)
- `use_llm` (`bool`): If True, use LLM for analysis. If False, use heuristic fallback (default: True)

**Returns**:

- `StoryAnalysis`: Analysis result containing:
  - `topic` (`str`): Main topic or subject
  - `target_audience` (`str`): Identified target audience
  - `key_message` (`str`): Primary message or takeaway
  - `tone` (`str`): Communication tone (formal, casual, professional, etc.)
  - `language` (`Literal["en", "ja"]`): Detected language
  - `suggested_structure` (`str | None`): Optional suggested presentation structure

**Raises**:

- `InputValidationError`: If text is empty or whitespace-only

**Example**:

```python
import asyncio
from pptx_agent.agents.story_analyzer import analyze_story

async def main():
    text = """
    # AI in Healthcare
    Artificial Intelligence is transforming medical diagnosis...
    """

    analysis = await analyze_story(text)
    print(f"Topic: {analysis.topic}")
    print(f"Language: {analysis.language}")
    print(f"Tone: {analysis.tone}")

asyncio.run(main())
```

### Outline Generator

**Module**: `pptx_agent.agents.outline_generator`

#### `generate_outline(story: StoryAnalysis, manifest: TemplateManifest | None = None, *, use_llm: bool = True) -> PresentationOutline`

Generates presentation outline from story analysis.

**Signature**:

```python
async def generate_outline(
    story: StoryAnalysis,
    manifest: TemplateManifest | None = None,
    *,
    use_llm: bool = True
) -> PresentationOutline
```

**Parameters**:

- `story` (`StoryAnalysis`): Story analysis object
- `manifest` (`TemplateManifest | None`): Optional template manifest for validation
- `use_llm` (`bool`): If True, use LLM for generation. If False, use heuristic fallback (default: True)

**Returns**:

- `PresentationOutline`: Outline containing:
  - `title` (`str`): Presentation title
  - `slides` (`list[SlideContent]`): List of slide content
  - `output_language` (`Literal["en", "ja"]`): Output language

**Raises**:

- `ValueError`: If story is invalid or cannot generate valid outline

**Example**:

```python
import asyncio
from pptx_agent.agents.story_analyzer import analyze_story
from pptx_agent.agents.outline_generator import generate_outline

async def main():
    story = await analyze_story("Your text here...")
    outline = await generate_outline(story)

    print(f"Title: {outline.title}")
    print(f"Slides: {len(outline.slides)}")
    for slide in outline.slides:
        print(f"  - Slide {slide.slide_number}: {slide.title}")

asyncio.run(main())
```

### Content Generator

**Module**: `pptx_agent.agents.content_generator`

#### `generate_content(outline: PresentationOutline, manifest: TemplateManifest | None = None, *, use_llm: bool = True) -> PresentationSchema`

Generates detailed content for each slide in the outline.

**Signature**:

```python
async def generate_content(
    outline: PresentationOutline,
    manifest: TemplateManifest | None = None,
    *,
    use_llm: bool = True
) -> PresentationSchema
```

**Parameters**:

- `outline` (`PresentationOutline`): Presentation outline
- `manifest` (`TemplateManifest | None`): Optional template manifest for layout validation
- `use_llm` (`bool`): If True, use LLM for generation. If False, use heuristic fallback (default: True)

**Returns**:

- `PresentationSchema`: Complete presentation schema with detailed slide content

**Example**:

```python
import asyncio
from pptx_agent.agents.content_generator import generate_content

async def main():
    content = await generate_content(outline, template_manifest)
    print(f"Generated {len(content.slides)} slides")

asyncio.run(main())
```

### Overflow Resolver

**Module**: `pptx_agent.agents.overflow_resolver`

#### `resolve_overflow(slide: SlideContent, manifest: TemplateManifest, language: Literal["en", "ja"] | None = None) -> OverflowResolution`

Analyzes text overflow and determines resolution strategy.

**Parameters**:

- `slide` (`SlideContent`): Slide to analyze
- `manifest` (`TemplateManifest`): Template manifest with capacity information
- `language` (`Literal["en", "ja"]`): Output language for capacity calculation

**Returns**:

- `strategy` (`OverflowStrategy`): Recommended strategy
- `overflow_detected` (`bool`): Whether overflow was detected
- `overflow_percentage` (`float`): Percentage of overflow
- `suggested_layout` (`str | None`): Alternative layout name if applicable
- `split_point` (`int | None`): Best character index to split at
- `target_length` (`int | None`): Target length for summarization

**Example**:

```python
from pptx_agent.agents.overflow_resolver import resolve_overflow

resolution = resolve_overflow(slide, manifest, "en")
if resolution.overflow_detected:
    print(f"Overflow: {resolution.overflow_percentage:.1f}%")
    print(f"Strategy: {resolution.strategy}")
```

## Schemas

### PresentationOutline

**Module**: `pptx_agent.schemas.outline`

High-level presentation structure.

**Fields**:

- `title` (`str`): Presentation title
- `slides` (`list[SlideContent]`): List of slide content
- `output_language` (`Literal["en", "ja"]`): Output language

**Example**:

```python
from pptx_agent.schemas.outline import PresentationOutline, SlideContent

outline = PresentationOutline(
    title="My Presentation",
    slides=[
        SlideContent(
            slide_number=1,
            layout_name="Title Slide",
            title="Introduction",
            content="Welcome to the presentation"
        )
    ],
    output_language="en"
)
```

### SlideContent

**Module**: `pptx_agent.schemas.outline`

Content for a single slide.

**Fields**:

- `slide_number` (`int`): Slide number (1-indexed)
- `layout_name` (`str`): Layout name from template
- `title` (`str`): Slide title
- `content` (`str`): Slide content text

**Validators**:

- Slide number: ≥1

### PresentationSchema

**Module**: `pptx_agent.schemas.presentation`

Complete presentation schema.

**Fields**:

- `title` (`str`): Presentation title
- `slides` (`list[SlideSchema]`): List of detailed slides
- `metadata` (`dict[str, Any]`): Optional metadata

### SlideSchema

**Module**: `pptx_agent.schemas.slide`

Detailed slide schema.

**Fields**:

- `layout_name` (`str`): Layout name
- `title` (`str`): Slide title
- `content` (`list[ContentBlock]`): Content blocks (TextBlock, ImageBlock, ChartBlock, TableBlock, SmartArtBlock)
- `notes` (`str | None`): Speaker notes

### TextBlock

**Module**: `pptx_agent.schemas.text`

Text content block.

**Fields**:

- `placeholder_name` (`str`): Target placeholder name
- `text` (`str`): Text content
- `language` (`Literal["en", "ja"]`): Language code
- `max_capacity` (`int | None`): Optional maximal char capacity

### ImageBlock

**Module**: `pptx_agent.schemas.visual_assets`

Image content block.

**Fields**:

- `placeholder_name` (`str`): Target placeholder name
- `image_url` (`str | None`): Image URL
- `image_path` (`str | None`): Local image path
- `alt_text` (`str`): Alternative text

### ChartBlock

**Module**: `pptx_agent.schemas.visual_assets`

Chart specification.

**Fields**:

- `placeholder_name` (`str`): Target placeholder
- `chart_type` (`str`): Chart type (bar, line, pie, column, area)
- `title` (`str`): Chart title
- `data` (`dict`): Chart data with categories and series

**Example**:

```python
from pptx_agent.schemas.visual_assets import ChartBlock

chart = ChartBlock(
    placeholder_name="Chart Placeholder",
    chart_type="bar",
    title="Sales by Quarter",
    data={
        "categories": ["Q1", "Q2", "Q3", "Q4"],
        "series": [
            {"name": "Revenue", "values": [100, 150, 200, 250]}
        ]
    }
)
```

### TableBlock

**Module**: `pptx_agent.schemas.visual_assets`

Table specification.

**Fields**:

- `placeholder_name` (`str`): Target placeholder
- `headers` (`list[str]`): Table headers
- `rows` (`list[list[str]]`): Table data rows

**Example**:

```python
from pptx_agent.schemas.visual_assets import TableBlock

table = TableBlock(
    placeholder_name="Table Placeholder",
    headers=["Product", "Price", "Stock"],
    rows=[
        ["Widget A", "$10", "100"],
        ["Widget B", "$15", "50"]
    ]
)
```

### SmartArtBlock

**Module**: `pptx_agent.schemas.visual_assets`

SmartArt specification.

**Fields**:

- `placeholder_name` (`str`): Target placeholder
- `diagram_type` (`str`): SmartArt layout type
- `nodes` (`list[dict[str, Any]]`): Node data (text and level)

### TemplateManifest

**Module**: `pptx_agent.schemas.template_manifest`

Template metadata and capabilities.

**Fields**:

- `template_name` (`str`): Template name
- `layouts` (`list[LayoutInfo]`): Available layouts
- `default_language` (`Literal["en", "ja"]`): Default language

**Example**:

```python
from pptx_agent.schemas.template_manifest import TemplateManifest

manifest = TemplateManifest.model_validate_json(
    Path("manifest.json").read_text()
)
print(f"Layouts: {[l.name for l in manifest.layouts]}")
```

## Validators

### Input Validator

**Module**: `pptx_agent.validators.input_validator`

#### `validate_and_sanitize(text: str, min_length: int = 10, max_length: int = 30000, field_name: str = "text") -> str`

Validates and sanitizes input text.

**Parameters**:

- `text` (`str`): Input text to validate
- `min_length` (`int`): Minimum required length
- `max_length` (`int`): Maximum allowed length
- `field_name` (`str`): Name of field for error message

**Returns**:

- `str`: Sanitized text

**Raises**:

- `InputValidationError`: If validation fails

**Example**:

```python
from pptx_agent.validators.input_validator import validate_and_sanitize

text = "Your presentation content..."
sanitized = validate_and_sanitize(text)
```

### Outline Validator

**Module**: `pptx_agent.validators.outline_validator`

#### `validate_outline(outline: PresentationOutline, template_manifest: TemplateManifest | None = None) -> PresentationOutline`

Validates outline against template constraints.

**Parameters**:

- `outline` (`PresentationOutline`): Outline to validate
- `template_manifest` (`TemplateManifest | None`): Optional template manifest

**Returns**:

- `PresentationOutline`: Validated outline

**Raises**:

- `InvalidFileError`: If validation fails

### Content Validator

**Module**: `pptx_agent.validators.content_validator`

#### `validate_content(content: PresentationSchema, outline: PresentationOutline | None = None, _template_manifest: TemplateManifest | None = None) -> PresentationSchema`

Validates generated content against business rules.

**Parameters**:

- `content` (`PresentationSchema`): Content to validate
- `outline` (`PresentationOutline | None`): Original outline
- `_template_manifest` (`TemplateManifest | None`): Optional template manifest

**Returns**:

- `PresentationSchema`: Validated content

**Raises**:

- `ContentValidationError`: If validation fails

### File Validator

**Module**: `pptx_agent.validators.file_validator`

#### `validate_pptx_file(file_path: Path | str) -> None`

Validates PPTX file against ZIP bomb and size constraints.

**Parameters**:

- `file_path` (`Path | str`): Path to PPTX file

**Raises**:

- `InvalidFileError`: If file is invalid
- `FileSizeLimitError`: If file size exceeds limits
- `CompressionRatioError`: If compression ratio is suspicious

#### `validate_template_path(template_path: str) -> Path`

Validates template path for security and validity.

**Parameters**:

- `template_path` (`str`): Path to template file

**Returns**:

- `Path`: Absolute path to validated template

**Raises**:

- `InvalidFileError`: If file is invalid
- `SecurityValidationError`: If security check fails

### Security Validator

**Module**: `pptx_agent.validators.security`

#### `detect_prompt_injection(text: str) -> SecurityValidationResult`

Detect prompt injection attempts in input text.

**Parameters**:

- `text` (`str`): Input text to check

**Returns**:

- `SecurityValidationResult`: Detection results and sanitized text

## REST API Interface

### FastAPI Application

**Module**: `pptx_agent.interfaces.api`

The REST API provides HTTP endpoints for presentation generation, template analysis, and QA validation. All endpoints support async processing and file uploads.

**Base URL**: `http://localhost:8000` (default)

**API Documentation**: Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)

### Endpoints

#### `GET /`

Root endpoint with API information.

**Response**:

```json
{
  "name": "PPTX Agent API",
  "version": "1.0.0",
  "docs": "/docs",
  "redoc": "/redoc"
}
```

#### `GET /health`

Health check endpoint.

**Response**:

```json
{
  "status": "healthy"
}
```

#### `POST /api/analyze-template`

Analyze PowerPoint template and generate manifest.

**Request**:

- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `template` (file, required): Template .pptx file
  - `request` (form field, optional): JSON-encoded `AnalyzeTemplateRequest`

**AnalyzeTemplateRequest Schema**:

```python
{
  "language": "en",  # Default language: "en" or "ja"
  "use_cache": true  # Whether to use cached manifest
}
```

**Response**: `AnalyzeTemplateResponse`

```python
{
  "manifest": {...},      # Template manifest data
  "cache_hit": false,     # Whether manifest was from cache
  "file_id": "uuid-here"  # Unique identifier for template
}
```

**Example**:

```bash
curl -X POST "http://localhost:8000/api/analyze-template" \
  -F "template=@template.pptx" \
  -F 'request={"language":"en","use_cache":true}'
```

#### `POST /api/generate`

Generate PowerPoint presentation from text input.

**Request**:

- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `input_file` (file, required): Input text or Markdown file
  - `template` (file, required): Template .pptx file
  - `request` (form field, optional): JSON-encoded `GenerateRequest`

**GenerateRequest Schema**:

```python
{
  "language": "en",         # Output language: "en" or "ja" (auto-detected if null)
  "qa_enabled": true,       # Enable QA checks after generation
  "autofix_enabled": false  # Enable automatic issue fixing (experimental)
}
```

**Response**: `GenerateResponse`

```python
{
  "file_id": "uuid-here",        # Unique identifier for generated file
  "output_path": "/path/to/output.pptx",
  "qa_report": {...}             # QA report if qa_enabled was true
}
```

**Example**:

```bash
curl -X POST "http://localhost:8000/api/generate" \
  -F "input_file=@input.txt" \
  -F "template=@template.pptx" \
  -F 'request={"language":"en","qa_enabled":true,"autofix_enabled":false}'
```

#### `POST /api/qa`

Run quality assurance checks on PowerPoint presentation.

**Request**:

- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `presentation` (file, required): Presentation .pptx file to validate
  - `template` (file, optional): Optional template .pptx for style conformance
  - `request` (form field, optional): JSON-encoded `QARequest`

**QARequest Schema**:

```python
{
  "language": "en",           # Language override: "en" or "ja" (auto-detected if null)
  "format": "json",           # Report format: "json" or "markdown"
  "autofix": false,           # Enable automatic issue fixing
  "max_fix_iterations": 3     # Maximum fix loop iterations (1-10)
}
```

**Response**: `QAResponse`

```python
{
  "report": {...},            # QA report (JSON or Markdown string)
  "passed": true,             # Whether QA validation passed
  "file_id": "uuid-here"      # File ID for fixed presentation if autofix enabled
}
```

**Example**:

```bash
curl -X POST "http://localhost:8000/api/qa" \
  -F "presentation=@output.pptx" \
  -F 'request={"language":"en","format":"json","autofix":false}'
```

#### `GET /api/download/{file_id}`

Download generated or fixed presentation file.

**Parameters**:

- `file_id` (path, required): Unique file identifier from previous API call

**Response**:

- **Content-Type**: `application/vnd.openxmlformats-officedocument.presentationml.presentation`
- **Body**: Presentation file binary data

**Example**:

```bash
curl -X GET "http://localhost:8000/api/download/uuid-here" \
  -o downloaded.pptx
```

### Running the API Server

**Development Mode**:

```bash
# Using uvicorn directly
uvicorn pptx_agent.interfaces.api:app --reload --port 8000

# Using mise (if configured)
mise run api
```

**Production Mode**:

```bash
uvicorn pptx_agent.interfaces.api:app --host 0.0.0.0 --port 8000 --workers 4
```

## QA Module

### QA Engine

**Module**: `pptx_agent.qa.engine`

#### `QAEngine`

Quality assurance engine for presentation validation.

**Constructor**:

```python
def __init__(
    self,
    language: Literal["en", "ja"] | None = None,
    rules: list[QARule] | None = None
)
```

**Parameters**:

- `language` (`Literal["en", "ja"] | None`): Language for capacity calculations
- `rules` (`list[QARule] | None`): Custom rules (uses defaults if None)

**Methods**:

##### `validate(presentation: PresentationWrapper) -> QAReport`

Run all QA rules against presentation.

**Parameters**:

- `presentation` (`PresentationWrapper`): Presentation to validate

**Returns**:

- `QAReport`: Validation results with all detected issues

**Example**:

```python
from pptx_agent.pptx_wrapper.presentation import PresentationWrapper
from pptx_agent.qa.engine import QAEngine

# Load presentation
wrapper = PresentationWrapper()
wrapper.load_template("output.pptx")

# Run QA validation
engine = QAEngine(language="en")
report = engine.validate(wrapper)

# Check results
if report.passed:
    print("✓ QA passed - no errors")
else:
    print(f"✗ QA failed - {report.error_count} errors")
    for issue in report.issues:
        print(f"  [{issue.severity}] {issue.message}")
```

### QA Schemas

**Module**: `pptx_agent.qa.schemas`

#### `Severity`

Issue severity levels.

**Values**:

- `ERROR`: Blocks quality, must fix before release
- `WARNING`: Should fix, not blocking but affects quality
- `INFO`: Informational, optional improvement

#### `QAIssue`

Represents a single quality issue.

**Fields**:

- `rule_id` (`str`): Unique rule identifier (e.g., "QA-L-001")
- `severity` (`Severity`): Issue severity level
- `slide_index` (`int`): Zero-based slide index
- `shape_index` (`int | None`): Zero-based shape index if applicable
- `message` (`str`): Human-readable issue description
- `auto_fixable` (`bool`): Whether issue can be automatically fixed
- `suggested_fix` (`str | None`): Suggested manual fix

**Example**:

```python
from pptx_agent.qa.schemas import QAIssue, Severity

issue = QAIssue(
    rule_id="QA-L-001",
    severity=Severity.ERROR,
    slide_index=2,
    shape_index=1,
    message="Text overflow detected in title placeholder",
    auto_fixable=True,
    suggested_fix="Reduce font size or shorten text"
)
```

#### `QAReport`

Aggregates all QA issues with summary statistics.

**Fields**:

- `total_issues` (`int`): Total number of issues found
- `error_count` (`int`): Number of ERROR severity issues
- `warning_count` (`int`): Number of WARNING severity issues
- `info_count` (`int`): Number of INFO severity issues
- `issues` (`list[QAIssue]`): List of all detected issues
- `fix_iterations` (`int`): Number of fix loop iterations performed
- `passed` (`bool`): True if error_count == 0 (computed property)

**Methods**:

##### `to_json() -> str`

Serialize to JSON string for machine processing.

**Returns**:

- `str`: JSON string representation

##### `to_markdown(language: Literal["en", "ja"] = "en") -> str`

Generate human-readable Markdown report.

**Parameters**:

- `language` (`Literal["en", "ja"]`): Report language

**Returns**:

- `str`: Markdown formatted report

**Example**:

```python
from pptx_agent.qa.schemas import QAReport

# Create report
report = QAReport(
    total_issues=2,
    error_count=1,
    warning_count=1,
    info_count=0,
    issues=[...],
    fix_iterations=0
)

# Export as JSON
json_str = report.to_json()

# Export as Markdown
markdown_str = report.to_markdown(language="en")

# Check if passed
if report.passed:
    print("✓ No errors")
```

### QA Rules

**Module**: `pptx_agent.qa.rules`

#### Layout Check Rules

**Module**: `pptx_agent.qa.rules.layout_checks`

- **QA-L-001**: Text overflow detection
- **QA-L-002**: Empty title placeholder detection
- **QA-L-003**: Unpopulated placeholder detection
- **QA-L-004**: Overlapping object detection
- **QA-L-005**: Boundary overflow detection
- **QA-L-006**: Minimum font size detection

#### Content Check Rules

**Module**: `pptx_agent.qa.rules.content_checks`

- **QA-C-001**: Bullet length check
- **QA-C-002**: Duplicate title detection
- **QA-C-003**: Unpopulated image placeholder detection
- **QA-C-004**: Pathological table dimension detection
- **QA-C-005**: Missing chart data detection
- **QA-C-006**: Speaker notes verification

#### Style Check Rules

**Module**: `pptx_agent.qa.rules.style_checks`

- **QA-S-001**: Off-template font detection
- **QA-S-002**: Off-template color detection
- **QA-S-003**: Invalid bullet indent detection

## Fixer Module

### Fix Engine

**Module**: `pptx_agent.fixer.engine`

#### `FixEngine`

Automatic issue remediation engine.

**Constructor**:

```python
def __init__(
    self,
    max_iterations: int = 3,
    strategies: list[FixStrategy] | None = None
)
```

**Parameters**:

- `max_iterations` (`int`): Maximum fix loop iterations (default: 3)
- `strategies` (`list[FixStrategy] | None`): Custom strategies (uses defaults if None)

**Methods**:

##### `fix_loop(presentation: PresentationWrapper, qa_report: QAReport) -> FixLoopResult`

Run iterative fix loop until issues resolved or max iterations reached.

**Parameters**:

- `presentation` (`PresentationWrapper`): Presentation to fix
- `qa_report` (`QAReport`): Initial QA report with issues

**Returns**:

- `FixLoopResult`: Fix loop results with final QA report

**Example**:

```python
from pptx_agent.fixer.engine import FixEngine
from pptx_agent.qa.engine import QAEngine
from pptx_agent.pptx_wrapper.presentation import PresentationWrapper

# Load presentation
wrapper = PresentationWrapper()
wrapper.load_template("output.pptx")

# Run initial QA
qa_engine = QAEngine()
initial_report = qa_engine.validate(wrapper)

# Run fix loop if issues found
if not initial_report.passed:
    fix_engine = FixEngine(max_iterations=3)
    result = fix_engine.fix_loop(wrapper, initial_report)

    print(f"Fix iterations: {result.iterations}")
    print(f"Fixes applied: {len(result.fixes_applied)}")
    print(f"Final status: {'✓ PASSED' if result.success else '✗ FAILED'}")
```

### Fixer Schemas

**Module**: `pptx_agent.fixer.schemas`

#### `FixStatus`

Fix operation status.

**Values**:

- `SUCCESS`: Fix successfully applied
- `PARTIAL`: Some issues fixed, some remain
- `FAILED`: Fix operation failed
- `SKIPPED`: Issue not auto-fixable, skipped

#### `FixResult`

Result of a single fix operation.

**Fields**:

- `issue` (`QAIssue`): The QA issue that was addressed
- `status` (`FixStatus`): Fix operation status
- `message` (`str`): Fix operation outcome description
- `changes_made` (`list[str]`): List of specific changes applied

**Example**:

```python
from pptx_agent.fixer.schemas import FixResult, FixStatus
from pptx_agent.qa.schemas import QAIssue, Severity

result = FixResult(
    issue=QAIssue(
        rule_id="QA-L-001",
        severity=Severity.ERROR,
        slide_index=2,
        shape_index=1,
        message="Text overflow detected",
        auto_fixable=True
    ),
    status=FixStatus.SUCCESS,
    message="Reduced font size from 18pt to 16pt",
    changes_made=["Font size: 18pt → 16pt"]
)
```

#### `FixLoopResult`

Result of complete fix loop with multiple iterations.

**Fields**:

- `iterations` (`int`): Number of fix loop iterations performed
- `fixes_applied` (`list[FixResult]`): List of all fix results
- `final_qa_report` (`QAReport`): QA report after final iteration
- `success` (`bool`): True if all errors resolved (error_count == 0)

**Example**:

```python
from pptx_agent.fixer.schemas import FixLoopResult

result = FixLoopResult(
    iterations=2,
    fixes_applied=[...],
    final_qa_report=QAReport(...),
    success=True
)

if result.success:
    print(f"✓ All issues resolved in {result.iterations} iterations")
else:
    print(f"✗ {result.final_qa_report.error_count} errors remain")
```

### Fix Strategies

**Module**: `pptx_agent.fixer.strategies`

#### Text Overflow Strategies

**Module**: `pptx_agent.fixer.strategies.text_overflow`

- Font reduction: Reduce font size to fit text
- Layout switching: Switch to layout with more capacity
- Content summarization: Use LLM to summarize overflowing text

#### Placeholder Strategies

**Module**: `pptx_agent.fixer.strategies.placeholder`

- Empty placeholder population: Fill empty placeholders with appropriate content

#### Style Strategies

**Module**: `pptx_agent.fixer.strategies.style`

- Style reset: Reset fonts/colors to template master styles

## Cache Module

### Cache Manager

**Module**: `pptx_agent.cache.manager`

#### `CacheManager`

Template manifest caching with SHA-256 keying.

**Constructor**:

```python
def __init__(self, cache_dir: Path | None = None)
```

**Parameters**:

- `cache_dir` (`Path | None`): Custom cache directory (uses system cache dir if None)

**Methods**:

##### `get_manifest(template_path: Path) -> dict[str, Any] | None`

Retrieve cached manifest for template.

**Parameters**:

- `template_path` (`Path`): Path to template file

**Returns**:

- `dict[str, Any] | None`: Cached manifest or None if not found

##### `set_manifest(template_path: Path, manifest: dict[str, Any]) -> None`

Cache manifest for template.

**Parameters**:

- `template_path` (`Path`): Path to template file
- `manifest` (`dict[str, Any]`): Manifest data to cache

##### `invalidate(template_path: Path) -> None`

Invalidate cached manifest for template.

**Parameters**:

- `template_path` (`Path`): Path to template file

##### `cleanup_stale(max_age_days: int = 30) -> int`

Remove cache entries older than specified age.

**Parameters**:

- `max_age_days` (`int`): Maximum age in days (default: 30)

**Returns**:

- `int`: Number of entries removed

**Example**:

```python
from pathlib import Path
from pptx_agent.cache.manager import CacheManager

# Initialize cache manager
cache = CacheManager()

# Check for cached manifest
template_path = Path("template.pptx")
manifest = cache.get_manifest(template_path)

if manifest:
    print("✓ Cache hit")
else:
    print("✗ Cache miss - parsing template")
    # ... parse template and generate manifest ...
    cache.set_manifest(template_path, manifest_dict)

# Cleanup old entries
removed = cache.cleanup_stale(max_age_days=30)
print(f"Removed {removed} stale cache entries")
```

## CLI Interface

### Enhanced CLI Commands

**Module**: `pptx_agent.interfaces.cli`

The CLI has been enhanced with additional commands for QA and template analysis.

#### `analyze-template` Command

Analyze template and generate manifest.

```bash
python -m pptx_agent.interfaces.cli analyze-template \
  --template template.pptx \
  --output manifest.json \
  [--language en|ja] \
  [--no-cache]
```

#### `qa` Command

Run QA validation on existing presentation.

```bash
python -m pptx_agent.interfaces.cli qa \
  --input presentation.pptx \
  [--template template.pptx] \
  [--language en|ja] \
  [--format json|markdown] \
  [--autofix] \
  [--max-iterations 3] \
  [--output report.json]
```

#### Enhanced `generate` Command

Generate presentation with QA and auto-fix options.

```bash
python -m pptx_agent.main \
  --input input.txt \
  --template template.pptx \
  --output output.pptx \
  [--language en|ja] \
  [--qa] \
  [--autofix] \
  [--max-fix-iterations 3] \
  [--verbose]
```
