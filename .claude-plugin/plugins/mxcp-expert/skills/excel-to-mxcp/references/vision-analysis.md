# Vision Analysis Reference

## When to Use Vision Analysis

Use when sheet structure is ambiguous:
- Merged cells > 10% of used range
- Irregular row heights detected
- Multiple blank rows/columns interspersed
- Complex nested structures
- pandas read_excel produces mostly NaN

## Workflow

### Step 1: Render Excel to HTML

Use openpyxl to convert sheet to HTML preserving visual structure:

```python
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

def excel_to_html(filepath, sheet_name):
    """Convert Excel sheet to HTML preserving visual structure."""
    wb = load_workbook(filepath)
    ws = wb[sheet_name] if sheet_name else wb.active

    html = ['<html><head><style>']
    html.append('''
        table { border-collapse: collapse; font-family: Arial; font-size: 12px; }
        td, th { border: 1px solid #ccc; padding: 4px 8px; min-width: 60px; }
        .merged { background-color: #f0f0f0; }
        .header { background-color: #4472C4; color: white; font-weight: bold; }
    ''')
    html.append('</style></head><body><table>')

    # Track merged cells
    merged_ranges = {}
    for merge in ws.merged_cells.ranges:
        for row in range(merge.min_row, merge.max_row + 1):
            for col in range(merge.min_col, merge.max_col + 1):
                if row == merge.min_row and col == merge.min_col:
                    merged_ranges[(row, col)] = {
                        'rowspan': merge.max_row - merge.min_row + 1,
                        'colspan': merge.max_col - merge.min_col + 1
                    }
                else:
                    merged_ranges[(row, col)] = None

    # Render rows (limit to 100 for vision)
    for row_idx, row in enumerate(ws.iter_rows(max_row=min(ws.max_row, 100)), 1):
        html.append('<tr>')
        for col_idx, cell in enumerate(row, 1):
            merge_info = merged_ranges.get((row_idx, col_idx), {})
            if merge_info is None:
                continue

            attrs = []
            if merge_info.get('rowspan', 1) > 1:
                attrs.append(f"rowspan='{merge_info['rowspan']}'")
            if merge_info.get('colspan', 1) > 1:
                attrs.append(f"colspan='{merge_info['colspan']}'")

            value = cell.value if cell.value is not None else ''
            html.append(f"<td {' '.join(attrs)}>{value}</td>")
        html.append('</tr>')

    html.append('</table></body></html>')
    return '\n'.join(html)
```

### Step 2: Screenshot with Playwright

```python
from playwright.sync_api import sync_playwright

def html_to_screenshot(html_content, output_path):
    """Render HTML to image using Playwright."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_content)
        page.wait_for_load_state('networkidle')

        table = page.locator('table')
        box = table.bounding_box()
        if box:
            page.screenshot(path=output_path, clip={
                'x': max(0, box['x'] - 10),
                'y': max(0, box['y'] - 10),
                'width': min(box['width'] + 20, 1920),
                'height': min(box['height'] + 20, 1080)
            })
        else:
            page.screenshot(path=output_path, full_page=True)

        browser.close()
```

### Step 3: Analyze with Vision

Use vision prompt to understand structure:

```
Analyze this Excel sheet image:
1. What is the overall structure? (table, form, report, notes)
2. Identify distinct sections and their types
3. For tabular sections: identify headers and data ranges
4. For text sections: identify section boundaries
5. Note any merged cells and their purpose
```

### Step 4: Apply Structure to Extraction

Use vision output to guide pandas extraction with specific row/column ranges.

## Merged Cell Patterns

| Pattern | Meaning | Action |
|---------|---------|--------|
| Header spanning columns | Group header | Extract as category |
| Row spanning | Repeated value | Fill down |
| Large merged area | Title/notes | Extract as text |
| Irregular merges | Complex layout | Use vision analysis |

## Threshold Calculation

```python
def needs_vision_analysis(ws):
    """Determine if sheet needs vision analysis."""
    total_cells = ws.max_row * ws.max_column
    if total_cells == 0:
        return False

    merged_cell_count = sum(
        (m.max_row - m.min_row + 1) * (m.max_col - m.min_col + 1)
        for m in ws.merged_cells.ranges
    )

    merged_ratio = merged_cell_count / total_cells
    return merged_ratio > 0.10  # 10% threshold
```
