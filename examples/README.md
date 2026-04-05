# Example Input Files

This directory contains example input files demonstrating various use cases for the AI PowerPoint Presentation Generator. These examples showcase the system's capabilities across different content types, languages, and visualization needs.

## Available Examples

### 01-business-quarterly-review.txt

**Type**: Business Presentation (English)
**Content**: Comprehensive quarterly business review covering financial performance, customer metrics, sales performance, market position, and operational excellence
**Target Audience**: Executives, board members, investors
**Recommended Template**: `basic-template.pptx` or `japanese-template.pptx`
**Expected Slides**: 15-20 slides
**Features**: Executive summary, financial metrics, strategic initiatives, KPIs

**Usage**:

```bash
python -m pptx_agent.main \
  --input examples/01-business-quarterly-review.txt \
  --template templates/basic-template.pptx \
  --output output/quarterly-review.pptx
```

**What to Expect**:

- Title slide with presentation overview
- Section headers for major topics
- Content slides with bullet points for key metrics
- Strategic initiatives and priorities
- Conclusion with next steps

---

### 02-technical-architecture-overview.txt

**Type**: Technical Presentation (English)
**Content**: Cloud-native microservices platform architecture covering architectural principles, technology stack, data management, observability, and security
**Target Audience**: Technical teams, architects, engineers
**Recommended Template**: `basic-template.pptx`
**Expected Slides**: 18-25 slides
**Features**: Technical diagrams concepts, architecture patterns, technology decisions

**Usage**:

```bash
python -m pptx_agent.main \
  --input examples/02-technical-architecture-overview.txt \
  --template templates/basic-template.pptx \
  --output output/architecture-overview.pptx
```

**What to Expect**:

- Technical content with architecture principles
- System components and integrations
- Technology stack descriptions
- Best practices and design patterns
- Performance and scalability considerations

---

### 03-python-programming-basics-ja.txt

**Type**: Educational Presentation (Japanese)
**Content**: Python programming basics tutorial covering language overview, development environment, syntax, control structures, data structures, and functions
**Target Audience**: Programming beginners, students, trainees
**Recommended Template**: `japanese-template.pptx`
**Expected Slides**: 20-25 slides
**Features**: Japanese full-width characters, educational structure, progressive learning

**Usage**:

```bash
python -m pptx_agent.main \
  --input examples/03-python-programming-basics-ja.txt \
  --template templates/japanese-template.pptx \
  --output output/python-basics-ja.pptx \
  --language ja
```

**What to Expect**:

- Japanese text with proper character encoding
- Educational flow from basics to advanced
- Code concepts explained in Japanese
- Learning objectives and examples
- Progressive difficulty structure

**Important Notes**:

- Use `--language ja` flag to ensure proper text capacity calculations for Japanese characters
- Japanese template optimized for full-width characters (0.55x capacity ratio)
- Text capacity automatically adjusted for Japanese language

---

### 04-sales-analytics-dashboard.txt

**Type**: Data Visualization Presentation (English)
**Content**: Comprehensive sales analytics with numerical data, metrics, trends, and performance indicators across revenue, customers, sales, marketing, and products
**Target Audience**: Sales leaders, executives, analysts
**Recommended Template**: `basic-template.pptx` (or `data-template.pptx` when available)
**Expected Slides**: 20-30 slides
**Features**: Rich numerical data, metrics, trends, percentages, growth rates

**Usage**:

```bash
python -m pptx_agent.main \
  --input examples/04-sales-analytics-dashboard.txt \
  --template templates/basic-template.pptx \
  --output output/sales-analytics.pptx
```

**What to Expect**:

- Data-rich slides with metrics and KPIs
- Revenue performance analysis
- Customer acquisition and retention metrics
- Sales team productivity data
- Marketing performance indicators

**Note**: When `data-template.pptx` becomes available, the AI will automatically convert numerical data into charts and tables. Currently, data is presented in text format with clear numerical highlights.

---

### 05-product-development-process.txt

**Type**: Process Flow Presentation (English)
**Content**: Product development lifecycle covering discovery, ideation, planning, development, testing, deployment, support, and continuous improvement phases
**Target Audience**: Product managers, development teams, stakeholders
**Recommended Template**: `basic-template.pptx` (or `smartart-template.pptx` when available)
**Expected Slides**: 25-30 slides
**Features**: Sequential processes, hierarchical structures, workflow cycles

**Usage**:

```bash
python -m pptx_agent.main \
  --input examples/05-product-development-process.txt \
  --template templates/basic-template.pptx \
  --output output/product-development.pptx
```

**What to Expect**:

- Process phases described sequentially
- Hierarchical team structures
- Workflow and decision-making processes
- Governance and quality standards
- Metrics and success criteria

**Note**: When `smartart-template.pptx` becomes available, the AI will automatically convert process descriptions into SmartArt diagrams (process flows, hierarchies, cycles). Currently, processes are presented as structured text with clear phase delineation.

---

## General Usage Instructions

### Basic Command Structure

```bash
python -m pptx_agent.main \
  --input <input-file-path> \
  --template <template-file-path> \
  --output <output-file-path> \
  [--language ja|en]
```

### Parameters

- `--input`: Path to input text file (required)
- `--template`: Path to PowerPoint template file (required)
- `--output`: Path for generated presentation file (required)
- `--language`: Output language - `ja` for Japanese, `en` for English (optional, auto-detected if not specified)

### Language Detection

The system automatically detects input language, but you can explicitly specify output language:

**English Output**:

```bash
python -m pptx_agent.main \
  --input examples/01-business-quarterly-review.txt \
  --template templates/basic-template.pptx \
  --output output/presentation-en.pptx \
  --language en
```

**Japanese Output**:

```bash
python -m pptx_agent.main \
  --input examples/03-python-programming-basics-ja.txt \
  --template templates/japanese-template.pptx \
  --output output/presentation-ja.pptx \
  --language ja
```

### Template Selection Guide

| Content Type                      | Recommended Template       | Why                                    |
| --------------------------------- | -------------------------- | -------------------------------------- |
| Business presentations (English)  | `basic-template.pptx`      | General-purpose layouts, English fonts |
| Technical presentations (English) | `basic-template.pptx`      | Clear layouts for technical content    |
| Educational content (Japanese)    | `japanese-template.pptx`   | Japanese fonts, optimized capacity     |
| Data visualization                | `data-template.pptx`\*     | Chart and table layouts                |
| Process flows                     | `smartart-template.pptx`\* | SmartArt diagrams                      |

\*Templates marked with asterisk require manual creation (specifications available in `templates/` directory)

---

## Tips for Best Results

### Content Structure

1. **Clear Headings**: Use clear section headings to organize content into logical slides
2. **Concise Paragraphs**: Keep paragraphs focused on one main idea
3. **Key Points**: Highlight important metrics, dates, and decisions
4. **Logical Flow**: Structure content in a narrative flow from introduction to conclusion

### Slide Count Guidelines

- **Short presentations**: 1,000-2,000 characters → 5-10 slides
- **Medium presentations**: 2,000-5,000 characters → 10-15 slides
- **Long presentations**: 5,000-10,000 characters → 15-25 slides
- **Maximum recommended**: 30,000 characters → ~30 slides (quality may degrade beyond 20 slides)

### Language-Specific Tips

**For Japanese Content**:

- Use `japanese-template.pptx` for proper font support
- Specify `--language ja` for accurate text capacity calculations
- Japanese text requires ~1.8x more space than English (automatically handled)
- Mix of kanji, hiragana, katakana handled correctly

**For English Content**:

- `basic-template.pptx` works well for most use cases
- Technical terminology and acronyms handled appropriately
- Bullet points automatically formatted

### Data and Visualizations

**Numerical Data**:

- Include metrics with clear labels: "Revenue: $10.5M" or "Growth: 25%"
- Present data in context with comparisons and trends
- The AI will structure data appropriately in slides

**Tables** (when data-template.pptx available):

- Describe tabular data clearly with headers and rows
- Keep tables to maximum 20 rows × 10 columns
- The AI will convert text descriptions to formatted tables

**Charts** (when data-template.pptx available):

- Describe numerical relationships and trends
- Specify chart types if needed (bar, line, pie, etc.)
- The AI will identify chart-appropriate data and create visualizations

**Process Flows** (when smartart-template.pptx available):

- Describe sequential steps clearly
- Use numbered lists or phases
- The AI will convert to SmartArt diagrams

---

## Creating Your Own Examples

### Content Guidelines

1. **Start with Clear Objective**: Define what the presentation should communicate
2. **Outline Main Topics**: List 3-7 main sections
3. **Expand Each Section**: Write 2-4 paragraphs per section
4. **Add Supporting Details**: Include metrics, examples, and context
5. **Conclude with Takeaways**: Summarize key points and next steps

### Content Length Recommendations

- **Minimum**: 1,000 characters (10-line minimum, per spec FR-005)
- **Optimal**: 3,000-8,000 characters for 10-20 slide presentations
- **Maximum**: 30,000 characters (hard limit per spec FR-005)

### Writing Style Tips

**For Business Presentations**:

- Use professional, concise language
- Include specific metrics and data points
- Structure with executive summary, analysis, recommendations
- End with clear action items or next steps

**For Technical Presentations**:

- Use precise technical terminology
- Explain complex concepts in logical progression
- Include architecture, implementation, and operational details
- Balance depth with accessibility for mixed audiences

**For Educational Content**:

- Start with fundamentals and build complexity gradually
- Use examples and analogies to illustrate concepts
- Include practice scenarios or use cases
- Structure with clear learning objectives

**For Data-Driven Presentations**:

- Lead with insights, support with data
- Use specific numbers with context (trends, comparisons)
- Tell story with data progression
- Highlight key takeaways from metrics

---

## Example Workflows

### Quick Test Run

Test the system with a short example:

```bash
# Generate a presentation
python -m pptx_agent.main \
  --input examples/01-business-quarterly-review.txt \
  --template templates/basic-template.pptx \
  --output test-output.pptx

# Open in PowerPoint or LibreOffice Impress
open test-output.pptx  # macOS
start test-output.pptx  # Windows
xdg-open test-output.pptx  # Linux
```

### Batch Processing Multiple Examples

Generate all examples:

```bash
# Create output directory
mkdir -p output

# Generate each example
for example in examples/*.txt; do
    filename=$(basename "$example" .txt)
    python -m pptx_agent.main \
        --input "$example" \
        --template templates/basic-template.pptx \
        --output "output/${filename}.pptx"
    echo "Generated: output/${filename}.pptx"
done
```

### Japanese Example Workflow

```bash
# Generate Japanese presentation
python -m pptx_agent.main \
  --input examples/03-python-programming-basics-ja.txt \
  --template templates/japanese-template.pptx \
  --output output/python-basics-ja.pptx \
  --language ja

# Verify text capacity calculations worked correctly
open output/python-basics-ja.pptx
```

---

## Troubleshooting

### Issue: Generated presentation has too many slides

**Solution**: Reduce input text length or split into multiple presentations. Optimal range is 10-20 slides (quality may degrade beyond 20 slides per spec SC-013).

### Issue: Text overflow in slides

**Solution**:

- System automatically handles overflow through staged resolution (font reduction → layout change → slide split → summarization per spec FR-032)
- Use language-appropriate template (Japanese template for Japanese text)
- Specify correct language with `--language` flag

### Issue: Japanese characters display incorrectly

**Solution**:

- Use `japanese-template.pptx` template
- Specify `--language ja` parameter
- Ensure input file is UTF-8 encoded

### Issue: Presentation doesn't match expected structure

**Solution**:

- Verify input text has clear section headings
- Check that content is well-structured with logical flow
- Review generated outline for understanding of content structure

---

## Performance Expectations

Based on success criteria (spec.md):

- **Template Parsing**: <5 seconds for typical templates (SC-002)
- **Outline Generation**: 120 second timeout (FR-047)
- **Slide Content Generation**: 60 second timeout per slide (FR-048)
- **PowerPoint Rendering**: <10 seconds after content generation (SC-003)
- **Total Generation**: Target <60 seconds for 10-slide presentation excluding LLM time (SC-001)

**Note**: Actual generation time depends on:

- Input text length and complexity
- Number of slides generated
- LLM provider response time
- Template complexity

---

## Additional Resources

- **Template Documentation**: [`../templates/README.md`](../templates/README.md)
- **User Guide**: [`../docs/user-guide.md`](../docs/user-guide.md)
- **Developer Guide**: [`../docs/developer-guide.md`](../docs/developer-guide.md)
- **API Reference**: [`../docs/api-reference.md`](../docs/api-reference.md)

---

## Contributing Examples

To contribute new examples to this directory:

1. Create a well-structured text file with clear sections
2. Test generation with appropriate template
3. Verify output quality in PowerPoint and LibreOffice Impress
4. Add entry to this README with usage instructions
5. Submit pull request with example file and README updates

**Example File Naming Convention**: `NN-descriptive-name.txt` where NN is next available number (01, 02, 03, etc.)

---

## License

Examples in this directory are provided under the same license as the main project. See [`../LICENSE`](../LICENSE) for details.

---

**Last Updated**: 2026-04-05
**Maintained By**: AI PowerPoint Generator Project Team
