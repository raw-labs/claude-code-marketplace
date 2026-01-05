# Extraction Strategy Guide

## Table of Contents
- [Strategy Decision](#strategy-decision)
- [Code-Based Extraction](#code-based-extraction)
- [Manual Step-by-Step Extraction](#manual-step-by-step-extraction)
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

### Use Manual Step-by-Step Extraction When:

| Indicator | Example |
|-----------|---------|
| Inconsistent tables | Merged cells, varying columns |
| Embedded meaning | "See above" references, context-dependent |
| Complex narrative | Meaning requires understanding |
| Visual structure | Layout not reflected in document model |
| Mixed content blocks | Tables interrupted by notes |
| Decision required | "Is this data or just an example?" |

**Manual extraction is necessary when understanding is required to classify.**

### Decision Algorithm

```python
def decide_extraction_strategy(content_block):
    """
    Returns: 'code' | 'manual' | 'skip'
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
                return 'manual'  # Long text cells, need to understand
        else:
            return 'manual'  # Messy table, process manually

    elif content_block['type'] == 'paragraph':
        text = content_block['text']

        if len(text) < 50:
            return 'skip'  # Too short, likely whitespace/header
        elif len(text) > 2000:
            return 'manual'  # Long content, need to chunk intelligently
        else:
            return 'code'  # Standard paragraph, chunk programmatically

    return 'manual'  # Default to manual for unknown types
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

# Write chunks to RAG files
os.makedirs('rag_content', exist_ok=True)
for i, chunk in enumerate(chunks):
    with open(f'rag_content/chunk_{i:03d}.txt', 'w') as f:
        f.write(f"=== SOURCE METADATA ===\n")
        f.write(f"Section: {chunk['section']}\n\n")
        f.write(f"=== CONTENT ===\n")
        f.write(chunk['content'])
    print(f"Wrote chunk {i}: {chunk['section']}")
```

## Manual Step-by-Step Extraction

**Agent reads content, understands it, and decides what to extract.**

### Workflow for Manual Extraction

1. **Read a section** (10-20 pages at a time for large docs)
2. **Classify each element:**
   - Is this data that belongs in DB?
   - Is this narrative that belongs in RAG?
   - Is this just formatting/boilerplate to skip?
3. **Extract with understanding:**
   - For tables: understand column meanings, clean data
   - For text: identify key information, create meaningful chunks
4. **Write to destination:**
   - DB: use pandas + duckdb
   - RAG: write txt files with proper metadata
5. **Track progress:** note what pages were processed

### Example Manual Flow

```
Agent reads pages 1-10:

Page 1-2: Title page and TOC → SKIP
Page 3-5: Executive Summary → RAG (summarizes key findings)
Page 6: Methodology table → DB (but has merged cells, need to flatten)
Page 7-10: Detailed analysis → RAG (narrative with entity mentions)

Agent actions:
1. Skip pages 1-2
2. Extract pages 3-5 text → write to rag_content/executive_summary.txt
3. Read page 6 table carefully, understand structure, create clean DataFrame → write to DB
4. Extract pages 7-10, identify entity links → write to rag_content/analysis.txt with DB links
```

### When Agent Should Pause and Think

- **Ambiguous table:** "This table has 'Notes' column with paragraphs - should I split it?"
- **Context-dependent:** "This paragraph says 'as shown above' - need to link to previous content"
- **Quality decision:** "This data looks like an example, not real data - should I skip?"
- **Incomplete extraction:** "Table continues on next page - need to merge"

## Hybrid Approach

**Most large documents need both strategies.**

### Recommended Flow for Large Documents

```
1. SCAN (code): Get document structure
   - List all headings
   - Count tables
   - Estimate page count per section

2. CLASSIFY (manual): Review structure, decide per-section strategy
   - Section A: tables look clean → code extraction
   - Section B: complex narrative → manual extraction
   - Section C: appendix data → code extraction

3. EXTRACT (mixed): Execute strategies
   - Run code extraction for A and C
   - Manually process B

4. LINK (manual): Review extracted content
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
  2. Decide: code or manual extraction?
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
    {"name": "Methodology", "strategy": "manual", "status": "done"},
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
