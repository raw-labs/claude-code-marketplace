---
name: excel-to-mxcp
description: "Intelligent Excel ingestion into MXCP servers. Handles messy, poorly-structured Excel files with merged cells, irregular layouts, and mixed data types. Automatically classifies data as structured (→ DuckDB/dbt), unstructured (→ RAG-friendly txt), or semi-structured (→ hybrid). Auto-detects relationships across files, generates MXCP tools, and tracks lineage. Use when: (1) Ingesting multiple Excel files into an MXCP project, (2) Processing messy Excel with merged cells or irregular structure, (3) Creating an MCP server from Excel data, (4) Preparing Excel data for RAG systems."
---

# Excel to MXCP Ingestion

One-shot intelligent ingestion of messy Excel files into MXCP with structured data in DuckDB and unstructured data in RAG-friendly txt files.

## Prerequisites

- xlsx skill (Anthropic) for Excel reading - provides pandas/openpyxl for reading Excel
- mxcp-expert skill for MXCP server creation

## State Tracking

**Critical for multi-file processing across context summarizations.**

Maintain `ingestion_state.json` in project root.

### Rules

1. **Before processing any file**: Read `ingestion_state.json` (create empty state if not exists)
2. **When creating a table**: Check if table with similar name/columns exists → extend or merge
3. **When detecting relationships**: Check against existing tables, not just current batch
4. **After processing**: Update `ingestion_state.json` immediately
5. **Pending relationships**: Track columns that look like FKs but reference tables not yet seen

See [state-tracking.md](references/state-tracking.md) for state schema and extend/merge logic.

## Execution Pipeline

Execute phases sequentially. No user interaction required.

### Phase 0: Project Setup

```bash
# If no MXCP project exists:
mkdir my-project && cd my-project
uv venv && source .venv/bin/activate
uv pip install mxcp
mxcp init --bootstrap
```

**Create initial state file if not exists:**
```json
{
  "last_updated": null,
  "tables": {},
  "relationships": [],
  "tools": [],
  "rag_chunks": {},
  "pending_relationships": []
}
```

**Create dbt_project.yml if not exists:**
```yaml
name: excel_ingestion
version: "1.0.0"
config-version: 2
profile: default
model-paths: ["models"]
```

### Phase 1: Discovery

**Processing order for multiple files:**
1. Read all file names and sheet names first
2. Process files that appear to be "master data" first (customers, products, locations)
3. Then process transactional data (orders, sales, events)
4. This order helps relationship detection

For each Excel file, analyze structure using openpyxl:
- Count merged cells per sheet
- Detect max rows/columns
- Flag sheets needing vision analysis (merged_cells > 10% of used range)

**If structure unclear**: Render sheet to image, then analyze with vision. See [vision-analysis.md](references/vision-analysis.md).

### Phase 2: Classification

| Pattern | Classification | Destination |
|---------|---------------|-------------|
| Regular rows/columns, consistent headers, typed data | **Structured** | DuckDB via dbt |
| Narrative text, paragraphs, notes, descriptions | **Unstructured** | txt for RAG |
| Tables with embedded notes, mixed layouts | **Semi-structured** | Hybrid |

See [data-classification.md](references/data-classification.md) for detailed criteria and detection algorithm.

### Phase 3: Relationship Detection

**Include tables from `ingestion_state.json` when detecting relationships.**

1. Identify primary key for each table (first unique column, or column named `id`, `*_id`, `key`, etc.)
2. Check columns for FK naming patterns (customer_id, product_id, etc.)
3. Look for referenced table in current batch AND state
4. If found → create relationship using detected PK (not hardcoded "id")
5. If not found → add to pending_relationships
6. Check if new tables resolve any pending relationships from state

**After detection, update `ingestion_state.json`** with new relationships and pending items.

### Phase 4: Generate Artifacts

#### Structured Data → dbt Python Models

```python
# models/load_{source_file}_{sheet_name}.py
import pandas as pd

def model(dbt, session):
    """Lineage: {source_file} > {sheet_name}"""
    df = pd.read_excel('{filepath}', sheet_name='{sheet_name}')
    df = df.dropna(how='all')
    df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('[^a-z0-9_]', '', regex=True)
    return df
```

#### Extending Existing Tables

When `should_extend_table()` returns "extend":
- If same columns: Create new model, then create a UNION view
- If additional columns: Modify existing model to include new columns, or create joined view

When returns "merge_candidate": Review column mapping, may need manual decision.

#### dbt schema.yml with tests

```yaml
# models/schema.yml
version: 2
models:
  - name: customers
    columns:
      - name: id
        tests: [not_null, unique]
      - name: email
        tests: [not_null]
  - name: orders
    columns:
      - name: id
        tests: [not_null, unique]
      - name: customer_id
        tests:
          - not_null
          - relationships:
              to: ref('customers')
              field: id
```

#### Unstructured Data → RAG-friendly txt

Chunk by section with context headers. See [data-classification.md](references/data-classification.md#rag-friendly-txt-format) for format.

#### Semi-structured Data → Hybrid

1. Extract tabular portions → dbt Python model
2. Extract narrative portions → txt file
3. Link via row/section identifiers

#### Incremental Validation

```bash
mxcp validate    # Verify YAML structure
mxcp dbt run     # Build models and load data
mxcp dbt test    # Run data quality tests
```

**Stop and fix any errors before proceeding.**

### Phase 5: Tool Design

**Goal: Expose the most valuable information through tools so LLMs can answer user questions.**

#### Analyze Data Value

Before creating tools, understand the data:
1. What entities exist? (customers, orders, products, etc.)
2. What are the key metrics? (totals, counts, averages)
3. What relationships matter? (customer orders, product sales)
4. What would users likely ask about this data?

#### Tool Design Principles

| User Need | Tool Pattern | Example |
|-----------|--------------|---------|
| Lookup specific record | `get_{entity}_by_{key}` | `get_customer_by_id` |
| Search/filter records | `search_{entities}` | `search_products` |
| List all records | `list_{entities}` | `list_categories` |
| Aggregate metrics | `get_{metric}_summary` | `get_sales_summary` |
| Relationship queries | `get_{related}_for_{entity}` | `get_orders_for_customer` |
| Time-based analysis | `get_{entity}_by_{period}` | `get_sales_by_month` |

#### Derive Tools From Data

```
For each structured table:
1. Create lookup tool if table has clear PK
2. Create search tool if table has searchable text columns
3. Create list tool if table is reference/dimension data

For relationships:
4. Create tools that traverse relationships (get orders for customer)

For numeric columns:
5. Create aggregation tools (sum, avg, count by category)

Based on user hints in prompt:
6. Prioritize tools that match user's stated goals
7. Add domain-specific tools based on data context
```

#### Example: Sales Data

If data contains customers, orders, products:
- `get_customer_by_id` - lookup
- `search_customers` - by name/email
- `get_orders_for_customer` - relationship
- `get_sales_by_product` - aggregation
- `get_top_customers` - analytics
- `get_monthly_revenue` - time series

### Phase 6: Tool Generation (Test-Driven)

**CRITICAL: Test-first approach. Derive expected results from source data BEFORE writing queries.**

#### Step 1: Derive Expected Results

Calculate expected results from source Excel/pandas data (ground truth). See [validation.md](references/validation.md#test-derivation-by-tool-type).

#### Step 2: Create Test Cases

Write tests FIRST with expected values:

```yaml
# tools/get_customer_by_id.yml
mxcp: 1
tool:
  name: get_customer_by_id
  description: |
    Get customer details by ID. Returns customer profile with contact info.
    Source: sales_data.xlsx > Customers
  parameters:
    - name: customer_id
      type: integer
      description: The customer's unique identifier
  return:
    type: object
    properties:
      id: {type: integer}
      name: {type: string}
      email: {type: string}
  source:
    file: ../sql/get_customer_by_id.sql
  tests:
    - name: lookup_existing_customer
      description: "Expected from source: row 5 of Customers sheet"
      arguments: [{key: customer_id, value: 101}]
      result:
        id: 101
        name: "Acme Corp"
        email: "contact@acme.com"
    - name: lookup_nonexistent
      arguments: [{key: customer_id, value: 99999}]
      result: null
```

#### Step 3: Write Tool Implementation

```sql
-- sql/get_customer_by_id.sql
SELECT id, name, email
FROM customers
WHERE id = $customer_id
```

#### Step 4: Validate and Lint

```bash
mxcp validate    # Schema correctness - fix any errors
mxcp lint        # Metadata quality - ensure descriptions, types, examples
```

**Fix all issues before proceeding.**

#### Step 5: Run Tests and Investigate Mismatches

```bash
mxcp test
```

**If tests fail, investigate systematically:**

1. Verify expected result is correct (re-check source Excel, use pandas)
2. Verify query logic: `mxcp query "SELECT * FROM customers WHERE id = 101"`
3. Cross-validate using [validation.md](references/validation.md#cross-validation-function)

#### Step 6: Document Verification

Each tool description should include verification notes (source file/sheet, cross-checks passed).

### Phase 7: Comprehensive Validation

**All tests must pass. Any failure requires investigation.**

```bash
mxcp validate    # Schema correctness
mxcp lint        # Metadata quality
mxcp dbt test    # Data integrity (not_null, unique, relationships)
mxcp test        # Tool tests (expected results from source)
```

#### Validation Checklist

- [ ] `mxcp validate` passes
- [ ] `mxcp lint` passes
- [ ] `mxcp dbt test` passes
- [ ] `mxcp test` passes - all expected results match source data
- [ ] Row counts match source Excel for each table
- [ ] Numeric column sums match source calculations
- [ ] Sample rows (5 per table) verified against source
- [ ] Relationship integrity verified (FK values exist)
- [ ] No data loss (all source rows accounted for)

**If any check fails: STOP and investigate.**

See [validation.md](references/validation.md) for cross-validation functions.

#### Final Summary

Log ingestion report: files processed, tables created (with row counts), txt files generated, relationships detected, tools generated, validation results.

## Output Structure

```
mxcp-project/
├── mxcp-site.yml
├── dbt_project.yml                # Required for dbt
├── ingestion_state.json           # Persistent state
├── models/
│   ├── load_sales_customers.py    # dbt Python models
│   ├── load_sales_orders.py
│   └── schema.yml                 # dbt tests
├── tools/
│   ├── get_customer_by_id.yml
│   ├── search_customers.yml
│   └── get_orders_for_customer.yml
├── sql/
│   └── *.sql
├── rag_content/
│   ├── sales_notes_section1.txt   # RAG chunks
│   └── manifest.json              # Lineage tracking
├── data/
│   └── db-default.duckdb
└── ingestion_report.json
```

## Lineage Tracking

Generate `rag_content/manifest.json`:

```json
{
  "generated": "2024-01-15T10:30:00Z",
  "sources": [
    {
      "file": "sales_data.xlsx",
      "sheets": [
        {"name": "Customers", "type": "structured", "table": "customers"},
        {"name": "Notes", "type": "unstructured", "chunks": 5}
      ]
    }
  ],
  "relationships": [
    {"from": "orders.customer_id", "to": "customers.id"}
  ]
}
```

## Error Handling

Continue on individual file/sheet errors. Log error and include in final summary.

## Capacity

- Process files incrementally to manage context
- Build schema progressively across files
- For very large files, process sheets individually
- State tracking enables resumption after context summarization
