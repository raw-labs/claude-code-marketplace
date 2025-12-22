---
name: mxcp-expert
description: Expert guidance for building production MCP servers using MXCP (Model Context Protocol eXtension Platform), an enterprise framework with SQL and Python endpoints, security, testing, and deployment. Use when: (1) Creating or initializing MXCP projects or MCP servers, (2) Building MCP tools, resources, or prompts, (3) Configuring endpoints, authentication, or policies, (4) Testing, validating, or debugging MXCP applications, or any task involving MXCP or MCP server development.
---

# MXCP Expert Skill

MXCP (Model Context Protocol eXtension Platform) is an enterprise-grade framework for building production-ready AI tools with SQL and Python.

## Quick Navigation

**New to MXCP?**
- [Quickstart](references/getting-started/quickstart.md) - Get running in 5 minutes
- [Hello World Tutorial](references/tutorials/hello-world.md) - Build your first tool
- [Introduction](references/getting-started/introduction.md) - How MXCP works

**Building Endpoints:**
- [SQL Endpoints](references/tutorials/sql-endpoints.md) - Query databases with SQL
- [Python Endpoints](references/tutorials/python-endpoints.md) - Complex logic and APIs
- [Endpoints Concepts](references/concepts/endpoints.md) - Tools, resources, prompts

**YAML Schema Reference:**
- [Tool Schema](references/schemas/tool.md) - Complete tool YAML reference
- [Resource Schema](references/schemas/resource.md) - Resource definitions
- [Prompt Schema](references/schemas/prompt.md) - Prompt templates
- [Site Config](references/schemas/site-config.md) - mxcp-site.yml reference
- [User Config](references/schemas/user-config.md) - ~/.mxcp/config.yml reference

**Quality & Testing:**
- [Validation](references/quality/validation.md) - Check endpoint structure
- [Testing](references/quality/testing.md) - Write and run tests
- [Linting](references/quality/linting.md) - Improve LLM understanding
- [Evals](references/quality/evals.md) - AI behavior testing

**Security:**
- [Authentication](references/security/authentication.md) - OAuth setup
- [Policies](references/security/policies.md) - Access control with CEL
- [Auditing](references/security/auditing.md) - Track operations

**Operations:**
- [Configuration](references/operations/configuration.md) - Profiles and environments
- [Deployment](references/operations/deployment.md) - Docker, systemd, production
- [Monitoring](references/operations/monitoring.md) - OpenTelemetry setup

**Reference:**
- [CLI Reference](references/reference/cli.md) - All commands
- [Common Tasks](references/reference/common-tasks.md) - Quick how-to guide
- [Python Runtime](references/reference/python.md) - Python API reference
- [SQL Functions](references/reference/sql.md) - Built-in SQL functions
- [Type System](references/concepts/type-system.md) - Parameter types

**Integrations:**
- [Claude Desktop](references/integrations/claude-desktop.md) - Client setup
- [dbt](references/integrations/dbt.md) - Data transformation
- [DuckDB](references/integrations/duckdb.md) - Extensions and features
- [Excel](references/integrations/excel-integration.md) - Excel file processing

**Examples:**
- [Analytics](references/examples/analytics.md) - Analytics patterns
- [Customer Service](references/examples/customer-service.md) - Support tools
- [Data Management](references/examples/data-management.md) - Data operations

## Core Principles

**This skill prioritizes:**

1. **Use uv for environments** - Always create venv with `uv venv` and activate before running mxcp
2. **Security First** - Use parameterized queries, validate inputs, implement authentication and policies
3. **Validation Always** - Run `mxcp validate` after every change, fix errors immediately
4. **Test Everything** - Write tests for all endpoints, run `mxcp test` before proceeding
5. **Quality Checks** - Use `mxcp lint` to improve LLM understanding of tools
6. **Incremental Development** - Build one tool at a time, validate before adding the next

**Environment setup (required before any mxcp command):**
```bash
uv venv && source .venv/bin/activate
uv pip install mxcp
```

## Mandatory Workflow

**Follow this workflow for every MXCP project:**

1. **Create** → `mxcp validate` → Fix any errors
2. **Implement** → `mxcp validate` → Fix any errors
3. **Add tests** → `mxcp test` → All tests must pass
4. **Check quality** → `mxcp lint` → Address warnings
5. **Verify manually** → `mxcp run tool NAME` → Confirm expected output

**When using dbt, also run:**
- `mxcp dbt test` → Verify data quality (not_null, unique, relationships)
- Add schema tests in `models/schema.yml` for all models

**Definition of Done:** A project is complete ONLY when:
- `mxcp validate` passes with no errors
- `mxcp test` passes with all tests green
- `mxcp dbt test` passes (if using dbt)
- `mxcp lint` shows no critical issues
- Manual verification confirms expected behavior

**Never skip validation or testing steps.**

## Testing Requirements

**MXCP endpoint tests must verify:**
- ✓ Correct results for valid inputs
- ✓ Edge cases (empty data, nulls, boundaries)
- ✓ Error handling for invalid inputs
- ✓ Query logic produces expected output

**dbt data tests must verify:**
- ✓ Required columns are `not_null`
- ✓ Primary keys are `unique`
- ✓ Foreign keys have valid `relationships`
- ✓ Data values are within expected ranges (`accepted_values`)

Example dbt schema tests:
```yaml
# models/schema.yml
models:
  - name: customers
    columns:
      - name: id
        tests: [not_null, unique]
      - name: email
        tests: [not_null, unique]
      - name: status
        tests:
          - accepted_values:
              values: ['active', 'inactive', 'pending']
```

Example MXCP endpoint tests with edge cases:
```yaml
tests:
  - name: valid_user
    arguments: [{key: user_id, value: 1}]
    result_contains: {id: 1}
  - name: user_not_found
    arguments: [{key: user_id, value: 99999}]
    result: null
  - name: handles_zero
    arguments: [{key: user_id, value: 0}]
    result: null
```

## Critical: Use the Default Database

**MXCP automatically creates and manages a DuckDB database.** Do not configure a custom database path unless the user explicitly asks for it.

When you run `mxcp init`, MXCP creates:
- Database at `data/db-default.duckdb` (or `data/db-{profile}.duckdb`)
- All tables, seeds, and dbt models go into this database automatically

**Use the default (no database configuration needed):**
```yaml
# mxcp-site.yml - Minimal config
mxcp: 1
project: my-project
profile: default
# Database is automatically created at data/db-default.duckdb
```

**Only configure `duckdb.path` if the user explicitly requests it** (e.g., shared database, specific location, read-only mode). Do not proactively add database configuration.

## Critical: Prefer Python Models Over CSV Seeds

**For Excel files and external data, use dbt Python models instead of converting to CSV seeds.**

**WRONG approach:**
```bash
# Don't do this workflow:
python convert_excel_to_csv.py  # Convert Excel to CSV
# Then seed via dbt
mxcp dbt seed
```

**CORRECT approach - Use dbt Python model:**
```python
# models/load_excel.py
import pandas as pd

def model(dbt, session):
    df = pd.read_excel('data/sales.xlsx')
    df = df.dropna(how='all')
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    return df
```

Then run: `mxcp dbt run --select load_excel`

**Why Python models are better:**
- No manual conversion step
- Handles Excel formatting, multiple sheets, type issues
- Transformation logic is version-controlled
- Runs as part of the dbt DAG
- Data quality tests apply automatically

**When CSV seeds ARE appropriate:**
- Small, static reference data (country codes, config values)
- Data that rarely changes and should be in version control
- Simple tabular data without formatting issues

## Critical: Common Mistakes to Avoid

**Read this before creating any tools.** These mistakes cause validation errors:

### 1. Missing `tool:` Wrapper

```yaml
# WRONG
mxcp: 1
name: get_calendar
description: ...

# CORRECT
mxcp: 1
tool:
  name: get_calendar
  description: ...
```

### 2. Missing Parameter Description

```yaml
# WRONG - causes validation error
parameters:
  - name: user_id
    type: string

# CORRECT
parameters:
  - name: user_id
    type: string
    description: The unique user identifier
```

### 3. Invalid Type Names

Valid types: `string`, `number`, `integer`, `boolean`, `array`, `object`

```yaml
# WRONG
type: map      # Use 'object'
type: strng    # Typo
type: int      # Use 'integer'

# CORRECT
type: object
type: string
type: integer
```

### 4. Invalid Parameter Names

Parameter names must match `^[a-zA-Z_][a-zA-Z0-9_]*$`

```yaml
# WRONG
name: user-name    # Hyphens not allowed
name: 1st_param    # Can't start with number

# CORRECT
name: user_name
name: first_param
```

### 5. Invalid Format Values

Valid formats: `email`, `uri`, `date`, `time`, `date-time`, `duration`, `timestamp`

```yaml
# WRONG
format: datetime   # Missing hyphen

# CORRECT
format: date-time
```

### 6. Both `code` and `file` in Source

Source must have exactly one of `code` or `file`:

```yaml
# WRONG
source:
  code: "SELECT 1"
  file: "query.sql"  # Can't have both

# CORRECT
source:
  code: "SELECT 1"
# OR
source:
  file: ../sql/query.sql
```

## Essential Workflow

### Initialize a New Project

```bash
mkdir my-mxcp-project && cd my-mxcp-project
uv venv && source .venv/bin/activate
uv pip install mxcp
mxcp init --bootstrap
```

### Create a Tool

1. Create tool definition in `tools/my_tool.yml`:

```yaml
mxcp: 1
tool:
  name: my_tool
  description: What this tool does
  parameters:
    - name: param_name
      type: string
      description: Parameter description
  return:
    type: object
    properties:
      result:
        type: string
  source:
    file: ../sql/my_tool.sql
```

2. Create implementation in `sql/my_tool.sql`:

```sql
SELECT $param_name as result
```

3. Validate immediately:

```bash
mxcp validate
```

### Validation-First Development

**Always validate after each change:**

```bash
# 1. Create tool YAML
mxcp validate  # Fix errors now

# 2. Create implementation
mxcp validate  # Validate again

# 3. Add tests
mxcp test      # Run tests

# 4. Check metadata quality
mxcp lint
```

### Run and Test

```bash
# Run a tool manually
mxcp run tool my_tool --param param_name=value

# Run all tests
mxcp test

# Start the server
mxcp serve
```

## Project Structure

```
mxcp-project/
├── mxcp-site.yml       # Project configuration (required)
├── tools/              # Tool definitions (.yml)
├── resources/          # Resource definitions (.yml)
├── prompts/            # Prompt definitions (.yml)
├── sql/                # SQL implementations
├── python/             # Python implementations
├── evals/              # LLM evaluation tests
└── data/               # Database files (db-default.duckdb)
```

**Directory rules:**
- Tools MUST be in `tools/*.yml`
- Resources MUST be in `resources/*.yml`
- Prompts MUST be in `prompts/*.yml`
- SQL files in `sql/`, referenced via relative paths
- Python files in `python/`, referenced via relative paths

## SQL vs Python Tools

**Use SQL for:**
- Database queries
- Data aggregations
- Simple transformations

**Use Python for:**
- Complex business logic
- External API calls
- ML model inference
- File processing

### SQL Tool Example

```yaml
mxcp: 1
tool:
  name: get_user
  description: Get user by ID
  parameters:
    - name: user_id
      type: integer
      description: User ID
  return:
    type: object
  source:
    code: |
      SELECT id, name, email
      FROM users
      WHERE id = $user_id
```

### Python Tool Example

```yaml
mxcp: 1
tool:
  name: analyze_data
  description: Analyze data with Python
  language: python
  parameters:
    - name: dataset
      type: string
      description: Dataset name
  return:
    type: object
  source:
    file: ../python/analysis.py
```

```python
# python/analysis.py
from mxcp.runtime import db

def analyze_data(dataset: str) -> dict:
    # Use validated table names or query specific tables
    allowed_tables = {"users", "orders", "products"}
    if dataset not in allowed_tables:
        return {"error": f"Unknown dataset: {dataset}"}

    # Table names can't be parameterized - use validated string
    results = db.execute(f"SELECT * FROM {dataset}")
    return {"count": len(results), "data": results}
```

## Security Features

For security implementation details, see:
- [Policies](references/security/policies.md) - Access control with CEL expressions
- [Authentication](references/security/authentication.md) - OAuth setup (GitHub, Google, etc.)
- [Auditing](references/security/auditing.md) - Operation tracking

## CLI Quick Reference

```bash
# Project
mxcp init --bootstrap        # Create new project
mxcp list                    # List all endpoints

# Quality
mxcp validate                # Check structure
mxcp test                    # Run tests
mxcp lint                    # Check metadata
mxcp evals                   # AI behavior tests

# Running
mxcp serve                   # Start MCP server
mxcp run tool NAME --param k=v   # Run tool manually

# Database
mxcp query "SELECT 1"        # Execute SQL

# Operations
mxcp drift-snapshot          # Create baseline
mxcp drift-check             # Detect changes
mxcp log --since 1h          # Query audit logs
```

## Troubleshooting

```bash
mxcp validate --debug        # Detailed validation errors
mxcp run tool NAME --debug   # Debug tool execution
mxcp list                    # See available endpoints
```

Common issues: YAML syntax, missing required fields, invalid types, file paths.

## Project Templates

Complete runnable examples in `assets/project-templates/`. Start with:
- `python-demo` - Python endpoint patterns
- `covid_owid` - Data workflow with dbt

```bash
cp -r assets/project-templates/python-demo my-project
cd my-project
mxcp validate && mxcp test
```

See [Configuration](references/operations/configuration.md) for mxcp-site.yml and config.yml options.
