# Extraction Strategy Guide

## Table of Contents
- [Strategy Decision](#strategy-decision)
- [Code-Based Extraction](#code-based-extraction)
- [Complex Content Extraction](#complex-content-extraction)
- [Hybrid Approach](#hybrid-approach)
- [Large Document Workflow](#large-document-workflow)

## Strategy Decision

**Before extracting anything, scan the document to decide extraction strategy per section.**

### Use Code-Based Extraction When:

| Indicator | Example |
|-----------|---------|
| Well-formatted tables | Consistent headers, typed cells |
| Repeating structure | Same table format on multiple pages |
| Proper heading styles | Heading1, Heading2 used consistently |
| Numbered/bulleted lists | Can be parsed programmatically |
| Predictable layout | Report template with known sections |

**Code extraction is faster and more reliable for structured content.**

### Use Complex Extraction When:

| Indicator | Example |
|-----------|---------|
| Inconsistent tables | Merged cells, varying columns |
| Embedded meaning | "See above" references, context-dependent |
| Complex narrative | Meaning requires understanding |
| Visual structure | Layout not reflected in document model |
| Mixed content blocks | Tables interrupted by notes |
| Decision required | "Is this data or just an example?" |

**Complex extraction requires understanding first, but still produces reproducible scripts.**

### Decision Algorithm

```python
def decide_extraction_strategy(content_block):
    """
    Returns: 'simple' | 'complex' | 'skip'
    simple = direct pandas/dbt extraction
    complex = needs preprocessing script, but still reproducible
    """
    if content_block['type'] == 'table':
        table = content_block['data']

        # Check table quality
        has_consistent_columns = len(set(len(row) for row in table)) == 1
        has_merged_indicators = any('merged' in str(cell).lower() for row in table for cell in row)
        has_empty_headers = not table[0] or any(not h.strip() for h in table[0])
        avg_cell_length = sum(len(str(c)) for row in table for c in row) / max(len(table) * len(table[0]), 1)

        if has_consistent_columns and not has_merged_indicators and not has_empty_headers:
            if avg_cell_length < 100:
                return 'code'  # Clean table, extract with code
            else:
                return 'complex'  # Long text cells, need preprocessing
        else:
            return 'complex'  # Messy table, needs preprocessing

    elif content_block['type'] == 'paragraph':
        text = content_block['text']

        if len(text) < 50:
            return 'skip'  # Too short, likely whitespace/header
        elif len(text) > 2000:
            return 'complex'  # Long content, needs chunking logic
        else:
            return 'code'  # Standard paragraph, chunk programmatically

    return 'complex'  # Default to complex for unknown types
```

## Code-Based Extraction

**Use Python code to extract and write data directly.**

### For Tables → DuckDB

```python
from docx import Document
import pandas as pd

doc = Document('large_report.docx')

# Find all well-formatted tables
for i, table in enumerate(doc.tables):
    # Extract to DataFrame
    headers = [cell.text.strip() for cell in table.rows[0].cells]
    data = [[cell.text.strip() for cell in row.cells] for row in table.rows[1:]]
    df = pd.DataFrame(data, columns=headers)

    # Clean column names
    df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('[^a-z0-9_]', '', regex=True)

    # Write directly to DuckDB
    import duckdb
    conn = duckdb.connect('data/db-default.duckdb')
    conn.execute(f"CREATE TABLE IF NOT EXISTS table_{i} AS SELECT * FROM df")
    conn.close()

    print(f"Extracted table {i}: {len(df)} rows")
```

### For Paragraphs → RAG

```python
from docx import Document
import os

doc = Document('large_report.docx')

# Group paragraphs by section
current_section = "Introduction"
chunks = []
current_chunk = []

for para in doc.paragraphs:
    if para.style.name.startswith('Heading'):
        # Save previous chunk
        if current_chunk:
            chunks.append({
                'section': current_section,
                'content': '\n'.join(current_chunk)
            })
        current_section = para.text
        current_chunk = []
    else:
        if para.text.strip():
            current_chunk.append(para.text)

# Write chunks to RAG files (see SKILL.md for full format)
os.makedirs('rag_content', exist_ok=True)
for i, chunk in enumerate(chunks):
    with open(f'rag_content/chunk_{i:03d}.txt', 'w') as f:
        f.write(f"=== SOURCE METADATA ===\n")
        f.write(f"File: large_report.docx\n")
        f.write(f"Section: {chunk['section']}\n\n")
        f.write(f"=== DATABASE LINKS ===\n")
        f.write(f"Table: none\nIDs: []\nLink Type: none\n\n")
        f.write(f"=== CONTENT ===\n")
        f.write(chunk['content'] + "\n\n")
        f.write(f"=== KEYWORDS ===\n")
        f.write(f"[extract keywords from content]\n")
    print(f"Wrote chunk {i}: {chunk['section']}")
```

## Complex Content Extraction

**When content requires understanding before extraction, the agent reads and classifies first, then generates reproducible scripts.**

### Workflow

1. **Read a section** (10-20 pages at a time for large docs)
2. **Classify each element:** DB, RAG, or skip?
3. **Design extraction approach:** What preprocessing is needed?
4. **Generate dbt model or script** that handles the complexity
5. **Verify output** matches source

**Key principle:** Even complex content must result in reproducible scripts (dbt models or Python scripts), not one-time manual writes.

### Example: Complex Document

```
Agent reads pages 1-10:

Page 1-2: Title page and TOC → SKIP
Page 3-5: Executive Summary → RAG
Page 6: Methodology table (merged cells) → DB (needs preprocessing)
Page 7-10: Detailed analysis → RAG

Agent generates:
- models/report/load_methodology.py  # handles merged cells
- scripts/report/extract_rag.py       # extracts summary + analysis
```

### When Agent Should Pause and Think

- **Ambiguous table:** "This table has 'Notes' column with paragraphs - should I split DB/RAG?"
- **Context-dependent:** "References 'see above' - need to resolve before chunking"
- **Quality decision:** "This data looks like an example, not real data - skip?"
- **Incomplete extraction:** "Table continues on next page - merge in preprocessing"

## Hybrid Approach

**Most large documents need both strategies.**

### Recommended Flow for Large Documents

```
1. SCAN (code): Get document structure
   - List all headings
   - Count tables
   - Estimate page count per section

2. CLASSIFY: Review structure, decide per-section strategy
   - Section A: tables look clean → code extraction
   - Section B: complex narrative → complex extraction
   - Section C: appendix data → code extraction

3. EXTRACT (mixed): Execute strategies
   - Run code extraction for A and C
   - Process B with preprocessing script

4. LINK: Review extracted content
   - Identify cross-references
   - Create RAG-DB links

5. VALIDATE (code): Run tests
```

## Large Document Workflow

### For Documents > 50 Pages

**Do NOT try to process entire document at once.**

#### Step 1: Initial Scan
```python
from docx import Document

doc = Document('200_page_report.docx')

# Get structure overview
structure = []
for para in doc.paragraphs:
    if para.style.name.startswith('Heading'):
        structure.append({
            'level': para.style.name,
            'text': para.text[:100]
        })

print(f"Document has {len(doc.paragraphs)} paragraphs, {len(doc.tables)} tables")
print(f"Sections: {len([s for s in structure if s['level'] == 'Heading 1'])}")
```

#### Step 2: Section-by-Section Processing

Process document in logical sections:

```
For each major section:
  1. Read section content
  2. Decide: simple or complex extraction?
  3. Extract content
  4. Write to DB/RAG
  5. Update manifest
  6. Validate extraction
  7. Move to next section
```

#### Step 3: Progress Tracking

Maintain processing state:

```json
{
  "file": "200_page_report.docx",
  "total_sections": 12,
  "processed_sections": [
    {"name": "Introduction", "strategy": "code", "status": "done"},
    {"name": "Methodology", "strategy": "complex", "status": "done"},
    {"name": "Results", "strategy": "code", "status": "in_progress"}
  ],
  "tables_extracted": 15,
  "rag_chunks_created": 23,
  "current_position": "Section 3, page 45"
}
```

#### Step 4: Memory Management

For very large docs, process in chunks to avoid context overflow:

1. Extract section boundaries first
2. Process one section at a time
3. Write results immediately (don't hold in memory)
4. Clear intermediate data before next section

### Resumption After Interruption

If processing is interrupted:

1. Check progress state
2. Resume from last completed section
3. Re-verify last section's output
4. Continue processing
