# Data Classification Guide

## Structured Data

**Indicators:**
- Regular grid pattern (consistent rows/columns)
- Clear header row with column names
- Typed data (numbers, dates, short text <100 chars)
- Few or no merged cells
- Consistent data in each column

**Examples:** Customer lists, transaction records, inventory tables, time series

**Destination:** dbt Python model → DuckDB table

## Unstructured Data

**Indicators:**
- Long text blocks (>200 chars average)
- Narrative content (paragraphs, sentences)
- No clear columnar structure
- Notes, descriptions, comments

**Examples:** Meeting notes, product descriptions, email content, documentation

**Destination:** txt files for RAG

**Chunking:**
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

**Examples:** Reports with summary + detail, forms, dashboards, mixed data/notes

**Destination:** Hybrid - extract tables → DuckDB, extract text → RAG

## Classification Algorithm

```python
def classify_sheet(df, ws):
    """
    Returns: 'structured' | 'unstructured' | 'semi-structured'
    """
    merged_ratio = len(ws.merged_cells.ranges) / max(ws.max_row * ws.max_column, 1)

    text_cols = df.select_dtypes(include=['object'])
    if text_cols.empty:
        return 'structured'  # All numeric

    avg_text_len = text_cols.astype(str).apply(lambda x: x.str.len().mean()).mean()
    max_text_len = text_cols.astype(str).apply(lambda x: x.str.len().max()).max()
    has_paragraphs = max_text_len > 500
    null_ratio = df.isnull().sum().sum() / (df.shape[0] * df.shape[1])

    if has_paragraphs and avg_text_len > 200:
        return 'unstructured'

    if merged_ratio > 0.1 or (has_paragraphs and avg_text_len < 200):
        return 'semi-structured'

    if null_ratio < 0.3 and avg_text_len < 100:
        return 'structured'

    return 'semi-structured'
```

## Merged Cell Patterns

| Pattern | Meaning | Action |
|---------|---------|--------|
| Header spanning columns | Group header | Extract as category |
| Row spanning | Repeated value | Fill down |
| Large merged area | Title/notes | Extract as text |
| Irregular merges | Complex layout | Use vision analysis |
