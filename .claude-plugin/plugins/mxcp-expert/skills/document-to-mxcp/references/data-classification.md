# Data Classification Guide

## Table of Contents
- [Structured Data](#structured-data)
- [Unstructured Data](#unstructured-data)
- [Semi-structured Data](#semi-structured-data)
- [Classification Algorithm](#classification-algorithm)
- [Document Patterns](#merged-cell-patterns-excel)

## Structured Data

**Indicators:**
- Regular grid/table pattern
- Clear header row with column names
- Typed data (numbers, dates, short text <100 chars)
- Consistent data in each column

**Sources:**
- Excel sheets with tabular data
- Word document tables with typed data
- CSV files

**Destination:** dbt Python model → DuckDB table

## Unstructured Data

**Indicators:**
- Long text blocks (>200 chars average)
- Narrative content (paragraphs, sentences)
- No clear columnar structure

**Sources:**
- Excel sheets with notes/descriptions
- Word document paragraphs
- Text-heavy sections

**Destination:** txt files for RAG

**Chunking:**
1. Identify section breaks (headings, blank lines)
2. Keep paragraphs together
3. Add context header + DB links to each chunk
4. Target 500-1000 words per chunk

## Semi-structured Data

**Indicators:**
- Mix of tables and text
- Tables with long text cells
- Form-like structure

**Sources:**
- Word documents with embedded tables + narrative
- Excel with mixed data/notes columns

**Destination:** Hybrid - tables → DuckDB, text → RAG, with bidirectional links

## Classification Algorithm

### For Excel Sheets
```python
def classify_sheet(df, ws):
    merged_ratio = len(ws.merged_cells.ranges) / max(ws.max_row * ws.max_column, 1)
    text_cols = df.select_dtypes(include=['object'])

    if text_cols.empty:
        return 'structured'

    avg_text_len = text_cols.astype(str).apply(lambda x: x.str.len().mean()).mean()
    max_text_len = text_cols.astype(str).apply(lambda x: x.str.len().max()).max()

    if max_text_len > 500 and avg_text_len > 200:
        return 'unstructured'
    if merged_ratio > 0.1 or (max_text_len > 500 and avg_text_len < 200):
        return 'semi-structured'
    if avg_text_len < 100:
        return 'structured'
    return 'semi-structured'
```

### For Word Content Blocks
```python
def classify_word_block(block):
    if block['type'] == 'table':
        # Check if table has mostly short text
        all_text = ' '.join([cell for row in block['data'] for cell in row])
        avg_cell_len = len(all_text) / max(block['row_count'] * block['col_count'], 1)

        if avg_cell_len < 100:
            return 'structured'
        elif avg_cell_len > 300:
            return 'unstructured'  # Table used for layout, not data
        else:
            return 'semi-structured'

    elif block['type'] == 'paragraph':
        if len(block['text']) > 200:
            return 'unstructured'
        elif block['style'].startswith('Heading'):
            return 'metadata'  # Use as section context
        else:
            return 'unstructured'
```

## Merged Cell Patterns (Excel)

| Pattern | Meaning | Action |
|---------|---------|--------|
| Header spanning columns | Group header | Extract as category |
| Row spanning | Repeated value | Fill down |
| Large merged area | Title/notes | Extract as text for RAG |

## Word Document Patterns

| Pattern | Classification | Action |
|---------|---------------|--------|
| Table with numbers/dates | Structured | Extract to DuckDB |
| Table with paragraphs | Semi-structured | Split columns |
| Heading + paragraphs | Unstructured | Chunk for RAG |
| Bulleted lists | Unstructured | Preserve structure in RAG |
