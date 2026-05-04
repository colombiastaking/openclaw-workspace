# Professional Document Generation Skill

Generate publication-quality Word documents (.docx) from Markdown with proper styling, embedded images, and professional formatting.

## Overview

This skill converts Markdown method statements (or any structured document) into professional Microsoft Word documents suitable for client delivery.

## Features

1. **Professional Heading Styles** — DEME brand colors (navy blue #1A3A5C, medium blue #2C5282)
2. **Page Numbers** — Custom footer: "PROJECT_CODE | Project Name — Rev XX | Page X of Y"
3. **Professional Tables** — Header row with dark blue background, white text, alternating row colors
4. **Image Embedding** — Preserves images from Markdown with proper sizing
5. **Caption Cleanup** — Removes placeholder text like "REFERENCE FORMAT", "La Rochelle"
6. **A4 Format** — Proper margins (2.5cm all sides)

## Usage

### Basic Command

```bash
python ~/.openclaw/workspace/.agents/skills/professional-docx/generate_professional_docx.py \
  input.md \
  output.docx \
  "PROJECT_CODE" \
  "Project Name" \
  "Rev"
```

### Example

```bash
cd ~/.openclaw/workspace/missions/2026-05-LAGOS-HARBOR-GABON/reports/method-statements

python ~/.openclaw/workspace/.agents/skills/professional-docx/generate_professional_docx.py \
  SNAKE-ISLAND-SURVEY-METHOD-STATEMENT-v08.md \
  SNAKE-ISLAND-SURVEY-METHOD-STATEMENT-v08.docx \
  "SGS/NEF/2026/SUR-MS-001" \
  "Snake Island Container Terminal" \
  "08"
```

### Python API

```python
from generate_professional_docx import generate_professional_docx

generate_professional_docx(
    input_md="input.md",
    output_docx="output.docx",
    project_code="SGS/NEF/2026/SUR-MS-001",
    project_name="Snake Island Container Terminal",
    rev="08"
)
```

## Style Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| Brand Primary | #1A3A5C | Dark navy — Heading 1 |
| Brand Secondary | #2C5282 | Medium blue — Heading 2/3 |
| Body Font | Calibri | 11pt, dark gray |
| Heading 1 | Calibri | 18pt, bold, all caps |
| Heading 2 | Calibri | 14pt, bold |
| Heading 3 | Calibri | 12pt, bold |
| Table Header | #1A3A5C | White text, 10pt |
| Table Body | 9.5pt | Alternating #F5F7FA/white |
| Page Size | A4 | 21.0 × 29.7 cm |
| Margins | 2.5 cm | All sides |

## Dependencies

```bash
pip install python-docx
```

System requirements:
- `pandoc` (for markdown → docx conversion)
- `python3` (3.8+)

## File Structure

```
.agents/skills/professional-docx/
├── SKILL.md                          # This file
├── generate_professional_docx.py    # Main script
└── download_equipment_specs.py      # Download official PDF specs
```

## Caption Cleanup

The script automatically cleans these placeholder patterns:
- `(REFERENCE FORMAT — ...)` → removed
- `(Reference format — ...)` → removed
- `(to be inserted)` → removed
- `(to be photographed ...)` → removed
- `La Rochelle SDI 20MP093` references → updated

## Table of Contents

Pandoc generates TOC automatically with `--toc --toc-depth=3`.

## Image Handling

Images referenced in Markdown like:
```markdown
![Caption](path/to/image.png)
```

Are preserved in the Word document. Ensure images are in the correct relative path.

## Equipment Spec Images

For survey method statements, equipment specification images should be placed in:
```
reports/method-statements/images/equipment-specs/
```

With descriptive names:
- `spec-22-em2040c.png` — Kongsberg EM2040C
- `spec-23-octans.png` — Exail Octans V
- `cal-10-patch-roll.png` — Roll calibration diagram
- `fig-15-rtk-system.png` — RTK system diagram

## Output Example

```
📄 Pandoc conversion complete
🎨 Applying professional styling...
✅ Professional document saved: output.docx

📊 Document Statistics:
   Paragraphs: 577
   Tables: 85
   File size: 6.6 MB
```

## Troubleshooting

### Images not showing
- Ensure image paths are correct relative to markdown file
- Check images exist before running script
- Use absolute paths if relative paths fail

### Tables not styled
- Tables must use standard Markdown pipe syntax
- Header separator line required: `|:--|`

### Page numbers not working
- Open document in Word and press Ctrl+A then F9 to update fields
- Or right-click footer → Update Field

## Author

Alice — AI Assistant for Colombia Staking
Updated: 2026-05-04
