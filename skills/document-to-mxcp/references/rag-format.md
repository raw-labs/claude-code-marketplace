# RAG Content Format

## File Requirements

- **Extension:** `.txt` only (never `.md`)
- **Location:** `rag_content/{source_name}/*.txt` (nested by source file)
- **Content:** Plain text, no markdown formatting
- **Whitespace:** Trim leading/trailing spaces, no excessive blank lines

Example structure:
```
rag_content/
├── sales_report/
│   ├── chunk_001.txt
│   └── chunk_002.txt
└── customer_data/
    ├── chunk_001.txt
    └── chunk_002.txt
```

## RAG Chunk Format

RAG chunks are plain text files containing the content to be embedded and retrieved.

### Simple Format (Recommended)

Just the content as plain text:

```
The market saw significant growth in Q4 2024, driven by
increased consumer spending and favorable economic conditions.
Key trends include digital transformation and sustainability initiatives.
```

Use simple format for:
- Content generated from database tables
- Standalone text that doesn't need source tracking
- Most ingestion scenarios

### With Source Metadata (Optional)

Add source tracking when debugging origin is important:

```
=== SOURCE ===
File: annual_report.docx
Section: Market Overview
Page: 5-7

=== CONTENT ===
The market saw significant growth in Q4 2024, driven by
increased consumer spending and favorable economic conditions.
Key trends include digital transformation and sustainability initiatives.
```

## Chunk Size Guidelines

| Content Type | Chunk Size | Rationale |
|--------------|------------|-----------|
| Individual records, FAQ, definitions | **Small** (1-3 paragraphs) | Self-contained, precise retrieval |
| Topic sections, analysis with context | **Medium** (full section) | Context needed for meaning |
| Narrative reports, policies, legal text | **Large** (multi-section) | Flowing argument, don't split |

**Rules:**
- Never split mid-sentence or mid-paragraph
- Never separate a table from its description
- Include enough context for the chunk to be understandable standalone

## Creating RAG Chunks

### From Documents (RAG-only)

```python
# scripts/annual_report/extract_rag.py
import os
import shutil
from docx import Document

source_name = "annual_report"
shutil.rmtree(f"rag_content/{source_name}", ignore_errors=True)
os.makedirs(f"rag_content/{source_name}")

doc = Document("source_data/annual_report.docx")
for idx, para in enumerate(doc.paragraphs):
    if para.text.strip():
        with open(f"rag_content/{source_name}/chunk_{idx:03d}.txt", "w") as f:
            f.write(para.text)
```

### From Database (DB + RAG)

```python
# models/product_catalog/generate_rag.py
import os
import shutil

def model(dbt, session):
    df = dbt.ref("product_catalog_items").df()
    source_name = "product_catalog"

    shutil.rmtree(f"rag_content/{source_name}", ignore_errors=True)
    os.makedirs(f"rag_content/{source_name}")

    for idx, row in df.iterrows():
        content = f"{row['name']}: {row['description']}"
        with open(f"rag_content/{source_name}/chunk_{idx:03d}.txt", "w") as f:
            f.write(content)

    return df
```

## Idempotency

RAG extraction scripts should be idempotent:
1. Clear the target folder before writing
2. Regenerate all chunks from source
3. Re-running produces identical results

This ensures the RAG content stays in sync with source files or database.
