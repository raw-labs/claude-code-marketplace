# RAG Content Format

## File Structure

**One source file = one RAG file.** Simple, clean mapping.

```
rag_content/
├── sales_report.txt
├── employee_handbook.txt
└── compliance_policy.txt
```

## File Requirements

- **Extension:** `.txt` only
- **Location:** `rag_content/{source_name}.txt`
- **Naming:** Match source filename (sanitized)

## Document Format

Structure content with sections and paragraphs for clean retrieval:

```
## Section Title

Paragraph content here. Multiple sentences grouped logically.

Another paragraph in the same section.

## Next Section

Content continues with clear separation between topics.
```

### Format Rules

1. **Section headers:** `## Title` (two hashes + space)
2. **Paragraphs:** Separated by blank lines
3. **No markdown beyond headers:** Plain text content
4. **Preserve hierarchy:** Main sections, subsections if needed

### Example: Document with Numbered Sections

```
## 1. Introduction

This document outlines the compliance requirements for all employees.

## 1.1 Scope

These policies apply to all full-time and contract employees.

## 1.2 Effective Date

Policies are effective as of January 1, 2024.

## 2. Data Handling

All customer data must be handled according to privacy regulations.
```

### Example: Product Catalog

```
## Laptop Pro X1

High-performance laptop with 16GB RAM and 512GB SSD.
Ideal for developers and power users.

## Wireless Mouse M200

Ergonomic wireless mouse with 6-month battery life.
Compatible with Windows and macOS.
```

## Creating RAG Files

### From Documents

```python
# scripts/report/extract_rag.py
import os
from docx import Document

source_name = "report"
os.makedirs("rag_content", exist_ok=True)

doc = Document("source_data/report.docx")
sections = []
current = {'title': 'Introduction', 'content': []}

for para in doc.paragraphs:
    if para.style.name.startswith('Heading'):
        if current['content']:
            sections.append(current)
        current = {'title': para.text, 'content': []}
    elif para.text.strip():
        current['content'].append(para.text)

if current['content']:
    sections.append(current)

with open(f"rag_content/{source_name}.txt", "w") as f:
    for s in sections:
        f.write(f"## {s['title']}\n\n")
        f.write("\n\n".join(s['content']))
        f.write("\n\n")
```

### From Database

```python
# models/catalog/generate_rag.py
import os

def model(dbt, session):
    df = dbt.ref("catalog_items").df()
    os.makedirs("rag_content", exist_ok=True)

    with open("rag_content/catalog.txt", "w") as f:
        for _, row in df.iterrows():
            f.write(f"## {row['name']}\n\n{row['description']}\n\n")
    return df
```

## Idempotency

Scripts overwrite the target file completely. Re-running produces identical output.
