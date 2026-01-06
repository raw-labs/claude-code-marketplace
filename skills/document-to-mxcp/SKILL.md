---
name: document-to-mxcp
description: "Intelligent single-file document ingestion into MXCP servers. Supports Excel (.xlsx, .xls, .csv) and Word (.docx) files. Analyzes content to determine if queries will be needed (DuckDB) or semantic search (RAG txt), including converting tabular text to narrative format. Creates bidirectional references between RAG content and database entries. Use when: (1) Ingesting a document into an MXCP project, (2) Adding a new data file to an existing MXCP server, (3) Processing documents with mixed tables and text, (4) Preparing data for RAG systems with database linkage."
---

# Document to MXCP Ingestion

Single-file intelligent ingestion of Excel/Word documents into MXCP. Analyzes content to determine: will queries be needed (→ DuckDB) or semantic search (→ RAG txt)? Supports bidirectional references.

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

## Environment Requirements

**Always use `uv` for package management and run in a virtual environment.**

```bash
# Create and activate venv (if not exists)
uv venv && source .venv/bin/activate

# Required packages
uv pip install mxcp pandas openpyxl python-docx duckdb
```

**Never install packages globally. Always verify venv is active before running commands.**

## Database

**Always use the default database: `data/db-default.duckdb`** - created automatically by MXCP if not specified. Never create custom database names.

## Core Principles

1. **Analyze first, ingest second.** Fully understand the file before writing anything.
2. **The project IS the state.** Discover existing state from `models/`, `tools/`, `rag_content/`.
3. **Choose extraction strategy wisely.** Use code for clean structure, manual for complex content.
4. **Value-driven tools.** Understand what information is valuable before creating tools.
5. **Test-first validation.** Compute expected results from source before implementing tools.
6. **Ask when uncertain.** If classification or linking is ambiguous, ask the user.

## Execution Pipeline

### Phase 0: Project Context

#### New project:
```bash
mkdir my-project && cd my-project
uv venv && source .venv/bin/activate
uv pip install mxcp pandas openpyxl python-docx duckdb
mxcp init --bootstrap
```

Create `dbt_project.yml`:
```yaml
name: document_ingestion
version: "1.0.0"
config-version: 2
profile: default
model-paths: ["models"]
```

#### Existing project:
```bash
# Ensure venv is active
source .venv/bin/activate

# Verify/install dependencies
uv pip install mxcp pandas openpyxl python-docx duckdb

# Discover current state
ls models/*.py models/*.sql 2>/dev/null     # Existing dbt models
cat models/schema.yml                         # Table schemas, relationships
ls tools/*.yml 2>/dev/null                    # Existing tools
cat rag_content/manifest.json 2>/dev/null    # RAG content
```

Note: What entities exist? What relationships? What RAG-DB links?

#### Re-ingestion (same file, updated content):

If the same source file was previously ingested:
1. Check `manifest.json` for existing chunks from this file
2. **Ask user:** "This file was previously ingested. Should I: (a) Replace all content, (b) Append new content, (c) Merge with deduplication?"
3. For replace: Delete old models/chunks, create new
4. For append: Create new models with `_v2` suffix, update combined views
5. For merge: Compare row-by-row, update changed, add new

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

#### 1.2 Word Document Analysis

Process paragraph by paragraph, table by table. Track section context from headings. For each content block, classify and decide destination.

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

#### 1.4 Extraction Strategy Decision

**For each content block, decide: code extraction or manual step-by-step?**

| Use Code Extraction | Use Manual Extraction |
|---------------------|----------------------|
| Clean tables (consistent columns) | Messy tables (merged cells, varying structure) |
| Repeating structure patterns | Context-dependent content ("see above") |
| Standard paragraph chunking | Complex narrative requiring understanding |
| Predictable document template | Meaning needed to classify |

**For large documents (>50 pages):** Process section-by-section. See [extraction-strategy.md](references/extraction-strategy.md).

**Code extraction:** Write Python dbt models to extract and load data programmatically.
**Manual extraction:** Agent reads content, understands it, decides what to extract, writes results.

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
1. **Same name exists?** → Extend with UNION
2. **>70% column overlap?** → Merge candidate
3. **FK columns?** → Link to existing tables
4. **Related RAG content?** → Plan bidirectional links

**Document decisions before proceeding.**

### Phase 3: Extract & Generate Artifacts

**Execute extraction strategy decided in Phase 1.4.**

#### Code Extraction Path

For clean, consistent content - write Python dbt models (`models/load_*.py`). Always use dbt models for schema validation, testing, and lineage tracking.

#### Manual Extraction Path

For complex content - agent reads, understands, and extracts step-by-step:

1. Read section (10-20 pages)
2. For each element: understand meaning, decide destination
3. Extract with context (flatten merged cells, resolve references)
4. Write to DB/RAG with proper metadata
5. Track progress, move to next section

#### Queryable Data → dbt Models

Create one dbt model per sheet/table: `models/load_{source}_{sheet}.py`
- Each sheet may have different destination (DB only, RAG only, or Both)
- Read from `source_data/{filename}` (copy source files there first)
- Clean column names: lowercase, underscores, alphanumeric only
- Add `_rag_refs` column for bidirectional linking (if using Both)

#### Update schema.yml (REQUIRED)

**Every model MUST have dbt tests.** See [testing.md](references/testing.md) for complete format.

Minimum tests per model:
- **Row count test** - verify ingested count matches source document
- `not_null` + `unique` on primary key
- `not_null` on required fields
- `relationships` on foreign keys
- `accepted_values` on categorical columns

#### Unstructured Data → RAG txt

RAG files: `rag_content/*.txt` - plain text only, never `.md`. See [rag-format.md](references/rag-format.md).

**Chunk size:** Small for standalone facts, medium for sections needing context, large for flowing narratives. Never split mid-sentence or separate tables from descriptions.

#### Both DB + RAG (generate RAG from DB)

**Why both?** Different retrieval needs:
- **DB:** User knows criteria ("filter by category X", "sum amounts for Q1")
- **RAG:** User describes semantically ("find content about performance issues")

When data needs both, ingest to DB first, then generate RAG from DB:

```python
# models/generate_rag.py - runs AFTER data is in DB
def model(dbt, session):
    df = dbt.ref("my_table").df()

    for entity in df["entity"].unique():
        rows = df[df["entity"] == entity]
        content = format_as_text(rows)  # Convert to readable text
        write_file(f"rag_content/{entity}.txt", content)

    return df  # Return unchanged for dbt lineage
```

Use simple RAG format (content only) when generating from DB - the DB is the source of truth.

#### Update manifest.json

See [rag-format.md](references/rag-format.md#manifestjson-structure) for full structure.

Key fields: `chunks` (chunk metadata), `db_to_rag_index` (reverse lookup `{table}.{id}` → chunk IDs).

#### Populate DB-side References

After RAG chunks created, update `_rag_refs` column from manifest's `db_to_rag_index`.

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

Compute expected values from source data before writing tests. Query pandas DataFrames for aggregations, scan RAG chunks for link verification.

### Phase 5: Tool Design & Implementation

**Invoke mxcp-expert skill** for tool creation. Read `common-mistakes.md` first.

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
1. Query source data to compute expected result
2. Add test cases matching pre-computed values
3. Include edge cases (empty, single, multiple results)

**Test values must match source data exactly.** If test fails, investigate - never just adjust expected value.

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
│   ├── load_*.py
│   ├── populate_rag_refs.py
│   └── schema.yml
├── tools/
│   └── *.yml
├── sql/
│   └── *.sql
├── rag_content/
│   ├── *.txt                  # .txt only, never .md
│   └── manifest.json
└── data/
    └── db-default.duckdb
```

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