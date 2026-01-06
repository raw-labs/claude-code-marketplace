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
├── customer_data/
│   ├── chunk_001.txt
│   └── chunk_002.txt
└── manifest.json
```

## When to Use Full vs Simple Format

| Scenario | Format | manifest.json |
|----------|--------|---------------|
| RAG with DB cross-references | Full (with sections) | Required |
| RAG-only, no DB | Simple (content only) | Optional |
| Generated from DB | Simple (content only) | Optional |

**Simple format:** Just the content as plain text. Use when no DB linkage needed.

**Full format:** Use structured sections (below) when bidirectional RAG-DB links are needed.

## RAG txt File Structure (Full Format)

Every RAG chunk file must have these sections:

```
=== SOURCE METADATA ===
File: sales_report.docx
Section: Customer Analysis
Page: 15-17

=== DATABASE LINKS ===
Table: customers
IDs: [101, 102]
Link Type: describes

=== CONTENT ===
[The actual text content here - can be multiple paragraphs.
This is what gets embedded and retrieved for RAG queries.]

=== KEYWORDS ===
customer analysis, sales performance, Q4 review
```

### Section Details

| Section | Purpose | Required |
|---------|---------|----------|
| SOURCE METADATA | Track origin for debugging | Yes |
| DATABASE LINKS | Enable bidirectional RAG-DB links | Yes (use "none" if no links) |
| CONTENT | The actual retrievable content | Yes |
| KEYWORDS | Aid retrieval and categorization | Yes |

### Link Types

Use these values in the "Link Type" field:

- `describes` - Text explains/describes the entity
- `summarizes` - Text aggregates data from entities
- `references` - Text mentions but doesn't describe
- `contextualizes` - Text provides background
- `none` - No database link

### Example: Chunk with No Database Links

```
=== SOURCE METADATA ===
File: annual_report.docx
Section: Market Overview
Page: 5-7

=== DATABASE LINKS ===
Table: none
IDs: []
Link Type: none

=== CONTENT ===
The market saw significant growth in Q4 2024, driven by
increased consumer spending and favorable economic conditions.
Key trends include...

=== KEYWORDS ===
market overview, Q4 2024, consumer spending, economic trends
```

### Example: Chunk Linked to Multiple Entities

```
=== SOURCE METADATA ===
File: customer_analysis.docx
Section: Top Performers
Page: 12

=== DATABASE LINKS ===
Table: customers
IDs: [101, 102, 103]
Link Type: summarizes

=== CONTENT ===
Our top three customers accounted for 45% of total revenue.
Customer 101 (Acme Corp) led with $500K in purchases...

=== KEYWORDS ===
top customers, revenue analysis, Acme Corp, customer performance
```

---

## manifest.json Structure

The manifest tracks all RAG chunks and enables reverse lookups from database to RAG.

```json
{
  "version": "1.0",
  "created_at": "2024-01-15T10:30:00Z",
  "chunks": {
    "sales_report/chunk_001": {
      "file": "sales_report/chunk_001.txt",
      "source": "sales_report.docx",
      "section": "Executive Summary",
      "page": "1-2",
      "linked_table": null,
      "linked_ids": [],
      "link_type": "none",
      "keywords": ["executive summary", "overview"]
    },
    "sales_report/chunk_002": {
      "file": "sales_report/chunk_002.txt",
      "source": "sales_report.docx",
      "section": "Customer Analysis",
      "page": "15-17",
      "linked_table": "customers",
      "linked_ids": [101, 102],
      "link_type": "describes",
      "keywords": ["customer analysis", "sales performance"]
    },
    "sales_report/chunk_003": {
      "file": "sales_report/chunk_003.txt",
      "source": "sales_report.docx",
      "section": "Customer Analysis",
      "page": "18-20",
      "linked_table": "customers",
      "linked_ids": [101],
      "link_type": "describes",
      "keywords": ["customer 101", "detailed analysis"]
    }
  },
  "db_to_rag_index": {
    "customers.101": ["sales_report/chunk_002", "sales_report/chunk_003"],
    "customers.102": ["sales_report/chunk_002"]
  }
}
```

### Key Fields

| Field | Purpose |
|-------|---------|
| `chunks` | Map of chunk_id → metadata |
| `db_to_rag_index` | Reverse lookup: `{table}.{id}` → list of chunk IDs |
| `linked_table` | Database table this chunk relates to |
| `linked_ids` | Specific record IDs referenced |
| `link_type` | Relationship type (describes, summarizes, etc.) |

### Updating manifest.json

When creating RAG chunks:

```python
import json
import os

manifest_path = 'rag_content/manifest.json'

# Load or create manifest
if os.path.exists(manifest_path):
    with open(manifest_path) as f:
        manifest = json.load(f)
else:
    manifest = {"version": "1.0", "chunks": {}, "db_to_rag_index": {}}

# Add new chunk (with nested folder)
source_name = "report"
chunk_id = f"{source_name}/chunk_004"
manifest["chunks"][chunk_id] = {
    "file": f"{chunk_id}.txt",
    "source": "report.docx",
    "section": "Analysis",
    "linked_table": "orders",
    "linked_ids": [201, 202],
    "link_type": "summarizes"
}

# Update reverse index
for entity_id in [201, 202]:
    key = f"orders.{entity_id}"
    if key not in manifest["db_to_rag_index"]:
        manifest["db_to_rag_index"][key] = []
    manifest["db_to_rag_index"][key].append(chunk_id)

# Save manifest
with open(manifest_path, 'w') as f:
    json.dump(manifest, f, indent=2)
```

