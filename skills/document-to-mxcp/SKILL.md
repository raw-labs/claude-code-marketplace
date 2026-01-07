---
name: document-to-mxcp
description: "Intelligent single-file document ingestion into MXCP servers. Supports Excel (.xlsx, .xls, .csv) and Word (.docx) files. Analyzes content to determine if queries will be needed (DuckDB) or semantic search (RAG txt), including converting tabular text to narrative format. Creates bidirectional references between RAG content and database entries. Use when: (1) Ingesting a document into an MXCP project, (2) Adding a new data file to an existing MXCP server, (3) Processing documents with mixed tables and text, (4) Preparing data for RAG systems with database linkage."
---

# Document to MXCP Ingestion

## Supported Formats

- **Excel:** .xlsx, .xls, .csv
- **Word:** .docx (for .doc files, convert to .docx first using LibreOffice or similar)

## Required Skills

**Invoke these skills as needed during execution:**

| Skill | When to Use |
|-------|-------------|
| **xlsx** | Reading/analyzing Excel files (.xlsx, .xls, .csv) |
| **docx** | Reading/analyzing Word documents (.docx) |
| **mxcp-expert** | Creating MXCP project, tools, dbt models, validation |

**Always use the appropriate skill** - don't try to implement Excel/Word parsing or MXCP operations from scratch.

## Environment

- **Package manager:** `uv` with virtual environment (never global installs)
- **Required packages:** `mxcp pandas openpyxl python-docx duckdb`
- **Database:** Always use default `data/db-default.duckdb` (auto-created by MXCP)

## Core Principles

1. **Analyze first, ingest second.** Fully understand the file before writing anything.
2. **Generate reproducible pipelines.** Output is working scripts, not just ingested data. Scripts must be re-runnable from scratch to produce identical results.
3. **Code-first extraction.** Always generate dbt models and scripts. Manual extraction is not reproducible.
4. **The project IS the state.** Discover existing state from `models/`, `tools/`, `rag_content/`.
5. **Value-driven tools.** Understand what information is valuable before creating tools.
6. **Test-first validation.** Compute expected results from ORIGINAL SOURCE FILE (not database) before implementing tools.
7. **Ask when uncertain.** If classification or linking is ambiguous, ask the user.

## Execution Pipeline

### Phase 0: Project Context

#### New project:
```bash
mkdir my-project && cd my-project
uv venv && source .venv/bin/activate
uv pip install mxcp pandas openpyxl python-docx duckdb
mxcp init --bootstrap
```

Create `dbt_project.yml` with `model-paths: ["models"]`.

#### Existing project:
```bash
# Ensure venv is active
source .venv/bin/activate

# Verify/install dependencies
uv pip install mxcp pandas openpyxl python-docx duckdb

# Discover current state - MUST review before adding new files
ls models/*.py models/*.sql 2>/dev/null     # Existing dbt models
cat models/schema.yml                         # Table schemas, relationships
ls tools/*.yml 2>/dev/null                    # Existing tools
ls scripts/*.py 2>/dev/null                   # Existing RAG extraction scripts
cat rag_content/manifest.json 2>/dev/null    # RAG content
```

**Before proceeding, understand:**
- What entities/tables already exist?
- What tools are available and what do they query?
- Will the new file's data overlap with existing data?
- Should new data extend existing models or stay separate?

#### State Tracking

**The project tracks ingestion state through its artifacts.** Before any ingestion, compare:

| Check | How |
|-------|-----|
| Source files exist | `ls source_data/` vs models that reference them |
| Schema changes | Compare source columns vs `schema.yml` |
| Row counts | Query DB vs source file counts |
| RAG coverage | `manifest.json` sources vs `source_data/` |

#### Handling Changes

| Change Type | Action |
|-------------|--------|
| Updated file | Compare columns, update model, re-run (idempotent) |
| Deleted file | **Ask user:** keep artifacts or remove all? |
| New version alongside old | Separate models + combined view if needed |
| Duplicates detected | **Ask user:** skip, update, or version? |

### Phase 1: Deep Document Analysis

**Goal: Fully understand the file BEFORE any ingestion decisions.**

#### 1.1 Excel Analysis

**Analyze each sheet independently** - sheets may have different content types and destinations.

For each sheet:
1. **Structure:** merged cells (>10% = complex), header location, data boundaries
2. **Content type:** Determine where on the spectrum:

| Content Type | Characteristics | Destination |
|--------------|-----------------|-------------|
| Structured (CSV-like) | Numbers, dates, short strings, categorical values | DB only |
| Text-heavy | Long text in cells (>200 chars), descriptions, notes | RAG only |
| Mixed | Structured fields + text content in same rows | Both |

3. **Multi-entity columns:** Same data repeated for different entities
4. **If unclear:** Use vision analysis. See [vision-analysis.md](references/vision-analysis.md).

**Multi-entity pattern:** When columns repeat per entity (e.g., `Value_A`, `Value_B`, `Value_C`):
- Identify the entity dimension
- Map columns to entities
- Denormalize: create one row per (record, entity) with entity-specific columns

**Hierarchical structure:** Merged header cells with sub-headers underneath:
- Flatten hierarchy: combine parent + child headers (e.g., "Q1 Revenue" from merged "Q1" + "Revenue")
- Preserve hierarchy in column names or as separate dimension

**Transposed tables:** Headers in rows instead of columns:
- Detect by checking if first column contains field names and other columns contain instances
- Transpose before extraction: `df = df.T` or pivot appropriately

**Explanatory content (NEVER lose this):**
- Cells or paragraphs explaining what data means → include as metadata or RAG
- If structured data: add as column (e.g., `_description`) or separate lookup table
- If RAG: include as context in the chunk
- **Rule:** Every explanatory paragraph must appear somewhere in output

#### 1.2 Word Document Analysis

Process paragraph by paragraph, table by table. Track section context from headings. For each content block, classify and decide destination.

**Explanatory paragraphs:** Paragraphs describing tables or sections must NOT be discarded:
- Include with related RAG chunks as context
- Or store in DB as metadata linked to the data they describe

#### 1.3 Classification: Database vs RAG vs Both

**The key question is NOT "is this tabular?" but "will queries be needed?"**

| Content | Will queries be needed? | Destination |
|---------|------------------------|-------------|
| Tables with numbers/dates for aggregation | Yes → **Database** | DuckDB for SUM, COUNT, filtering |
| Tables with descriptive text columns | No → **RAG** | Convert to narrative text |
| Tables that need both query AND search | Both → **Database + RAG** | Store in DB, also generate RAG text |
| Paragraphs, narrative text | No → **RAG** | txt for semantic search |

**Decision process:**
1. **Database only:** Structured data for queries (filters, aggregations, joins)
2. **RAG only:** Text content for semantic similarity search
3. **Both:** Same data needs structured queries AND semantic search

**Converting tables to RAG:** See [data-classification.md](references/data-classification.md#converting-tables-to-rag-text) for conversion examples.

**When to ask user:**
- Unclear if queries will be needed on this data
- Table has mixed numeric + text columns
- Same data might need both approaches

#### 1.4 Extraction Strategy

**Always generate code** - dbt models and scripts that can be re-run.

| Content Type | Approach |
|--------------|----------|
| Clean tables | Direct pandas extraction |
| Messy tables (merged cells) | Preprocessing script to normalize, then extract |
| Complex structure | Multi-step pipeline: clean → transform → load |

**For large documents (>50 pages):** Process section-by-section. See [extraction-strategy.md](references/extraction-strategy.md).

**Document extraction strategy per section before proceeding.**

### Phase 2: Integration Analysis

Skip if project is empty or file has only RAG content (no database tables).

#### 2.1 Primary Key Detection

Look for columns named `id`, `{table}_id`, `key`, `code` that are unique and non-null.

#### 2.2 Relationship Detection

Detect FK columns by:
- Naming patterns: `*_id`, `*_key`, `*_code`
- Value matching: column values exist in another table's PK

#### 2.3 RAG-DB Link Detection

**Detection methods (in priority order):**
1. **Explicit IDs:** Regex for "Customer 101", "Order #12345", "ID: ABC-123"
2. **Entity names:** Match known names from DB against text
3. **Section context:** Heading "Customer Analysis" + table "customers" → link
4. **Semantic similarity:** Use embeddings only when explicit matching fails

**Link types:** `describes` (explains entity), `summarizes` (aggregates), `references` (mentions), `contextualizes` (background)

**When no clear link exists:** Don't force it. Many RAG chunks are standalone.

#### 2.4 Integration Decisions

For each NEW structured table:
1. **Same entity exists?** → Create combined view or extend existing model
2. **>70% column overlap?** → Merge candidate, align schemas
3. **FK columns?** → Link to existing tables
4. **Related RAG content?** → Update manifest with cross-references

**When adding files to existing project:**
- Review existing `models/`, `scripts/`, `tools/` before creating new ones
- Same entity in multiple files? Create combined view or extend existing model
- Never create duplicates - extend existing tools rather than creating `_v2` versions

**Document decisions before proceeding.**

### Phase 3: Generate Extraction Scripts

**The deliverable is the PIPELINE, not just the data.** Generate dbt models and scripts that:
- Can be re-run from scratch to reproduce identical results
- Update output automatically when source files change
- Are version-controlled alongside the project

#### Folder Structure Per Source

**All artifacts for a source file share the same folder name:**

```
{source} = sanitized filename (e.g., sales_report_2024)

models/{source}/          # dbt models for this source
tools/{source}/           # tools for querying this source
rag_content/{source}/     # RAG chunks from this source
scripts/{source}/         # standalone scripts (if RAG-only)
```

Example for `sales_report.xlsx`:
```
models/sales_report/
├── load_orders.py        # → table: sales_report_orders
├── load_products.py      # → table: sales_report_products
└── generate_rag.py       # generates RAG from DB (if Both)

tools/sales_report/
├── get_order.yml
└── search_products.yml

rag_content/sales_report/
├── chunk_001.txt
└── chunk_002.txt
```

This makes it easy to identify, update, or remove all artifacts for a source.

#### DB Only → dbt Models

**Model requirements:**
- Place in `models/{source}/` folder
- Table name: `{source}_{sheet}` (e.g., `sales_report_orders`)
- Read from `source_data/{filename}`
- Clean column names: lowercase, underscores, alphanumeric only

**Idempotency:** dbt models are inherently idempotent - re-running `mxcp dbt run` rebuilds tables from source.

**schema.yml (REQUIRED):** Every model MUST have dbt tests. See [testing.md](references/testing.md).

Minimum tests: row count, `not_null` + `unique` on PK, `relationships` on FKs, `accepted_values` on categoricals.

#### RAG Only → Extraction Script

For text content that only needs semantic search (no DB queries):

```python
# scripts/annual_report/extract_rag.py
import os
import shutil
from docx import Document

source_name = "annual_report"  # must match folder name
shutil.rmtree(f"rag_content/{source_name}", ignore_errors=True)
os.makedirs(f"rag_content/{source_name}")

doc = Document("source_data/annual_report.docx")
for idx, para in enumerate(doc.paragraphs):
    if para.text.strip():
        with open(f"rag_content/{source_name}/chunk_{idx}.txt", "w") as f:
            f.write(para.text)
```

RAG files: plain text only, never `.md`. See [rag-format.md](references/rag-format.md).

**Chunk size:** Small for standalone facts, medium for sections needing context, large for narratives. Never split mid-sentence.

#### DB + RAG → dbt Model + RAG Generation

**Why both?** DB for structured queries, RAG for semantic search on same data.

```python
# models/product_catalog/generate_rag.py - dbt.ref() creates dependency
import os
import shutil

def model(dbt, session):
    df = dbt.ref("product_catalog_items").df()
    source_name = "product_catalog"  # must match folder name

    shutil.rmtree(f"rag_content/{source_name}", ignore_errors=True)
    os.makedirs(f"rag_content/{source_name}")

    for idx, row in df.iterrows():
        content = f"{row['name']}: {row['description']}"
        with open(f"rag_content/{source_name}/chunk_{idx}.txt", "w") as f:
            f.write(content)

    return df
```

Use simple RAG format (content only) when generating from DB - the DB is the source of truth.

**Idempotency:** RAG generation scripts clear and recreate the target folder, ensuring re-runs produce identical results regardless of previous state.

#### Update manifest.json

See [rag-format.md](references/rag-format.md#manifestjson-structure) for full structure.

Key fields: `chunks` (chunk metadata), `db_to_rag_index` (reverse lookup `{table}.{id}` → chunk IDs).

#### Validate
```bash
mxcp validate && mxcp dbt run && mxcp dbt test
```

### Phase 4: Data Value Analysis

**Goal: Understand what information is valuable BEFORE creating tools.**

**Skip if only unstructured data (no tools needed for RAG-only content).**

#### 4.1 Domain Understanding

1. **Domain:** Financial? Sales? HR? Operations?
2. **Users:** What role? What decisions?
3. **Entities:** Primary entities and relationships
4. **Metrics:** Totals, counts, trends, rankings
5. **RAG-DB synergy:** What questions need both structured and unstructured data?

#### 4.2 Question Generation

Generate 5-15 concrete questions:
- "What are the total sales for customer X?"
- "Show me the analysis notes for customer X" (RAG lookup)
- "Which customers have related documentation?"

#### 4.3 Compute Ground Truth

**Compute expected values from the ORIGINAL SOURCE FILE, not the database.**

```python
# CORRECT: Read original file with pandas
df = pd.read_excel("source_data/sales_report.xlsx")
expected_count = len(df)
expected_total = df["amount"].sum()

# WRONG: Query database (could have extraction bugs)
# result = duckdb.query("SELECT COUNT(*) FROM sales")  # Don't use this!
```

If database results don't match source file calculations, the extraction has a bug.

### Phase 5: Tool Design & Implementation

**Invoke mxcp-expert skill** for tool creation.

#### 5.1 Design Principles

Each tool must be:
1. **Self-documenting** - LLM understands without extra context
2. **Well-parametrized** - Clear names, types, descriptions, examples
3. **Categorical values documented** - Enum values listed in description and schema
4. **Focused** - One tool = one question type
5. **Predictable** - Same inputs → same outputs

#### 5.2 Categorical Data Handling

For columns with ≤20 unique values: add `enum` to parameter schema and list valid values in description.

#### 5.3 Tool Categories

| Question Type | Pattern | Example |
|--------------|---------|---------|
| Lookup | `get_{entity}_by_id` | `get_customer_by_id` |
| Aggregation | `get_{entity}_{metric}` | `get_customer_sales` |
| Search | `search_{entities}` | `search_orders` |
| **RAG lookup** | `get_{entity}_docs` | `get_customer_docs` |

#### 5.4 MXCP Tool Tests (REQUIRED)

**Every tool MUST include tests.** See [testing.md](references/testing.md) for complete format and examples.

Before writing each tool:
1. Compute expected values from ORIGINAL SOURCE FILE (Excel/Word) using pandas/python-docx
2. Add test cases with those pre-computed values
3. Include edge cases (empty, single, multiple results)

**Test values must come from source file, not database.** If tool query returns different values than source file analysis, the extraction has a bug - fix the extraction, don't adjust the test.

### Phase 6: Run All Tests (REQUIRED)

**Both dbt and mxcp tests MUST pass before completion.**

```bash
mxcp dbt run && mxcp dbt test  # Schema constraints
mxcp validate && mxcp test      # Tool behavior
```

**If tests fail:** See [testing.md](references/testing.md#debugging-test-failures) for debugging guide. Never just change expected values - fix root cause.

### Phase 7: Summary

Document:
- File processed, classification decisions
- Tables created with dbt test results (pass/fail)
- RAG chunks created with link counts
- Tools created with mxcp test results (pass/fail)
- All tests must show PASS before declaring completion

## Output Structure

```
project/
├── mxcp-site.yml
├── dbt_project.yml
├── source_data/
│   └── {original files}
├── models/
│   ├── {source}/              # folder per source file
│   │   ├── load_*.py          # dbt models for DB ingestion
│   │   └── generate_rag.py    # RAG generation (if Both)
│   ├── combined_*.sql         # combined views across sources (if needed)
│   └── schema.yml
├── scripts/
│   └── {source}/              # folder per source file
│       └── extract_rag.py     # standalone RAG extraction
├── tools/
│   └── {source}/              # folder per source file
│       └── *.yml
├── sql/
│   └── *.sql
├── rag_content/
│   ├── {source}/              # folder per source file
│   │   └── *.txt              # .txt only, never .md
│   └── manifest.json
└── data/
    └── db-default.duckdb
```

**Consistency rule:** `{source}` folder name must match across `models/`, `tools/`, `scripts/`, and `rag_content/`.

## When to Ask User

### Upfront Discovery (ask before analysis)

- "What queries will you need?" (by ID, by category, aggregations, search)
- "What metadata should be preserved?" (dates, status fields, notes)
- "Should data be in DB only, RAG only, or both?"
- "Are there entity-specific columns?" (per-country, per-version, per-department)

### During Processing

| Situation | Action |
|-----------|--------|
| Unclear if queries needed | Ask: "Will you need to run queries on this data, or just search it?" |
| Re-ingesting same file | Ask: "Replace, append, or merge?" |
| Ambiguous entity linking | Ask: "Does this text relate to [entity]?" |
| Schema conflict with existing | Ask: "Rename new table or migrate existing?" |
| Large document (>50 pages) | Inform: "Processing in sections, may take time" |

## Error Handling

- Content block analysis fails → Log, skip block, continue
- Table extraction fails → Try alternative parsing, log if fails
- Model build fails → Stop, fix
- Test fails → Investigate root cause
- Link detection uncertain → Skip link, log for review