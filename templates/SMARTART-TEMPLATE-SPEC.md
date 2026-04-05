# SmartArt Template Specification

## Purpose

This specification defines requirements for `smartart-template.pptx` - a PowerPoint template with layouts containing pre-configured SmartArt diagrams for process flows, hierarchies, and cycles.

## Task Reference

**T070 [US5]**: Create sample template with SmartArt layouts in templates/smartart-template.pptx

## Required Layouts

### 1. Process Flow Layout

- **Name**: "Process Flow" or "Process SmartArt"
- **Placeholders**:
  - Title (TITLE type)
  - SmartArt diagram (OBJECT type) - pre-configured with Process SmartArt
- **SmartArt Configuration**:
  - Type: Process (e.g., Basic Process, Step-Up Process, Vertical Process)
  - Nodes: 3-5 nodes recommended (can be populated dynamically)
  - Layout: Horizontal or vertical flow

### 2. Hierarchy Layout

- **Name**: "Hierarchy" or "Organization Chart"
- **Placeholders**:
  - Title (TITLE type)
  - SmartArt diagram (OBJECT type) - pre-configured with Hierarchy SmartArt
- **SmartArt Configuration**:
  - Type: Hierarchy (e.g., Organization Chart, Hierarchy List)
  - Nodes: 3-7 nodes recommended
  - Layout: Top-down hierarchy with multiple levels

### 3. Cycle Layout

- **Name**: "Cycle" or "Cycle Diagram"
- **Placeholders**:
  - Title (TITLE type)
  - SmartArt diagram (OBJECT type) - pre-configured with Cycle SmartArt
- **SmartArt Configuration**:
  - Type: Cycle (e.g., Basic Cycle, Block Cycle)
  - Nodes: 3-6 nodes recommended
  - Layout: Circular or cyclical arrangement

### 4. Relationship Layout

- **Name**: "Relationship" or "Relationship Diagram"
- **Placeholders**:
  - Title (TITLE type)
  - SmartArt diagram (OBJECT type) - pre-configured with Relationship SmartArt
- **SmartArt Configuration**:
  - Type: Relationship (e.g., Basic Venn, Grouped List)
  - Nodes: 2-4 nodes recommended
  - Layout: Interconnected elements

### 5. Two-Column SmartArt Layout

- **Name**: "Two Column SmartArt"
- **Placeholders**:
  - Title (TITLE type)
  - Left column: SmartArt diagram (OBJECT type)
  - Right column: Text content (TEXT type) or another SmartArt
- **Purpose**: Combine SmartArt visualization with explanatory text

## Supported SmartArt Types

As per User Story 5 and SmartArtBlock schema:

- **Process**: Sequential steps, workflows, timelines
- **Hierarchy**: Organization charts, decision trees, taxonomies
- **Cycle**: Continuous processes, feedback loops
- **Relationship**: Comparisons, connections, groupings

## SmartArt Node Structure

Each SmartArt node in the specification should support:

```json
{
  "text": "Node text content",
  "level": 0 // Hierarchy level (0 = top level, 1 = child, etc.)
}
```

## Creation Instructions

### Using Microsoft PowerPoint

1. Open PowerPoint
2. Create a new blank presentation
3. Go to View > Slide Master
4. Create custom layouts with the names described above
5. For each layout:
   - Insert > SmartArt
   - Choose the appropriate SmartArt type
   - Configure with placeholder text (e.g., "Node 1", "Node 2", etc.)
   - The system will replace this text with generated content
6. Apply consistent styling and color scheme
7. Exit Slide Master view
8. Save as `templates/smartart-template.pptx`

### Using LibreOffice Impress

**Note**: LibreOffice Impress has limited SmartArt support. For best results:

1. Create the template in PowerPoint first
2. Or use basic shapes arranged in diagram patterns as alternatives
3. Save as templates/smartart-template.pptx

### Important Considerations

- **Pre-configured SmartArt**: The SmartArt diagrams must already exist in the template layouts
- **Node Count**: The template_parser will detect the number of nodes in each SmartArt
- **XML Manipulation**: The system manipulates SmartArt via XML (see smartart_builder.py)
- **Placeholder Names**: Use clear, descriptive names like "SmartArt Placeholder" or "Content Placeholder"

## Testing

Once created, the template should:

1. Be parseable by template_parser
2. Have SmartArt-containing layouts detected correctly
3. Support SmartArt node count extraction via manifest_builder
4. Allow SmartArt population via smartart_builder
5. Work with content_validator SmartArt constraints

### Test Command

```bash
# Parse the template to verify SmartArt detection
uv run python -c "
from pptx_agent.template_parser import TemplateParser
parser = TemplateParser('templates/smartart-template.pptx')
manifest = parser.parse()
print('SmartArt layouts found:', [layout.name for layout in manifest.layouts if layout.has_smartart])
"
```

## SmartArt Constraints

As per FR-034 and validation:

- SmartArt node counts must match template structure
- Text content must fit within SmartArt node text boxes
- Maximum node text length: Varies by SmartArt type (typically 50-100 characters per node)

## Known Limitations

From spec.md assumptions and risks:

1. **Template-First Architecture**: SmartArt must be pre-configured in templates
2. **XML Complexity**: Advanced SmartArt features may not be supported
3. **Commercial Library Option**: If XML manipulation proves unstable, commercial libraries may be considered

## Notes

- For MVP testing, existing templates (basic-template.pptx) may be used if they have OBJECT placeholders
- The smartart_builder currently raises NotImplementedError as acknowledged in the spec
- This template is specifically designed for testing SmartArt population workflows
- Full SmartArt XML manipulation may require additional development or commercial libraries

## Alternative: Fallback Template

If full SmartArt template creation is not immediately feasible:

1. Use `basic-template.pptx` with OBJECT placeholders
2. Mock SmartArt structures in tests
3. Document the template requirement for future implementation

## References

- **Spec**: specs/001-ai-pptx-generator/spec.md - User Story 5
- **Schema**: src/pptx_agent/schemas/visual_assets.py - SmartArtBlock
- **Builder**: src/pptx_agent/pptx_wrapper/smartart_builder.py
- **Tests**: tests/unit/pptx_wrapper/test_slide_builder_smartart.py
