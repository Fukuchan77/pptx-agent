# API Reference - AI PowerPoint Presentation Generator

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
def generate_presentation(
    input_text: str,
    template_path: str,
    output_path: str,
    template_manifest: TemplateManifest | None = None,
    output_language: Literal["en", "ja"] | None = None,
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
from pathlib import Path
from pptx_agent.pipeline import generate_presentation

input_text = Path("input.txt").read_text()
result = generate_presentation(
    input_text=input_text,
    template_path="templates/basic-template.pptx",
    output_path="output.pptx",
    output_language="en"
)
print(f"Generated: {result}")
```

## Agents

### Story Analyzer

**Module**: `pptx_agent.agents.story_analyzer`

#### `analyze_story(text: str) -> StoryAnalysis`

Analyzes input text to extract story elements.

**Parameters**:

- `text` (`str`): Input text to analyze (plain text or Markdown)

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
from pptx_agent.agents.story_analyzer import analyze_story

text = """
# AI in Healthcare
Artificial Intelligence is transforming medical diagnosis...
"""

analysis = analyze_story(text)
print(f"Topic: {analysis.topic}")
print(f"Language: {analysis.language}")
print(f"Tone: {analysis.tone}")
```

### Outline Generator

**Module**: `pptx_agent.agents.outline_generator`

#### `generate_outline(story: StoryAnalysis) -> PresentationOutline`

Generates presentation outline from story analysis.

**Parameters**:

- `story` (`StoryAnalysis`): Story analysis object

**Returns**:

- `PresentationOutline`: Outline containing:
  - `title` (`str`): Presentation title
  - `slides` (`list[SlideContent]`): List of slide content
  - `output_language` (`Literal["en", "ja"]`): Output language

**Raises**:

- `ValueError`: If story is invalid or cannot generate valid outline

**Example**:

```python
from pptx_agent.agents.story_analyzer import analyze_story
from pptx_agent.agents.outline_generator import generate_outline

story = analyze_story("Your text here...")
outline = generate_outline(story)

print(f"Title: {outline.title}")
print(f"Slides: {len(outline.slides)}")
for slide in outline.slides:
    print(f"  - Slide {slide.slide_number}: {slide.title}")
```

### Content Generator

**Module**: `pptx_agent.agents.content_generator`

#### `generate_content(outline: PresentationOutline, manifest: TemplateManifest | None = None) -> PresentationSchema`

Generates detailed content for each slide in the outline.

**Parameters**:

- `outline` (`PresentationOutline`): Presentation outline
- `manifest` (`TemplateManifest | None`): Optional template manifest for layout validation

**Returns**:

- `PresentationSchema`: Complete presentation schema with detailed slide content

**Example**:

```python
from pptx_agent.agents.content_generator import generate_content

content = generate_content(outline, template_manifest)
print(f"Generated {len(content.slides)} slides")
```

### Overflow Resolver

**Module**: `pptx_agent.agents.overflow_resolver`

#### `resolve_overflow(slide: SlideContent, manifest: TemplateManifest, language: Literal["en", "ja"]) -> OverflowResolution`

Analyzes text overflow and determines resolution strategy.

**Parameters**:

- `slide` (`SlideContent`): Slide to analyze
- `manifest` (`TemplateManifest`): Template manifest with capacity information
- `language` (`Literal["en", "ja"]`): Output language for capacity calculation

**Returns**:

- `OverflowResolution`: Resolution result containing:
  - `overflow_detected` (`bool`): Whether overflow was detected
  - `overflow_percentage` (`float`): Percentage of overflow
  - `strategy` (`OverflowStrategy`): Recommended strategy
  - `alternative_layout` (`str | None`): Alternative layout name if applicable

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

- Title length: ≤60 characters
- Slide number: ≥1

### PresentationSchema

**Module**: `pptx_agent.schemas.presentation`

Complete presentation schema.

**Fields**:

- `title` (`str`): Presentation title
- `slides` (`list[SlideSchema]`): List of detailed slides

### SlideSchema

**Module**: `pptx_agent.schemas.slide`

Detailed slide schema.

**Fields**:

- `slide_number` (`int`): Slide number
- `layout_name` (`str`): Layout name
- `title` (`str`): Slide title
- `text_blocks` (`list[TextBlock]`): Text content blocks
- `chart_block` (`ChartBlock | None`): Optional chart
- `table_block` (`TableBlock | None`): Optional table
- `smartart_block` (`SmartArtBlock | None`): Optional SmartArt
- `notes` (`str`): Speaker notes

### TextBlock

**Module**: `pptx_agent.schemas.text`

Text content block.

**Fields**:

- `placeholder_name` (`str`): Target placeholder name
- `content` (`str`): Text content
- `bullet_points` (`list[str] | None`): Optional bullet points

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
- `has_header_row` (`bool`): Whether first row is header

**Example**:

```python
from pptx_agent.schemas.visual_assets import TableBlock

table = TableBlock(
    placeholder_name="Table Placeholder",
    headers=["Product", "Price", "Stock"],
    rows=[
        ["Widget A", "$10", "100"],
        ["Widget B", "$15", "50"]
    ],
    has_header_row=True
)
```

### SmartArtBlock

**Module**: `pptx_agent.schemas.visual_assets`

SmartArt specification.

**Fields**:

- `placeholder_name` (`str`): Target placeholder
- `layout_type` (`str`): SmartArt layout type
- `nodes` (`list[str]`): Node text content

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

#### `validate_and_sanitize(text: str, max_length: int = 30000, min_length: int = 10, log_level: str = "INFO") -> str`

Validates and sanitizes input text.

**Parameters**:

- `text` (`str`): Input text to validate
- `max_length` (`int`): Maximum allowed length (default: 30000)
- `min_length` (`int`): Minimum required length (default: 10)
- `log_level` (`str`): Logging level (default: "INFO")

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

#### `validate_content(content: PresentationSchema, outline: PresentationOutline, manifest: TemplateManifest | None = None) -> PresentationSchema`

Validates generated content against business rules.

**Parameters**:

- `content` (`PresentationSchema`): Content to validate
- `outline` (`PresentationOutline`): Original outline
- `manifest` (`TemplateManifest | None`): Optional template manifest

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

**Module**: `pptx_agent.validators.
