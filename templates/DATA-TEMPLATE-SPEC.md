# Data Template Specification

## Purpose

This specification defines requirements for `data-template.pptx` - a PowerPoint template with layouts optimized for charts and tables.

## Task Reference

**T062 [US4]**: Create sample template with chart and table layouts in templates/data-template.pptx

## Required Layouts

### 1. Chart Layout

- **Name**: "Chart" or "Chart Slide"
- **Placeholders**:
  - Title (TITLE type)
  - Chart area (OBJECT or CHART type) - for inserting charts
  - Optional: Subtitle or notes area

### 2. Table Layout

- **Name**: "Table" or "Table Slide"
- **Placeholders**:
  - Title (TITLE type)
  - Table area (TABLE or OBJECT type) - for inserting tables
  - Optional: Notes or context text area

### 3. Chart and Table Layout

- **Name**: "Data Analysis" or "Chart and Table"
- **Placeholders**:
  - Title (TITLE type)
  - Chart area (OBJECT/CHART type)
  - Table area (TABLE/OBJECT type)
  - Optional: Notes area

### 4. Two-Column Data Layout

- **Name**: "Two Column Data"
- **Placeholders**:
  - Title (TITLE type)
  - Left column: Chart or table
  - Right column: Chart or table

## Supported Chart Types

As per FR-025 and SUPPORTED_CHART_TYPES constant:

- Bar
- Column
- Line
- Pie
- Scatter
- Doughnut
- Area
- Radar

## Table Constraints

As per FR-026 and validation constants:

- Maximum rows: 20
- Maximum columns: 10

## Creation Instructions

### Using Microsoft PowerPoint

1. Open PowerPoint
2. Create a new blank presentation
3. Go to View > Slide Master
4. Create custom layouts with the placeholders described above
5. For chart areas: Insert > Chart placeholder
6. For table areas: Insert > Table placeholder
7. Apply consistent styling and color scheme
8. Save as templates/data-template.pptx

### Using LibreOffice Impress

1. Open Impress
2. Create new presentation
3. Go to View > Master Slide
4. Create custom layouts with appropriate object frames
5. Save as templates/data-template.pptx

## Testing

Once created, the template should:

- Be parseable by template_parser
- Support chart insertion via chart_builder
- Support table insertion via table_builder
- Work with content_validator constraints

## Notes

- For now, existing templates (basic-template.pptx, japanese-template.pptx) can be used if they have OBJECT placeholders
- The chart_builder and table_builder work with any template that has appropriate placeholder types
- This template is specifically optimized for data visualization use cases
