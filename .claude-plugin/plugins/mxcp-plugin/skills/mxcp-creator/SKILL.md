---
name: mxcp-creator
description: This skill should be used when users want to create, build, initialize, or set up MXCP servers or projects. MXCP is an enterprise-grade MCP (Model Context Protocol) framework for building production AI applications with SQL and Python endpoints, security, audit trails, policy enforcement, and comprehensive testing. Also use this skill for configuring MCP tools/resources/prompts, implementing endpoints, setting up authentication/policies, or troubleshooting MXCP applications.
---

# MXCP: Enterprise MCP Framework

MXCP is an enterprise-grade MCP (Model Context Protocol) framework for building production AI applications with SQL and Python. This skill provides comprehensive guidance for working with MXCP projects.

## Scope: Technical Implementation Only

This skill focuses on **how to implement** MCP servers using MXCP, not **what to implement**.

**In Scope**:
- Choosing technical approaches (SQL vs Python, OAuth vs token auth)
- Implementing endpoints, authentication, policies
- Testing, validation, debugging
- Security and robustness patterns

**Out of Scope**:
- Defining business requirements or use cases
- Determining what features the MCP server should provide
- Business logic design decisions

**When user needs are unclear technically**: Ask clarifying questions about data sources, authentication, access patterns.

**When user needs are unclear functionally**: Ask the user to clarify their business requirements before proceeding.

## Quick Reference

**When to use this skill:**
- Creating or initializing MXCP projects
- Defining MCP tools, resources, or prompts
- Implementing SQL queries or Python endpoints
- Configuring authentication, policies, or audit logging
- Setting up dbt integration for data transformation
- Testing, validating, or debugging MXCP endpoints
- Deploying MXCP servers to production

**New to MXCP? Quick navigation:**
- **First time?** → See [Getting Started](#getting-started) for project initialization
- **Learning by example?** → See [Project Templates](#working-with-project-templates) (14 complete examples)
- **Building Python tools?** → Copy `assets/project-templates/python-demo/`
- **Working with CSV data?** → Copy `assets/project-templates/covid_owid/`
- **Need OAuth integration?** → Copy `assets/project-templates/google-calendar/`
- **Stuck on an error?** → See **references/debugging-guide.md**
- **Need YAML validation?** → Use `python scripts/validate_yaml.py` (see [YAML Schema Validation](#yaml-schema-validation))

## ⚠️ COMMON MISTAKES TO AVOID

**READ THIS BEFORE CREATING ANY TOOLS** - These mistakes cause validation errors:

### 1. Wrong Tool Definition Structure

❌ **WRONG** (Missing `tool:` wrapper):
```yaml
mxcp: 1
name: get_calendar
description: ...
language: python
```

✅ **CORRECT**:
```yaml
mxcp: 1
tool:
  name: get_calendar
  description: ...
  language: python
```

**Fix**: Always add `tool:` as a top-level key after `mxcp: 1`.

### 2. Using `type:` Instead of `language:` for Python Tools

❌ **WRONG**:
```yaml
tool:
  name: my_tool
  type: python  # ❌ Wrong field name
```

✅ **CORRECT**:
```yaml
tool:
  name: my_tool
  language: python  # ✅ Correct for Python tools
```

**Fix**: Use `language: python` for Python tools. Use `type: sql` for SQL tools.

### 3. Misusing the `required:` Field

❌ **WRONG** (Will cause validation error):
```yaml
parameters:
  - name: ticker
    type: string
    required: true  # ❌ Causes: "True is not of type 'array'"
```

❌ **ALSO WRONG**:
```yaml
parameters:
  - name: city
    type: string
    required: false  # ❌ Not valid syntax
```

✅ **CORRECT** (Required parameter):
```yaml
parameters:
  - name: ticker
    type: string
    description: "Stock ticker symbol"
    # No default = required by default
```

✅ **CORRECT** (Optional parameter):
```yaml
parameters:
  - name: city
    type: string
    description: "Filter by city (optional)"
    default: null  # Makes it optional
```

✅ **CORRECT** (Optional with specific default):
```yaml
parameters:
  - name: limit
    type: integer
    description: "Maximum results"
    default: 100  # Optional, defaults to 100
```

**Fix**:
- For required parameters: Don't add `required:` field at all
- For optional parameters: Add `default: null` or `default: <value>`

### 4. Not Validating Early Enough

❌ **WRONG** (Creating multiple tools before validating):
```bash
# Create tool1.yml
# Create tool2.yml
# Create tool3.yml
# Create tool4.yml
mxcp validate  # ❌ Now you have errors in 4 files!
```

✅ **CORRECT** (Validate after EACH tool):
```bash
# Create tool1.yml
mxcp validate  # ✅ Fix errors NOW
# Create tool2.yml
mxcp validate  # ✅ Fix errors NOW
# Continue...
```

**Fix**: Run `mxcp validate` immediately after creating EACH tool definition.

### 5. Not Reading Examples First

❌ **WRONG**: Creating YAML from scratch based on assumptions.

✅ **CORRECT**:
1. Read **references/minimal-working-examples.md** FIRST
2. Copy a working example
3. Modify incrementally
4. Validate after each change

## Before You Start: Mandatory Checklist

**Before creating ANY tool, complete this checklist in order:**

- [ ] 1. Read **references/minimal-working-examples.md** to see working examples
- [ ] 2. Identify which example is closest to the use case
- [ ] 3. Copy the relevant example as a starting point
- [ ] 4. Review the tool template below
- [ ] 5. Modify the copied example incrementally
- [ ] 6. Validate after EACH change

**DO NOT skip this checklist. DO NOT create YAML from scratch.**

## Quick Start: Tool Templates

**Copy these templates to avoid syntax errors:**

### Python Tool Template

```yaml
mxcp: 1
tool:
  name: YOUR_TOOL_NAME
  description: |
    Clear description of what this tool does and when to use it.
    Explain the purpose and expected behavior.
  language: python
  parameters:
    # Required parameter (no default)
    - name: required_param
      type: string
      description: "What this parameter is for"

    # Optional parameter (with null default)
    - name: optional_param
      type: string
      description: "What this optional parameter is for"
      default: null

    # Optional parameter (with specific default)
    - name: limit
      type: integer
      description: "Maximum number of results"
      default: 100
  return:
    type: object
    description: "Description of what gets returned"
    properties:
      status: { type: string, description: "Operation status" }
      data: { type: array, description: "Result data" }
  source:
    file: ../python/your_module.py
  tests:
    - name: "basic_test"
      arguments:
        - key: required_param
          value: "test_value"
      result:
        status: "success"
```

**After copying this template:**
1. Replace `YOUR_TOOL_NAME` with the actual tool name
2. Update the `description` to explain what the tool does
3. Update the `parameters` section
4. Update the `return` type
5. Update the `source.file` path
6. 🛑 **RUN `mxcp validate` IMMEDIATELY** 🛑

### SQL Tool Template

```yaml
mxcp: 1
tool:
  name: YOUR_TOOL_NAME
  description: |
    Clear description of what this SQL query does.
  parameters:
    - name: filter_value
      type: string
      description: "Filter criteria (optional)"
      default: null
  return:
    type: array
    items:
      type: object
      properties:
        id: { type: integer }
        name: { type: string }
  source:
    code: |
      SELECT
        id,
        name,
        other_column
      FROM your_table
      WHERE $filter_value IS NULL OR column = $filter_value
      ORDER BY id
      LIMIT 100
  tests:
    - name: "test_query"
      arguments: []
      # Add expected results if known
```

**After copying this template:**
1. Replace `YOUR_TOOL_NAME` with the actual tool name
2. Update the SQL query in `source.code`
3. Update parameters and return types
4. 🛑 **RUN `mxcp validate` IMMEDIATELY** 🛑

## Core Principles

**ALWAYS prioritize in this order:**

1. **Security** - Authentication, authorization, input validation, parameterized queries
2. **Robustness** - Error handling, type validation, data quality checks
3. **Validity** - Structure validation, schema compliance, type safety
4. **Testability** - Test cases, validation scripts, lint checks
5. **Testing** - Run validate/test/lint before deployment
6. **Features** - Implement requested functionality based on user needs

## Mandatory Build Workflow

**CRITICAL: Follow this exact workflow to ensure correctness**

🚨 **DO NOT create multiple tools before validating the first one!** 🚨

### Step-by-Step Process

1. **Create ONE tool definition YAML** (e.g., `tools/my_tool.yml`)
2. 🛑 **STOP! Run `mxcp validate` RIGHT NOW** 🛑
3. **Fix ALL validation errors before proceeding**
4. **Create Python implementation** (if needed, e.g., `python/my_service.py`)
5. 🛑 **STOP! Run `mxcp validate` AGAIN** 🛑
6. **Add tests to the tool YAML** (in `tests:` section)
7. **Run `mxcp test` to verify functionality**
8. **Manual verification**: `mxcp run tool <name>`
9. **Only after ALL checks pass**, create the next tool

### Correct Workflow Example

```bash
# Create first tool
cat > tools/tool1.yml <<EOF
mxcp: 1
tool:
  name: tool1
  ...
EOF

# VALIDATE IMMEDIATELY
mxcp validate  # ← Must pass before continuing!

# Create Python code (if needed)
cat > python/service1.py <<EOF
...
EOF

# VALIDATE AGAIN
mxcp validate  # ← Must pass before continuing!

# Test
mxcp test

# Now create second tool
cat > tools/tool2.yml <<EOF
...
EOF

# VALIDATE IMMEDIATELY
mxcp validate  # ← Always validate after each tool!
```

**Definition of Done**:
- [ ] Virtual environment created with `uv venv`
- [ ] Dependencies installed: `uv pip install mxcp black pyright pytest pytest-asyncio pytest-httpx pytest-cov`
- [ ] `mxcp validate` passes (no errors)
- [ ] `mxcp test` passes (MXCP integration tests)
- [ ] **Python code formatted**: `black python/` passes (if Python code exists)
- [ ] **Type checking passes**: `pyright python/` passes (if Python code exists)
- [ ] `pytest tests/` passes (Python unit tests, if applicable)
- [ ] `dbt test` passes (if using dbt)
- [ ] **Result correctness verified** (tests check actual values)
- [ ] **External calls mocked** (if Python tools use APIs)
- [ ] **Concurrency safe** (Python tools avoid race conditions)
- [ ] **Documentation quality verified** (LLMs can understand with zero context)
- [ ] **Error handling implemented** (Python tools return structured errors)
- [ ] Manual test succeeds with real data
- [ ] Security checklist completed
- [ ] Config.yml provided with instructions

**Two types of tests required**:
1. **MXCP tests** (in YAML `tests:` section) - Integration testing
2. **Python unit tests** (pytest in `tests/` directory) - Isolation testing with mocking

See:
- **references/comprehensive-testing-guide.md** for complete testing strategy
- **references/build-and-validate-workflow.md** for mandatory workflow

**If ANY check fails, the project is NOT done. Fix until all pass.**

## Configuration Policy

**CRITICAL: NEVER edit `~/.mxcp/config.yml`**

**ALWAYS create project-local `config.yml` instead:**

- ✅ **DO**: Create `config.yml` in project directory
- ✅ **DO**: Use environment variables for secrets
- ✅ **DO**: Provide instructions for user to copy to `~/.mxcp/` if they want
- ❌ **DON'T**: Edit or modify `~/.mxcp/config.yml`
- ❌ **DON'T**: Assume location of user's global config

**Reasoning**:
- User maintains control over their global configuration
- Project remains self-contained and portable
- Safer for automated agents
- User can review before integrating into global config

See **references/project-selection-guide.md** (Configuration Management section) for complete details.

## Core Concepts

### What is MXCP?

MXCP provides a **structured methodology** for building production MCP servers:

1. **Data Quality First**: Start with dbt models and data contracts
2. **Service Design**: Define types, security policies, and API contracts
3. **Smart Implementation**: Choose SQL for data, Python for logic
4. **Quality Assurance**: Validate, test, lint, and evaluate
5. **Production Operations**: Monitor drift, track audits, ensure performance

### Implementation Languages

- **SQL**: Best for data queries, aggregations, joins, filtering
- **Python**: Best for complex logic, ML models, API calls, async operations
- **Both**: Can be combined in the same project

### Project Structure

**CRITICAL: MXCP enforces this directory structure. Files in wrong directories are ignored.**

```
mxcp-project/
├── mxcp-site.yml       # Project configuration (required)
├── tools/              # MCP tool definitions (.yml) - MUST be here
├── resources/          # MCP resource definitions (.yml) - MUST be here
├── prompts/            # MCP prompt definitions (.yml) - MUST be here
├── evals/              # LLM evaluation tests (.yml)
├── python/             # Python endpoints and shared code
├── plugins/            # MXCP plugins for DuckDB
├── sql/                # SQL implementation files
├── drift/              # Drift detection snapshots
├── audit/              # Audit logs (when enabled)
├── models/             # dbt models (optional)
└── target/             # dbt target directory (optional)
```

**Directory Rules**:
- Tools MUST be in `tools/*.yml` (not in root or other directories)
- Resources MUST be in `resources/*.yml`
- Prompts MUST be in `prompts/*.yml`
- SQL implementations should be in `sql/*.sql` and referenced via relative paths
- Use `mxcp init --bootstrap` to create proper structure

## Decision Framework

**When building MXCP servers, follow this decision tree:**

### Step 1: Understand the Technical Requirements

**If technical details are unclear**, ask clarifying questions about implementation:
- What type of data source? (CSV, API, database, etc.)
- Authentication mechanism? (OAuth, token, none)
- Access control needs? (public, role-based, user-specific)
- Data sensitivity? (PII, credentials, financial)

**Important**: These questions clarify the **technical implementation approach**, not the business requirements. If the user's functional requirements are unclear (e.g., "what should this tool do?"), ask them to clarify their business needs first.

**If no interaction available**, use technical heuristics from **references/project-selection-guide.md**

### Step 2: Select Approach

Consult **references/project-selection-guide.md** for:
- Decision tree based on data source type
- Template selection (if applicable)
- Implementation patterns
- Security requirements

### Step 3: Common Patterns & Templates

**CSV File → MCP Server**:
- **Template**: `assets/project-templates/covid_owid/` (complete CSV + dbt example)
- **Steps**:
  1. Place CSV in `seeds/` directory
  2. Create `seeds/schema.yml` with column definitions and tests
  3. Run `dbt seed` to load into DuckDB
  4. Create SQL tool with `SELECT * FROM <table>`
  5. Add parameters for filtering/pagination
  6. Test with `dbt test` and `mxcp test`

**API Integration → MCP Server**:
- **Templates**:
  - OAuth: `google-calendar/`, `jira-oauth/`, `salesforce-oauth/`
  - Token: `jira/`, `salesforce/`, `confluence/`
  - SSO: `keycloak/`
- **Steps**:
  1. Check `assets/project-templates/` for matching template
  2. If found: copy template, adapt configuration
  3. If not found: use `python-demo/` template as base
  4. Implement authentication (OAuth/token)
  5. Create Python tools for API operations
  6. Add error handling and retries

**Python Tools → MCP Server**:
- **Template**: `assets/project-templates/python-demo/` (START HERE)
- **Steps**:
  1. Copy python-demo template
  2. Review example tools: `analyze_numbers`, `create_sample_data`, `process_time_series`
  3. Adapt Python functions in `python/` directory
  4. Update tool definitions in `tools/`
  5. Follow Python development workflow (black → pyright → pytest)

**Database → MCP Server**:
- **Approach 1 - Direct Query** (real-time data):
  1. Use DuckDB `ATTACH` with PostgreSQL, MySQL, SQLite, SQL Server
  2. Create SQL tools with `ATTACH IF NOT EXISTS` in tool definition
  3. Store credentials in environment variables (config.yml)
  4. Use read-only database users for security
  5. Add parameterized queries (`$param`) to prevent SQL injection

- **Approach 2 - Cached Data** (fast queries, dbt):
  1. Define external database as dbt source
  2. Create dbt model to materialize/cache data in DuckDB
  3. Run `dbt run` to fetch and cache data
  4. Run `dbt test` for data quality validation
  5. Create MXCP tools to query cached data (very fast)
  6. Create refresh tool to update cache periodically

- **Examples**:
  - **minimal-working-examples.md** - Example 6 (PostgreSQL direct), Example 7 (dbt cache)
  - **references/database-connections.md** - Complete guide with all databases

**See**:
- [Project Templates](#working-with-project-templates) for all 14 templates
- **references/project-selection-guide.md** for complete decision tree
- **references/database-connections.md** for database connection patterns

## Getting Started

### Initialize a New Project

**CRITICAL: Always use `uv` for Python environment management.**

```bash
# 1. Create project directory
mkdir my-mxcp-project && cd my-mxcp-project

# 2. Create virtual environment with uv
uv venv

# 3. Activate virtual environment
source .venv/bin/activate  # On Unix/macOS
# OR
.venv\Scripts\activate     # On Windows

# 4. Install MXCP and development tools
uv pip install mxcp black pyright pytest pytest-asyncio pytest-httpx pytest-cov

# 5. Initialize MXCP project
mxcp init --bootstrap

# This creates:
# - mxcp-site.yml with default config
# - Organized directory structure
# - Example hello-world endpoints (SQL + Python)
# - server_config.json for Claude Desktop

# 6. Clean up example files (recommended)
# The bootstrap creates hello-world examples for learning, but should be removed for production projects
rm tools/hello_world.yml
rm sql/hello_world.sql
```

### Python Development Workflow

**ALWAYS follow this workflow when working with Python code:**

```bash
# 1. Activate virtual environment (if not already active)
source .venv/bin/activate

# 2. After creating/editing Python files, format with black
black python/

# 3. Run type checker
pyright python/

# 4. Run unit tests
pytest tests/ -v

# 5. Only after all checks pass, proceed
```

**Mandatory tooling**:
- **uv**: Virtual environment and package management
- **black**: Code formatting (run after every edit)
- **pyright**: Type checking (run after every edit)
- **pytest**: Unit testing with coverage

### Start the Server

**ALWAYS activate virtual environment before running MXCP commands:**

```bash
# Activate environment first
source .venv/bin/activate

# Start with stdio transport (for Claude Desktop)
mxcp serve

# Start with HTTP transport
mxcp serve --transport http --port 8080

# Use specific profile
mxcp serve --profile production
```

## Working with Project Templates

MXCP provides 14 complete, runnable project templates in `assets/project-templates/` for common integration scenarios. Each template includes complete tool definitions, Python implementations, configuration examples, and comprehensive READMEs.

### Quick Start Templates

**New to MXCP? Start with one of these:**

1. **`python-demo`** - Python endpoint patterns (START HERE for Python tools)
   - Features: sync/async functions, database access, statistical analysis
   - Best for: Learning Python endpoint development
   - README: 58 lines with running examples

2. **`covid_owid`** - CSV data workflow with dbt (START HERE for data projects)
   - Features: CSV loading, dbt models, SQL queries, data quality tests
   - Best for: Learning data ingestion and transformation
   - README: 149 lines with complete workflow

### Templates by Use Case

**Data Integration**:
- **`covid_owid`** - CSV + dbt workflow with external data caching
- **`earthquakes`** - External API data fetching and caching (138-line README)

**OAuth & API Integrations**:
- **`google-calendar`** - Google OAuth2 flow with calendar operations (213-line README)
- **`jira-oauth`** - Jira with OAuth authentication (160-line README)
- **`salesforce-oauth`** - Salesforce OAuth integration (184-line README)

**Token-Based API Integrations**:
- **`jira`** - Jira API with token authentication (144-line README)
- **`salesforce`** - Salesforce with token auth (111-line README)
- **`confluence`** - Confluence API integration (152-line README)

**Enterprise Authentication**:
- **`keycloak`** - SSO integration with Keycloak (75-line README)

**Advanced Use Cases**:
- **`plugin`** - DuckDB plugin development (82-line README)
- **`python-demo`** - Advanced Python patterns and database operations

### How to Use Templates

1. **Choose template** based on use case above or see **references/project-selection-guide.md**

2. **Copy template** to your workspace:
   ```bash
   # Example: Copy Google Calendar template
   cp -r assets/project-templates/google-calendar my-calendar-project
   cd my-calendar-project
   ```

3. **Set up environment**:
   ```bash
   # Create virtual environment
   uv venv
   source .venv/bin/activate

   # Install dependencies
   uv pip install mxcp black pyright pytest pytest-asyncio pytest-httpx pytest-cov
   ```

4. **Read the template README**:
   ```bash
   cat README.md  # Every template has comprehensive setup instructions
   ```

5. **Customize configuration**:
   - Update `mxcp-site.yml` with your project name
   - Create `config.yml` in project directory for authentication/secrets (NOT `~/.mxcp/config.yml`)
   - Modify tool definitions for your specific use case
   - Update Python code if needed

6. **Test and validate**:
   ```bash
   mxcp validate
   mxcp test
   mxcp serve
   ```

### When NOT to Use Templates

- **Simple CSV queries** → Create minimal project with `mxcp init --bootstrap` + dbt seeds
- **Unique API requirements** → Start from scratch or adapt `python-demo` template
- **Learning MXCP basics** → Use minimal-working-examples.md first, then explore templates

### Template Structure

Each template is a complete MXCP project:
```
template-name/
├── README.md           # Setup instructions and usage examples
├── mxcp-site.yml       # Project configuration
├── config.yml          # Authentication/secrets configuration
├── tools/*.yml         # Tool definitions
├── python/*.py         # Python implementations (if applicable)
├── seeds/*.csv         # Data files (if applicable)
└── models/*.sql        # dbt models (if applicable)
```

**All templates are immediately runnable** - copy, configure credentials, and use.

See **references/project-selection-guide.md** for decision tree and detailed template selection guidance.

## Creating Endpoints

**Two types of tools:**

1. **Custom SQL/Python Tools** - Defined in `tools/*.yml` for specific use cases
2. **Generic SQL Tools** - Built-in tools (`list_tables`, `get_table_schema`, `execute_sql_query`) that allow LLMs to explore and query databases dynamically

**Enable generic SQL tools** for natural language data exploration:
```yaml
# mxcp-site.yml
sql_tools:
  enabled: true
```

**Important**: Generic SQL tools (`list_tables`, `get_table_schema`, `execute_sql_query`) are only available when the MCP server is running via `mxcp serve`. They **cannot** be tested using `mxcp run tool <name>` because they are dynamically generated at runtime and don't exist as static tool definitions in the `tools/` directory.

To test generic SQL tools:
```bash
# Start the server
mxcp serve

# Connect from Claude Desktop or another MCP client
# The generic SQL tools will be available in the tool list
```

See **assets/project-templates/covid_owid/** for complete example and **references/cli-reference.md** for security considerations.

For detailed examples and patterns, see:
- **references/endpoint-patterns.md** - Tool, resource, and prompt examples
- **references/python-api.md** - Python runtime API and patterns

## Enterprise Features

### Policy Enforcement

Control access and filter data using policies:

```yaml
policies:
  input:
    - condition: "!('hr.read' in user.permissions)"
      action: deny
      reason: "Missing HR read permission"
  output:
    - condition: "user.role != 'hr_manager'"
      action: filter_fields
      fields: ["salary", "ssn"]
```

See **references/policies.md** for comprehensive policy examples.

### Audit Logging

Enable audit trails for compliance:

```yaml
# In mxcp-site.yml
profiles:
  production:
    audit:
      enabled: true
      path: audit-logs.jsonl
```

Query logs:
```bash
mxcp log --since 1h --tool employee_data
mxcp log --export-duckdb audit.db
```

### OpenTelemetry (Distributed Tracing)

Enable production observability with OpenTelemetry:

```yaml
# In mxcp-site.yml
profiles:
  production:
    telemetry:
      enabled: true
      endpoint: "http://otel-collector:4318"
```

This provides:
- Distributed tracing across your MXCP server and dependencies
- Performance metrics and monitoring
- Integration with observability platforms (Jaeger, Grafana, etc.)

### Authentication

Configure OAuth providers in project-local `config.yml`:

```yaml
# config.yml (in project directory)
mxcp: 1

profiles:
  default:
    auth:
      provider: github
      # OAuth credentials configured here or via environment variables
    secrets:
      - name: api_token
        type: env
        parameters:
          env_var: API_TOKEN

  production:
    auth:
      provider: github
```

**Usage**:
```bash
# Option 1: Use config from project directory
mxcp serve  # Automatically finds ./config.yml

# Option 2: Specify config location
MXCP_CONFIG=./config.yml mxcp serve

# Option 3: User can manually copy to ~/.mxcp/ if preferred
cp config.yml ~/.mxcp/
```

## dbt Integration

**dbt creates the tables → MXCP queries them**

Combine dbt transformations with MXCP endpoints:

1. **For CSV files**: Use dbt seeds to load data with schema validation
2. **For transformations**: Create dbt models to transform data
3. **Run dbt**: Execute `dbt seed` and `dbt run` to materialize tables
4. **Query from MXCP**: Create tools that query dbt tables

**Essential dbt concepts for MXCP:**
- **Seeds** - CSV files loaded as tables (best for user-provided data)
- **Models** - SQL transformations that create new tables/views
- **Schema.yml** - ALWAYS create for seeds and models (defines types, tests, docs)
- **Tests** - Data quality validation (unique, not_null, etc.)

**Example workflow (CSV → MCP tool)**:
```bash
# 1. Place CSV in seeds/
cp user_data.csv seeds/

# 2. Create seeds/schema.yml
cat > seeds/schema.yml <<EOF
version: 2
seeds:
  - name: user_data
    columns:
      - name: id
        tests: [unique, not_null]
      - name: email
        tests: [not_null]
EOF

# 3. Load seed
dbt seed

# 4. Test data quality
dbt test

# 5. Create MXCP tool to query
# tools/get_users.yml
# source: SELECT * FROM user_data WHERE id = $user_id
```

See:
- **references/dbt-core-guide.md** - Essential dbt knowledge for MXCP (MUST READ for CSV/data projects)
- **references/dbt-patterns.md** - Advanced dbt integration patterns
- **references/duckdb-essentials.md** - DuckDB features and SQL extensions

## Agent-Centric Design

**CRITICAL: Design tools that LLMs can effectively use to accomplish real-world tasks.**

LLMs are your primary users. Your tools must enable LLMs to complete workflows with minimal tool calls and maximum effectiveness.

### Core Design Principles

1. **Build for Workflows, Not Just Data Access**
   - Don't just expose database tables - design tools around complete workflows
   - Consolidate related operations (e.g., get user + orders + analytics in one tool)
   - Example: `get_customer_purchase_summary` vs separate `get_customer` + `get_orders`

2. **Optimize for Limited Context**
   - LLMs have constrained context windows - make every token count
   - Provide `detail_level` options: minimal, standard, full
   - Default to human-readable identifiers (names, not just IDs)
   - Return high-signal information, not exhaustive data dumps

3. **Design Actionable Error Messages**
   - Error messages should guide LLMs toward correct usage
   - Suggest specific next steps: "Try using filter='active' to reduce results"
   - Include `suggestion` field in error responses

4. **Follow Natural Task Subdivisions**
   - Tool names reflect how humans think about tasks
   - Use consistent prefixes: `get_customer_*`, `analyze_sales_*`
   - Group related tools for discoverability

5. **Provide Response Format Options**
   - Support different detail levels based on LLM needs
   - Include display names alongside IDs
   - Use human-readable dates, not epoch timestamps
   - Omit verbose internal metadata

See **references/agent-centric-design.md** for complete design patterns and examples.

## Documentation Quality

**CRITICAL: Tools must be self-documenting for LLMs with zero prior context.**

LLMs connecting to MXCP servers have NO knowledge about your domain, data, or tools. The documentation YOU provide is their ONLY guide.

**Documentation requirements**:
- **Tool descriptions**: Explain WHAT it does, WHAT it returns, WHEN to use it
- **Parameter descriptions**: Document valid values, formats, examples, defaults
- **Return type descriptions**: Describe every field in the response
- **Cross-references**: Mention related tools for chaining operations
- **Error cases**: Document expected errors and what they mean

**Example of good documentation**:
```yaml
tool:
  name: get_customer_orders
  description: "Retrieve all orders for a specific customer by customer ID. Returns order history including order date, total amount, status, and items. Use this to answer questions about a customer's purchase history or order status."
  parameters:
    - name: customer_id
      type: string
      description: "Unique customer identifier (e.g., 'CUST_12345'). Found in customer records or from list_customers tool."
      required: true
      examples: ["CUST_12345", "CUST_98765"]
  return:
    type: array
    items:
      type: object
      properties:
        order_id: { type: string, description: "Unique order identifier" }
        total_amount: { type: number, description: "Total order value in USD" }
```

See **references/llm-friendly-documentation.md** for complete documentation guidelines.

## Error Handling

**Python Error Handling (YOU must handle)**:
- External API failures
- Invalid input validation
- Resource not found errors
- Business logic errors
- Async/await errors

**SQL Error Handling (MXCP manages automatically)**:
- SQL syntax errors
- Type mismatches
- Parameter binding errors
- Database connection errors

**Python error pattern - ALWAYS return structured errors**:
```python
async def fetch_user(user_id: int) -> dict:
    try:
        response = await client.get(f"https://api.example.com/users/{user_id}")

        if response.status_code == 404:
            return {
                "success": False,
                "error": f"User with ID {user_id} not found",
                "error_code": "NOT_FOUND",
                "user_id": user_id
            }

        return {"success": True, "user": response.json()}

    except httpx.TimeoutException:
        return {
            "success": False,
            "error": "Request timed out after 10 seconds.",
            "error_code": "TIMEOUT"
        }
```

**Error message principles**:
1. Be specific (exactly what went wrong)
2. Be actionable (suggest what to do next)
3. Provide context (relevant values/IDs)
4. Use plain language (avoid technical jargon)

See **references/error-handling-guide.md** for comprehensive error handling patterns.

## Quality Assurance

**ALWAYS run quality checks before deployment:**

```bash
# 1. Structure validation
mxcp validate              # Check YAML structure, types, required fields

# 2. Functional testing
mxcp test                  # Run all test cases
mxcp test tool <name>      # Test specific tool

# 3. Data quality (if using dbt)
dbt test                   # Run dbt data quality tests
dbt test --select <model>  # Test specific model

# 4. Metadata quality
mxcp lint                  # Check descriptions, improve documentation

# 5. LLM behavior testing
mxcp evals                 # Test how LLMs interact with tools
mxcp evals suite_name      # Test specific eval suite
```

### YAML Schema Validation

**JSON Schema Specifications for MXCP Files**

The `assets/schemas/` directory contains JSON Schema files that define the exact structure and validation rules for all MXCP YAML files:

- **mxcp-site-schema-1.json** - Validates `mxcp-site.yml` project configuration
- **mxcp-config-schema-1.json** - Validates `config.yml` authentication and secrets
- **tool-schema-1.json** - Validates tool definitions in `tools/*.yml`
- **resource-schema-1.json** - Validates resource definitions in `resources/*.yml`
- **prompt-schema-1.json** - Validates prompt definitions in `prompts/*.yml`
- **eval-schema-1.json** - Validates evaluation suites in `evals/*.yml`
- **common-types-schema-1.json** - Common type definitions used by other schemas

**When to use schema validation:**

1. **During development** - Validate YAML files as you create them to catch structure errors early
2. **Before committing** - Ensure all configuration files are valid before version control
3. **In CI/CD pipelines** - Automate validation as part of your build process
4. **When debugging** - Get detailed error messages about invalid YAML structure

**Using the validation script:**

```bash
# Validate a single YAML file
python scripts/validate_yaml.py path/to/file.yml

# Validate all MXCP YAML files in project templates
python scripts/validate_yaml.py --all

# Example output:
# ✓ assets/project-templates/jira/tools/get_issue.yml
# ✗ assets/project-templates/custom/tools/bad_tool.yml
#   Error: At tool -> parameters -> 0: 'type' is a required property
```

**How this differs from `mxcp validate`:**

- **Schema validation** (`scripts/validate_yaml.py`) - Checks YAML structure and syntax against JSON schemas (fast, no MXCP installation needed)
- **MXCP validation** (`mxcp validate`) - Full validation including SQL syntax, Python imports, parameter types, and business logic (requires MXCP)

**Best practice**: Use schema validation first for quick feedback, then run `mxcp validate` for comprehensive checks.

### Creating Effective Evaluations

**Evaluations are the ultimate quality measure** - they test whether LLMs can accomplish real tasks using your tools.

**Create evaluations that**:
- Test critical workflows (most common use cases)
- Verify safety (LLMs don't call destructive operations inappropriately)
- Check policy enforcement (LLMs respect user permissions)
- Require complex multi-step tasks (dozens of tool calls)
- Use realistic prompts (how humans would ask)

**Evaluation file format**:
```yaml
# evals/customer-evals.yml
mxcp: 1
suite: customer_analysis
description: "Test LLM's ability to analyze customer data"

tests:
  - name: churn_risk_assessment
    description: "LLM should identify high churn risk customers"
    prompt: "Which customers are at risk of churning?"
    user_context:  # Optional: test policies
      role: analyst
    assertions:
      must_call:
        - tool: analyze_customer_churn_risk
      answer_contains:
        - "risk"
        - "recommend"
```

See **references/mxcp-evaluation-guide.md** for complete evaluation design guidelines.

**Security validation checklist:**
- [ ] All SQL queries use parameterized variables (`$param`)
- [ ] Authentication configured for all endpoints requiring it
- [ ] Policies defined for sensitive data access
- [ ] Secrets stored in Vault/1Password (never in code)
- [ ] Input validation on all parameters
- [ ] Audit logging enabled for production

**Robustness validation checklist:**
- [ ] Error handling in Python endpoints (try/except)
- [ ] NULL handling in SQL queries
- [ ] Type validation in all tool definitions
- [ ] Return type specifications complete
- [ ] Test cases cover edge cases (empty, null, invalid)

**Before deployment workflow:**
```bash
# Run full validation suite
mxcp validate && mxcp test && mxcp lint

# For dbt projects, also run:
dbt test

# Create drift baseline before first deployment
mxcp drift-snapshot

# Enable audit logging for production
# In mxcp-site.yml profiles.production:
#   audit:
#     enabled: true
```

For comprehensive testing guidance, see **references/testing-guide.md**.

## CLI Commands Reference

### Core Commands
- `mxcp init [--bootstrap]` - Initialize new project
- `mxcp serve` - Start MCP server
- `mxcp list` - List all endpoints
- `mxcp run tool NAME --param key=value` - Execute endpoint

### Quality Commands
- `mxcp validate` - Check structure
- `mxcp test` - Run tests
- `mxcp lint` - Check metadata
- `mxcp evals` - Test LLM behavior

### Data Commands
- `mxcp query "SQL"` - Execute SQL
- `mxcp dbt run` - Run dbt
- `mxcp drift-snapshot` - Create baseline
- `mxcp drift-check` - Detect changes

### Monitoring Commands
- `mxcp log [--since 1h]` - Query audit logs
- `mxcp log-cleanup` - Apply retention

For complete CLI documentation, see **references/cli-reference.md**.

## Troubleshooting

### Validation Error Decoder

**Understanding and fixing common `mxcp validate` errors:**

#### Error: `tool.parameters.0.required: True is not of type 'array'`

**Cause**: Used `required: true` or `required: false` in parameter definition.

**Fix**: Remove the `required:` field entirely. Parameters are required by default unless they have a `default:` field.

```yaml
# ❌ WRONG
parameters:
  - name: foo
    type: string
    required: true  # ← Remove this

# ✅ CORRECT (required parameter)
parameters:
  - name: foo
    type: string
    # No default = required

# ✅ CORRECT (optional parameter)
parameters:
  - name: foo
    type: string
    default: null  # ← Add this instead
```

#### Error: `Expected tool definition but not found`

**Cause**: Missing `tool:` wrapper key in the YAML structure.

**Fix**: Add `tool:` as a top-level key after `mxcp: 1`.

```yaml
# ❌ WRONG
mxcp: 1
name: my_tool
description: ...

# ✅ CORRECT
mxcp: 1
tool:
  name: my_tool
  description: ...
```

#### Error: `tool.language: field required` or `tool.type: field required`

**Cause**: Used wrong field name for tool type.

**Fix**:
- For Python tools: Use `language: python`
- For SQL tools: Don't specify language (SQL is implicit when using `source.code`)

```yaml
# ❌ WRONG (Python tool)
tool:
  name: my_tool
  type: python  # ← Wrong field

# ✅ CORRECT (Python tool)
tool:
  name: my_tool
  language: python  # ← Correct field
  source:
    file: ../python/my_module.py

# ✅ CORRECT (SQL tool)
tool:
  name: my_tool
  # No language field needed for SQL
  source:
    code: |
      SELECT * FROM table
```

#### Error: `tool.source: field required`

**Cause**: Missing `source:` section in tool definition.

**Fix**: Add either `source.file:` (for Python) or `source.code:` (for SQL).

```yaml
# For Python tools
tool:
  name: my_tool
  language: python
  source:
    file: ../python/my_module.py

# For SQL tools
tool:
  name: my_tool
  source:
    code: |
      SELECT * FROM table
```

#### Error: `tool.parameters.0.type: field required`

**Cause**: Missing `type:` field in parameter definition.

**Fix**: Add `type:` to every parameter (string, integer, number, boolean, array, object).

```yaml
# ❌ WRONG
parameters:
  - name: foo
    description: "..."

# ✅ CORRECT
parameters:
  - name: foo
    type: string  # ← Add type
    description: "..."
```

#### Error: `Output validation failed: Expected integer, got float`

**Cause**: DuckDB may return different numeric types than expected. For example, a query might return a `float`/`number` type even when the column logically contains integer values, or when you expect an integer result.

**Context**: This commonly occurs when:
- Using aggregate functions like `COUNT()`, `SUM()`, or `AVG()`
- Querying columns that DuckDB infers as numeric rather than integer
- Performing mathematical operations that produce floating-point results

**Fix**: Update the return type in the tool definition to match what DuckDB actually returns.

```yaml
# ❌ WRONG (causes validation error)
return:
  type: array
  items:
    type: object
    properties:
      quantity: { type: integer }  # ← DuckDB returns float

# ✅ CORRECT (matches DuckDB's actual type)
return:
  type: array
  items:
    type: object
    properties:
      quantity: { type: number }  # ← Use number for DuckDB numeric types
```

**Workflow to diagnose type mismatches**:
1. Run `mxcp test` to see which fields fail validation
2. Run the query manually with `mxcp query "SELECT ..."` to see actual return types
3. Update the return type definition to match DuckDB's actual output
4. Re-run `mxcp test` to verify

**General guidance**: When in doubt about DuckDB return types, use `number` instead of `integer` for numeric columns. DuckDB's type inference is flexible and often returns broader numeric types.

### Common Issues

**dbt models not found:**
```bash
dbt debug && dbt compile
```

**Policy errors:**
```bash
mxcp run tool my_tool --user-context '{"role": "admin"}'
```

**Database issues:**
```bash
# Check path
echo $MXCP_DUCKDB_PATH

# Use read-only mode
mxcp serve --readonly
```

**Debug mode:**
```bash
mxcp serve --debug
mxcp validate --debug
```

## Best Practices

1. **Project Structure** - Follow organized directory layout
2. **Type Safety** - Define all parameter and return types
3. **Security** - Use Vault/1Password, never commit secrets
4. **Testing** - Write tests for all endpoints
5. **Documentation** - Add descriptions, run `mxcp lint`
6. **Performance** - Use SQL for queries, Python for logic
7. **Development Workflow**:
   ```bash
   mxcp validate && mxcp test && mxcp lint  # Development
   mxcp drift-snapshot && mxcp evals        # Before deployment
   mxcp drift-check && mxcp log --since 24h # Production
   ```

## Additional Resources

### Learn by Example (Start Here!)

**Complete Project Templates** (14 runnable examples):
- **assets/project-templates/** - Copy, customize, and run
  - `python-demo/` - Python endpoint patterns (START HERE for Python)
  - `covid_owid/` - CSV + dbt workflow (START HERE for data)
  - `google-calendar/` - OAuth integration example
  - See [Project Templates](#working-with-project-templates) for all 14 templates

**Minimal Working Examples**:
- **references/minimal-working-examples.md** - Guaranteed-to-work code snippets

### Critical References (Read First)

**Workflow & Best Practices**:
- **references/build-and-validate-workflow.md** - MANDATORY workflow to ensure correctness (READ THIS!)
- **references/agent-centric-design.md** - Design tools that LLMs can effectively use (ESSENTIAL!)
- **references/llm-friendly-documentation.md** - LLM-first documentation + response formats (CRITICAL!)

**Testing & Quality**:
- **references/comprehensive-testing-guide.md** - MXCP tests + Python unit tests + mocking + concurrency
- **references/mxcp-evaluation-guide.md** - Creating effective LLM evaluations (Quality Measure!)
- **assets/schemas/** - JSON Schema definitions for YAML validation (see [YAML Schema Validation](#yaml-schema-validation))
- **scripts/validate_yaml.py** - Validation script for YAML structure checking

**Error Handling & Debugging**:
- **references/error-handling-guide.md** - Python error handling patterns (structured errors)
- **references/debugging-guide.md** - Systematic debugging workflow and troubleshooting

### Essential References (Most Projects)

**Project Planning**:
- **references/project-selection-guide.md** - Decision tree, heuristics, template selection

**Data & SQL**:
- **references/dbt-core-guide.md** - dbt essentials for MXCP (seeds, models, schema.yml)
- **references/duckdb-essentials.md** - DuckDB features, SQL extensions, best practices
- **references/database-connections.md** - Connect to PostgreSQL, MySQL, SQLite, SQL Server (NEW!)

**Python Development**:
- **references/python-development-workflow.md** - uv, black, pyright, pytest workflow
- **references/python-api.md** - Python runtime API and library wrapping patterns
- **references/endpoint-patterns.md** - Complete endpoint examples (SQL and Python)

### Specialized Guides

**Data Integration**:
- **references/excel-integration.md** - Excel file handling (.xlsx, .xls), pandas integration
- **references/synthetic-data-patterns.md** - Generate test/demo data with GENERATE_SERIES

**Advanced Topics**:
- **references/type-system.md** - Type validation rules
- **references/policies.md** - Policy expressions and examples
- **references/dbt-patterns.md** - Advanced dbt integration patterns
- **references/testing-guide.md** - Comprehensive testing guide
- **references/cli-reference.md** - Complete CLI documentation
- **references/claude-desktop.md** - Claude Desktop setup
