# Data Classification Guide

## Table of Contents
- [Key Decision: Will Queries Be Needed?](#key-decision)
- [Database Only](#database-only)
- [RAG Only](#rag-only)
- [Both Database and RAG](#both-database-and-rag)
- [Converting Tables to RAG Text](#converting-tables-to-rag-text)
- [Classification Algorithm](#classification-algorithm)
- [Document Patterns](#merged-cell-patterns-excel)

## Key Decision

**The question is NOT "is this tabular?" but "will queries be needed on this data?"**

Tabular data with descriptive text columns is often better suited for RAG (semantic search) than for database queries. Only put data in the database if aggregations, filtering, or lookups will be performed.

## Database Only

**When to use:** Data will be queried (SUM, COUNT, GROUP BY, filtering, lookups)

**Indicators:**
- Numeric columns for aggregation (amounts, counts, scores)
- Date columns for time-based queries
- ID columns for lookups and joins
- Categorical columns for filtering

**Examples:**
- Sales transactions (query: "total sales by month")
- Inventory levels (query: "items below threshold")
- Customer IDs with metrics (query: "top 10 customers by revenue")

**Destination:** dbt Python model → DuckDB table

## RAG Only

**When to use:** Data is for semantic search/context retrieval, not queries

**Indicators:**
- Descriptive text columns (notes, analysis, comments)
- Narrative content explaining entities
- Context that helps answer "tell me about X" questions

**Examples:**
- Customer notes ("High-value partner, expanded in Q3")
- Product descriptions
- Meeting summaries
- Analysis paragraphs

**Destination:** txt files for RAG (convert tables to narrative text)

**Chunking:** See SKILL.md "Unstructured Data → RAG txt" section for chunk sizing.

## Both Database and RAG

**When to use:** Data needs BOTH queries AND semantic search

**Indicators:**
- Numeric data for aggregation PLUS descriptive text for context
- Users will ask "what are total sales?" AND "tell me about this customer"

**Examples:**
- Customer table with revenue (queryable) AND notes (searchable)
- Project list with budgets (queryable) AND descriptions (searchable)

**Destination:**
1. Numeric/queryable columns → DuckDB table
2. Descriptive columns → RAG text files (generated from DB)

## Converting Tables to RAG Text

When tabular data has text columns better suited for RAG, convert rows to narrative format:

**Original table:**
| ID | Name | Description |
|----|------|-------------|
| 101 | Acme Corp | High-value partner, expanded operations in Q3. Key contact: John Smith. |
| 102 | Beta Inc | New customer, pilot program started. Interested in enterprise tier. |

**Converted to RAG text:**
```
Customer 101 (Acme Corp): High-value partner, expanded operations in Q3. Key contact: John Smith.

Customer 102 (Beta Inc): New customer, pilot program started. Interested in enterprise tier.
```

**Conversion guidelines:**
- Include ID/name for reference
- Preserve the descriptive content
- One entity per paragraph or grouped logically
- Add section context if relevant

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
