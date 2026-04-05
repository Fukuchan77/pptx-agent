# PowerPoint Templates Guide

This directory contains PowerPoint templates for the AI PowerPoint Presentation Generator. Templates define the visual design, layouts, placeholders, and structure that the AI uses when generating presentations.

## Available Templates

### 1. basic-template.pptx ✅ AVAILABLE

**Purpose**: General-purpose template for standard business presentations

**Features**:

- Title slide layout
- Content slides with bullet points
- Section header layouts
- Two-column layouts
- Basic color theme and fonts

**Use Cases**:

- Business proposals
- Status reports
- General presentations
- Meeting decks

**Usage**:

```bash
python -m pptx_agent.main \
  --input input.txt \
  --template templates/basic-template.pptx \
  --output output.pptx
```

---

### 2. japanese-template.pptx ✅ AVAILABLE

**Purpose**: Template optimized for Japanese language content

**Features**:

- Japanese-friendly fonts (supports full-width characters)
- Text capacity calculations optimized for Japanese (0.55x ratio)
- Cultural design considerations
- Proper spacing for kanji, hiragana, and katakana

**Use Cases**:

- Japanese business presentations
- Educational content in Japanese
- Mixed Japanese-English technical documents

**Usage**:

```bash
python -m pptx_agent.main \
  --input japanese_input.txt \
  --template templates/japanese-template.pptx \
  --output output_ja.pptx \
  --language ja
```

---

### 3. Data Visualization Template ⚠️ SPECIFICATION ONLY

**Status**: Specification exists ([`DATA-TEMPLATE-SPEC.md`](DATA-TEMPLATE-SPEC.md)), but .pptx file must be created manually

**Purpose**: Template with layouts optimized for charts and tables

**Planned Features**:

- Chart placeholder layouts (bar, line, pie, scatter, area, radar, doughnut)
- Table layouts with appropriate sizing
- Data-focused design with minimal text
- Color schemes optimized for data visualization

**How to Create**:

1. Open Microsoft PowerPoint or LibreOffice Impress
2. Follow specifications in `DATA-TEMPLATE-SPEC.md`
3. Create slide layouts with chart and table placeholders
4. Save as `data-template.pptx` in this directory

**Planned Usage**:

```bash
python -m pptx_agent.main \
  --input data_story.txt \
  --template templates/data-template.pptx \
  --output data_presentation.pptx
```

---

### 4. SmartArt Template ⚠️ SPECIFICATION ONLY

**Status**: Specification exists ([`SMARTART-TEMPLATE-SPEC.md`](SMARTART-TEMPLATE-SPEC.md)), but .pptx file must be created manually

**Purpose**: Template with SmartArt diagrams for process flows, hierarchies, and cycles

**Planned Features**:

- Process flow SmartArt layouts
- Hierarchy/organizational chart layouts
- Cycle/circular flow layouts
- SmartArt XML structures for AI population

**How to Create**:

1. Open Microsoft PowerPoint or LibreOffice Impress
2. Follow specifications in `SMARTART-TEMPLATE-SPEC.md`
3. Create slide layouts with SmartArt diagrams
4. Save as `smartart-template.pptx` in this directory

**Planned Usage**:

```bash
python -m pptx_agent.main \
  --input process_story.txt \
  --template templates/smartart-template.pptx \
  --output process_presentation.pptx
```

---

## Template Structure Requirements

All templates MUST follow these requirements to work with the AI generator:

### Required Slide Master Elements

1. **Slide Master**: Base design with theme colors and fonts
2. **Title Slide Layout**: For presentation opening
3. **Content Layouts**: For main content slides
4. **Section Header Layouts**: For section dividers

### Placeholder Requirements

Each content layout must have **named placeholders**:

- `Title`: For slide titles (required)
- `Content`: For body text, bullet points
- `Text 1`, `Text 2`: For two-column layouts
- `Chart 1`: For chart placeholders
- `Table 1`: For table placeholders

### Text Capacity Guidelines

The AI calculates text capacity based on placeholder dimensions:

- **English text**: 1.0x ratio (standard character width)
- **Japanese text**: 0.55x ratio (full-width characters need ~1.8x more space)

Ensure placeholders are sized appropriately for expected content volume.

### SmartArt Requirements

For SmartArt-enabled templates:

1. SmartArt must be **pre-configured** in the template
2. The AI populates existing SmartArt nodes with text
3. The AI cannot create new SmartArt from scratch
4. Node count must match between template and generated content

---

## Creating Custom Templates

### Step 1: Design in PowerPoint

1. Open Microsoft PowerPoint or LibreOffice Impress
2. Create a new presentation
3. Design your slide master and color theme
4. Create slide layouts with appropriate placeholders

### Step 2: Name Placeholders

1. For each placeholder, set a clear name:
   - Right-click placeholder → Format Shape → Alt Text
   - Or use Selection Pane to rename placeholders
2. Use standard names: `Title`, `Content`, `Text 1`, `Chart 1`, etc.

### Step 3: Test with Template Parser

```bash
python -m pptx_agent.template_parser.parser templates/your-template.pptx
```

This will generate a JSON manifest showing:

- Available layouts
- Placeholder configurations
- Text capacity estimates
- SmartArt configurations (if any)

### Step 4: Verify Generation

Test your template with sample content:

```bash
python -m pptx_agent.main \
  --input tests/fixtures/sample_story_en.txt \
  --template templates/your-template.pptx \
  --output test_output.pptx
```

Open `test_output.pptx` in PowerPoint/Impress to verify:

- All layouts applied correctly
- Text fits within placeholders
- Colors and fonts preserved
- No formatting errors

---

## Template Design Best Practices

### Visual Design

1. **Consistent Theme**: Use slide master for consistent colors and fonts
2. **Readable Fonts**: Choose fonts that work well at presentation scale
3. **Sufficient Contrast**: Ensure text is readable against backgrounds
4. **White Space**: Leave adequate margins around text areas

### Layout Design

1. **Multiple Layouts**: Provide variety (title-only, single-column, two-column, chart, table)
2. **Flexible Sizing**: Different placeholder sizes for different content volumes
3. **Clear Hierarchy**: Visual distinction between titles, headings, and body text
4. **Alignment**: Consistent alignment across all layouts

### Placeholder Sizing

1. **Title Placeholders**: ~60 characters maximum
2. **Body Text**: 4-6 bullet points with ~20-30 words each
3. **Two-Column**: Split content evenly between columns
4. **Chart Areas**: Large enough for legends and labels
5. **Table Areas**: Space for headers and 10-20 rows

### Language Considerations

For **Japanese templates**:

- Use fonts that support full-width characters (MS Mincho, MS Gothic, Meiryo)
- Increase placeholder sizes by ~45% compared to English templates
- Test with actual Japanese content
- Consider vertical text option for specific layouts

For **English templates**:

- Standard fonts work well (Arial, Calibri, Helvetica)
- Follow standard sizing guidelines
- Ensure readability at distance

---

## Template Manifest

When you provide a template to the AI, it generates a manifest containing:

```json
{
  "layouts": [
    {
      "name": "Title Slide",
      "placeholders": [
        {
          "name": "Title",
          "type": "TITLE",
          "capacity": 60
        }
      ]
    }
  ],
  "theme": {
    "colors": ["#1F4788", "#FFFFFF"],
    "fonts": ["Calibri", "Arial"]
  }
}
```

The AI uses this manifest to:

- Select appropriate layouts for each slide
- Validate that generated text fits within capacity
- Generate content that matches template structure

---

## Troubleshooting

### Issue: Text Overflow

**Symptom**: Generated text doesn't fit in placeholders

**Solutions**:

1. Increase placeholder size in template
2. Use language-appropriate capacity ratio
3. Enable overflow resolution in pipeline (automatic)

### Issue: Missing Layouts

**Symptom**: AI generates error about missing layout

**Solutions**:

1. Ensure template has required layouts (Title, Content)
2. Check placeholder names match expected values
3. Verify template manifest generation succeeds

### Issue: SmartArt Not Populated

**Symptom**: SmartArt appears empty or unchanged

**Solutions**:

1. Verify SmartArt exists in template (AI cannot create it)
2. Check node count matches between template and content
3. Ensure SmartArt has proper XML structure

### Issue: Incorrect Language Detection

**Symptom**: Japanese text treated as English (or vice versa)

**Solutions**:

1. Explicitly specify language with `--language ja` or `--language en`
2. Verify input text has sufficient language-specific characters
3. Use language-appropriate template

---

## Template Versioning

When updating templates:

1. **Increment version** in filename: `template-v1.pptx` → `template-v2.pptx`
2. **Document changes** in commit message or changelog
3. **Test backward compatibility** with existing content
4. **Update manifest** if layout names or structure changes

---

## Contributing Templates

To contribute new templates to the project:

1. Design template following requirements above
2. Test with multiple content types (English, Japanese, charts, tables)
3. Verify ≥80% success rate with various inputs
4. Document template features and use cases
5. Submit PR with template file and updated README

---

## Resources

- **PowerPoint Help**: https://support.microsoft.com/powerpoint
- **LibreOffice Impress**: https://www.libreoffice.org/discover/impress/
- **python-pptx Documentation**: https://python-pptx.readthedocs.io/
- **Project Documentation**: [`../docs/`](../docs/)

---

## License

Templates in this directory are provided under the same license as the main project. See [`../LICENSE`](../LICENSE) for details.

---

**Last Updated**: 2026-04-05
**Maintained By**: AI PowerPoint Generator Project Team
