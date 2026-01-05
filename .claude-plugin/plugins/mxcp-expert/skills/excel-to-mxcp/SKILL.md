---
name: excel-to-mxcp
description: "Intelligent single-file Excel/CSV ingestion into MXCP servers. Given ONE file (.xlsx, .xls, .csv), performs deep analysis to classify each sheet/section as structured (DuckDB/dbt) or unstructured (RAG txt). When adding to an existing MXCP project, reviews current state and decides whether to extend or update. Use when: (1) Ingesting a single Excel/CSV file into an MXCP project, (2) Adding a new data file to an existing MXCP server, (3) Processing messy Excel with merged cells or irregular structure, (4) Preparing tabular or text data for RAG systems."
---

# Excel to MXCP Ingestion

Single-file intelligent ingestion of Excel/CSV into MXCP. Analyzes document thoroughly before ingestion, routes data to DuckDB (structured) or RAG txt (unstructured).

## Prerequisites

- xlsx skill (Anthropic) for Excel/CSV reading
- mxcp-expert skill for MXCP server creation

## Core Principles

1. **Analyze first, ingest second.** Fully understand the file before writing anything.
2. **The project IS the state.** Discover existing state from `models/`, `tools/`, `rag_content/`.
3. **Value-driven tools.** Understand what information is valuable before creating tools.
4. **Test-first validation.** Compute expected results from source before implementing tools.

## Execution Pipeline

### Phase 0: Project Context

#### New project:
```bash
mkdir my-project && cd my-project
uv venv && source .venv/bin/activate
uv pip install mxcp
mxcp init --bootstrap
```

Create `dbt_project.yml`:
```yaml
name: excel_ingestion
version: "1.0.0"
config-version: 2
profile: default
model-paths: ["models"]
```

#### Existing project:
```bash
ls models/*.py models/*.sql 2>/dev/null     # Existing dbt models
cat models/schema.yml                         # Table schemas, relationships
ls tools/*.yml 2>/dev/null                    # Existing tools
cat rag_content/manifest.json 2>/dev/null    # RAG content
```

Note: What entities exist? What relationships? What tools?

### Phase 1: Deep Document Analysis

**Goal: Fully understand the file BEFORE any ingestion decisions.**

#### 1.1 Sheet Discovery
```python
from openpyxl import load_workbook
wb = load_workbook(filepath, read_only=True)
sheets = wb.sheetnames
```

#### 1.2 Per-Sheet Analysis

For EACH sheet:
1. **Structure:** merged cells (>10% = complex), header location, data boundaries
2. **Content:** column types, average text length, long-form text (>200 chars)
3. **If unclear:** Use vision analysis. See [vision-analysis.md](references/vision-analysis.md).

#### 1.3 Classification

See [data-classification.md](references/data-classification.md):

| Pattern | Classification | Destination |
|---------|---------------|-------------|
| Regular grid, typed data, short text | **Structured** | DuckDB via dbt |
| Long text, paragraphs, narrative | **Unstructured** | txt for RAG |
| Mixed tables + text | **Semi-structured** | Split both |

**If user provides context** (e.g., "this is financial data for accountants"), use it to inform classification and Phase 4.

**Document classification decisions before proceeding.**

### Phase 2: Integration Analysis

Skip if project is empty or file has only unstructured data.

#### 2.1 Primary Key Detection

For each new table, detect PK:
```python
def detect_pk(df, table_name):
    patterns = ['id', f'{table_name}_id', f'{table_name[:-1]}_id', 'key', 'code']
    for p in patterns:
        if p in df.columns and df[p].is_unique and df[p].notna().all():
            return p
    # Fallback: first unique column
    for col in df.columns:
        if df[col].is_unique and df[col].notna().all():
            return col
    return None
```

#### 2.2 Relationship Detection

Detect FK columns by:
- Naming patterns: `*_id`, `*_key`, `*_code`
- Value matching: column values exist in another table's PK

#### 2.3 Integration Decisions

For each NEW structured table:
1. **Same name exists?** → Extend with UNION
2. **>70% column overlap?** → Merge candidate
3. **FK columns?** → Link to existing tables
4. **Schema conflict?** → Rename or migrate

**Document decisions before proceeding.**

### Phase 3: Generate Artifacts

**Skip DuckDB parts if only unstructured data. Skip RAG parts if only structured data.**

#### Structured Data → dbt Models

```python
# models/load_{source}_{sheet}.py
import pandas as pd

def model(dbt, session):
    df = pd.read_excel('{filepath}', sheet_name='{sheet}')
    df = df.dropna(how='all')
    df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('[^a-z0-9_]', '', regex=True)
    return df
```

#### Extending existing table:
```sql
SELECT * FROM {{ ref('load_existing') }}
UNION ALL
SELECT * FROM {{ ref('load_new') }}
```

#### Update schema.yml
```yaml
version: 2
models:
  - name: customers
    description: "Source: sales.xlsx > Customers"
    columns:
      - name: id
        tests: [not_null, unique]
```

#### Unstructured Data → RAG txt

```
=== SOURCE METADATA ===
File: {source_file}
Sheet: {sheet_name}
Generated: {timestamp}

=== CONTENT ===
{extracted text}

=== KEYWORDS ===
{keywords}
```

Update `rag_content/manifest.json`.

#### Validate
```bash
mxcp validate && mxcp dbt run && mxcp dbt test
```

**Stop and fix errors before proceeding.**

### Phase 4: Data Value Analysis

**Goal: Understand what information is valuable BEFORE creating tools.**

**Skip if only unstructured data (no tools needed for RAG-only content).**

#### 4.1 Domain Understanding

1. **Domain:** Financial? Sales? HR? Operations?
2. **Users:** What role? What decisions?
3. **Entities:** Primary entities and relationships
4. **Metrics:** Totals, counts, trends, rankings
5. **Insights:** Aggregations, filters, joins that matter

**If user provided context, use it here.**

#### 4.2 Question Generation

Generate 5-15 concrete questions users would ask. Examples:
- "What are the total sales for customer X?"
- "Which products sold the most?"
- "Show me orders over $10,000"

#### 4.3 Compute Ground Truth

**CRITICAL: Compute expected results from source Excel BEFORE writing tools.**

For each question:
```python
# Question: "Total sales for customer 101?"
df = pd.read_excel('sales.xlsx', sheet_name='Orders')
expected = df[df['customer_id'] == 101]['amount'].sum()
# Result: 45230.50
```

Record with precision:
```yaml
question: "Total sales for customer 101"
expected: 45230.50
derivation: "df[df['customer_id'] == 101]['amount'].sum()"
```

**These expected results become test assertions in tool definitions.**

### Phase 5: Tool Design & Implementation

**Goal: Create tools that answer identified questions.**

#### 5.1 Design Principles

Each tool must be:
1. **Self-documenting** - LLM understands without extra context
2. **Well-parametrized** - Clear names, types, descriptions, examples
3. **Focused** - One tool = one question type
4. **Predictable** - Same inputs → same outputs

#### 5.2 Tool Structure

```yaml
mxcp: 1
tool:
  name: get_customer_sales
  description: |
    Get total sales for a customer.
    Returns sum of order amounts for the given customer ID.
    Use when asked about customer spending or sales volume.
  parameters:
    - name: customer_id
      type: integer
      description: The customer's unique identifier
      required: true
      examples: [101, 205]
  return:
    type: object
    properties:
      customer_id: {type: integer}
      total_sales: {type: number}
      order_count: {type: integer}
  source:
    file: ../sql/get_customer_sales.sql
  tests:
    - name: customer_101
      description: "Verified against source Excel"
      arguments: [{key: customer_id, value: 101}]
      result: {customer_id: 101, total_sales: 45230.50, order_count: 4}
```

#### 5.3 Tool Categories

| Question Type | Pattern | Example |
|--------------|---------|---------|
| Lookup | `get_{entity}_by_id` | `get_customer_by_id` |
| Aggregation | `get_{entity}_{metric}` | `get_customer_sales` |
| Search | `search_{entities}` | `search_orders` |
| Rankings | `get_top_{entities}` | `get_top_products` |
| Time-based | `get_{metric}_by_{period}` | `get_sales_by_month` |

#### 5.4 Existing Tools

If extending data, verify existing tools:
```bash
mxcp test  # Run existing tests
```
If tests fail, investigate if new data changes expected results.

### Phase 6: Validation & Reconciliation

```bash
mxcp validate && mxcp lint && mxcp test
```

**If tests fail, investigate systematically:**

1. Re-verify pandas calculation from source
2. Check data in DuckDB: `mxcp query "SELECT ..."`
3. Identify source: row filtering? type conversion? column normalization?
4. Fix root cause (not just the tool)

**All tests must pass.**

### Phase 7: Summary

Document:
- File processed, classification decisions
- Tables created/extended (with row counts)
- RAG chunks created
- Questions identified, tools created
- Discrepancies found and resolved

## Output Structure

```
project/
├── mxcp-site.yml
├── dbt_project.yml
├── models/
│   ├── load_{source}_{sheet}.py
│   └── schema.yml
├── tools/
│   └── get_*.yml
├── sql/
│   └── *.sql
├── rag_content/
│   ├── *.txt
│   └── manifest.json
└── data/
    └── db-default.duckdb
```

## Error Handling

- Sheet analysis fails → Log, skip, continue
- Model build fails → Stop, fix
- Test fails → Investigate root cause
