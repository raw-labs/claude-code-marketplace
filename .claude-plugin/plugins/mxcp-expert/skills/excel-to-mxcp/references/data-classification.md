# Data Classification Guide

Detailed criteria for classifying Excel data as structured, unstructured, or semi-structured.

## Table of Contents

- [Structured Data](#structured-data)
- [Unstructured Data](#unstructured-data)
- [Semi-structured Data](#semi-structured-data)
- [Detection Algorithm](#detection-algorithm)
- [Handling Merged Cells](#handling-merged-cells)
- [RAG-Friendly txt Format](#rag-friendly-txt-format)

## Structured Data

**Indicators:**
- Regular grid pattern (consistent rows/columns)
- Clear header row with column names
- Typed data (numbers, dates, short text)
- Few or no merged cells
- Consistent data in each column

**Examples:**
- Customer lists
- Transaction records
- Inventory tables
- Time series data

**Destination:** dbt Python model → DuckDB table

## Unstructured Data

**Indicators:**
- Long text blocks (>200 chars average)
- Narrative content (paragraphs, sentences)
- No clear columnar structure
- Notes, descriptions, comments
- Free-form text

**Examples:**
- Meeting notes
- Product descriptions
- Email content
- Document text pasted into Excel

**Destination:** txt files for RAG

**Chunking approach:**
1. Identify section breaks (blank rows, headers, formatting changes)
2. Keep paragraphs together
3. Add context header to each chunk
4. Target 500-1000 words per chunk

## Semi-structured Data

**Indicators:**
- Mix of tables and text
- Tables with embedded notes
- Irregular layouts with identifiable patterns
- Form-like structure (labels + values)
- Multiple sub-tables in one sheet

**Examples:**
- Reports with summary + detail tables
- Forms with filled data
- Dashboards exported to Excel
- Mixed data and notes

**Destination:** Hybrid
- Extract tabular portions → DuckDB
- Extract narrative portions → txt
- Link via identifiers

## Detection Algorithm

```python
def classify_data(df, ws):
    """
    Classify sheet data.

    Args:
        df: pandas DataFrame of sheet data
        ws: openpyxl worksheet for formatting info

    Returns:
        'structured' | 'unstructured' | 'semi-structured'
    """
    merged_ratio = len(ws.merged_cells.ranges) / max(ws.max_row * ws.max_column, 1)

    # Calculate text statistics
    text_cols = df.select_dtypes(include=['object'])
    if text_cols.empty:
        return 'structured'  # All numeric

    avg_text_len = text_cols.astype(str).apply(lambda x: x.str.len().mean()).mean()
    max_text_len = text_cols.astype(str).apply(lambda x: x.str.len().max()).max()

    # Check for paragraph-like text
    has_paragraphs = max_text_len > 500

    # Check for consistent structure
    null_ratio = df.isnull().sum().sum() / (df.shape[0] * df.shape[1])

    # Classification logic
    if has_paragraphs and avg_text_len > 200:
        return 'unstructured'

    if merged_ratio > 0.1 or (has_paragraphs and avg_text_len < 200):
        return 'semi-structured'

    if null_ratio < 0.3 and avg_text_len < 100:
        return 'structured'

    return 'semi-structured'  # Default to hybrid
```

## Handling Merged Cells

Merged cells often indicate:

| Pattern | Meaning | Action |
|---------|---------|--------|
| Header spanning columns | Group header | Extract as category |
| Row spanning | Repeated value | Fill down |
| Large merged area | Title/notes | Extract as text |
| Irregular merges | Complex layout | Use vision analysis |

## RAG-Friendly txt Format

```
=== SOURCE METADATA ===
File: quarterly_report.xlsx
Sheet: Executive Summary
Section: Q4 Performance
Row Range: 5-25
Generated: 2024-01-15T10:30:00Z

=== CONTEXT ===
Related Table: quarterly_metrics
Related ID: Q4_2024
Previous Section: Q3 Performance

=== CONTENT ===
[Extracted text content here]

=== KEYWORDS ===
quarterly, performance, revenue, growth, Q4, 2024
```

This format enables:
- Source attribution in RAG results
- Linking to structured data
- Keyword extraction for search
- Section-level granularity
