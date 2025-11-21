# Project Selection Guide

Decision tree and heuristics for selecting the right MXCP approach and templates based on **technical requirements**.

**Scope**: This guide helps select implementation patterns (SQL vs Python, template selection, architecture patterns) based on data sources, authentication mechanisms, and technical constraints. It does NOT help define business requirements or determine what features to build.

## Decision Tree

Use this decision tree to determine the appropriate MXCP implementation approach:

```
User Request
    ├─ Data File
    │   ├─ CSV file
    │   │   ├─ Static data → dbt seed + SQL tool
    │   │   ├─ Needs transformation → dbt seed + dbt model + SQL tool
    │   │   └─ Large file (>100MB) → Convert to Parquet + dbt model
    │   ├─ Excel file (.xlsx, .xls)
    │   │   ├─ Static/one-time → Convert to CSV + dbt seed
    │   │   ├─ User upload (dynamic) → Python tool with pandas + DuckDB table
    │   │   └─ Multi-sheet → Python tool to load all sheets as tables
    │   ├─ JSON/Parquet
    │   │   └─ DuckDB read_json/read_parquet directly in SQL tool
    │   └─ Synthetic data needed
    │       ├─ For testing → dbt model with GENERATE_SERIES
    │       ├─ Dynamic generation → Python tool with parameters
    │       └─ With statistics → Generate + analyze in single tool
    │
    ├─ External API Integration
    │   ├─ OAuth required
    │   │   ├─ Google (Calendar, Sheets, etc.) → google-calendar template
    │   │   ├─ Jira Cloud → jira-oauth template
    │   │   ├─ Salesforce → salesforce-oauth template
    │   │   └─ Other OAuth → Adapt google-calendar template
    │   │
    │   ├─ API Token/Basic Auth
    │   │   ├─ Jira → jira template
    │   │   ├─ Confluence → confluence template
    │   │   ├─ Salesforce → salesforce template
    │   │   ├─ Custom API → python-demo template
    │   │   └─ REST API → Create new Python tool
    │   │
    │   └─ Public API (no auth)
    │       └─ Create SQL tool with read_json/read_csv from URL
    │
    ├─ Database Connection
    │   ├─ PostgreSQL
    │   │   ├─ Direct query → DuckDB ATTACH + SQL tools
    │   │   └─ Cache data → dbt source + model + SQL tools
    │   ├─ MySQL
    │   │   ├─ Direct query → DuckDB ATTACH + SQL tools
    │   │   └─ Cache data → dbt source + model
    │   ├─ SQLite → DuckDB ATTACH + SQL tools (simple)
    │   ├─ SQL Server → DuckDB ATTACH + SQL tools
    │   └─ Other/NoSQL → Create Python tool with connection library
    │
    ├─ Complex Logic/Processing
    │   ├─ Data transformation → dbt model
    │   ├─ Business logic → Python tool
    │   ├─ ML/AI processing → Python tool with libraries
    │   └─ Async operations → Python tool with async/await
    │
    └─ Authentication/Security System
        ├─ Keycloak → keycloak template
        ├─ Custom SSO → Adapt keycloak template
        └─ Policy enforcement → Use MXCP policies
```

## Available Project Templates

### Data-Focused Templates

#### covid_owid
**Use when**: Working with external data sources, caching datasets

**Features**:
- dbt integration for data caching
- External CSV/JSON fetching
- Data quality tests
- Incremental updates

**Example use cases**:
- "Cache COVID statistics for offline analysis"
- "Query external datasets regularly"
- "Download and transform public data"

**Key files**:
- `models/` - dbt models for data transformation
- `tools/` - SQL tools querying cached data

#### earthquakes
**Use when**: Real-time data monitoring, geospatial data

**Features**:
- Real-time API queries
- Geospatial filtering
- Time-based queries

**Example use cases**:
- "Monitor earthquake activity"
- "Query geospatial data by region"
- "Real-time event tracking"

### API Integration Templates

#### google-calendar (OAuth)
**Use when**: Integrating with Google APIs or other OAuth 2.0 services

**Features**:
- OAuth 2.0 authentication flow
- Token management
- Google API client integration
- Python endpoints with async support

**Example use cases**:
- "Connect to Google Calendar"
- "Access Google Sheets data"
- "Integrate with Gmail"
- "Any OAuth 2.0 API integration"

**Adaptation guide**:
1. Replace Google API client with target API client
2. Update OAuth scopes and endpoints
3. Modify tool definitions for new API methods
4. Update configuration with new OAuth provider

#### jira (API Token)
**Use when**: Integrating with Jira using API tokens

**Features**:
- API token authentication
- JQL query support
- Issue, user, project management
- Python HTTP client pattern

**Example use cases**:
- "Query Jira issues"
- "Get project information"
- "Search for users"

#### jira-oauth (OAuth)
**Use when**: Jira integration requiring OAuth

**Features**:
- OAuth 1.0a for Jira
- More secure than API tokens
- Full Jira REST API access

#### confluence
**Use when**: Atlassian Confluence integration

**Features**:
- Confluence REST API
- Page and space queries
- Content search

**Example use cases**:
- "Search Confluence pages"
- "Get page content"
- "List spaces"

#### salesforce / salesforce-oauth
**Use when**: Salesforce CRM integration

**Features**:
- Salesforce REST API
- SOQL queries
- OAuth or username/password auth

**Example use cases**:
- "Query Salesforce records"
- "Get account information"
- "Search opportunities"

### Development Templates

#### python-demo
**Use when**: Building custom Python-based tools

**Features**:
- Python endpoint patterns
- Async/await examples
- Database access patterns
- Error handling

**Example use cases**:
- "Create custom API integration"
- "Implement complex business logic"
- "Build ML/AI-powered tools"

**Key patterns**:
```python
# Sync endpoint
def simple_tool(param: str) -> dict:
    return {"result": param.upper()}

# Async endpoint
async def async_tool(ids: list[str]) -> list[dict]:
    results = await asyncio.gather(*[fetch_data(id) for id in ids])
    return results

# Database access
def db_tool(query: str) -> list[dict]:
    return db.execute(query).fetchall()
```

### Infrastructure Templates

#### plugin
**Use when**: Extending DuckDB with custom functions

**Features**:
- DuckDB plugin development
- Custom SQL functions
- Compiled extensions

**Example use cases**:
- "Add custom SQL functions"
- "Integrate C/C++ libraries"
- "Optimize performance-critical operations"

#### keycloak
**Use when**: Enterprise authentication/authorization

**Features**:
- Keycloak integration
- SSO support
- Role-based access control

**Example use cases**:
- "Integrate with Keycloak SSO"
- "Implement role-based policies"
- "Enterprise user management"

#### squirro
**Use when**: Enterprise search and insights integration

**Features**:
- Squirro API integration
- Search and analytics
- Enterprise data access

## Common Scenarios and Heuristics

### Scenario 1: CSV File to Query

**User says**: "I need to connect my chat to a CSV file"

**Heuristic**:
1. **DO NOT** use existing templates
2. **CREATE** new MXCP project from scratch
3. **APPROACH**:
   - Place CSV in `seeds/` directory
   - Create `seeds/schema.yml` with schema definition and tests
   - Run `dbt seed` to load into DuckDB
   - Create SQL tool: `SELECT * FROM <table_name>`
   - Add parameters for filtering if needed

**Implementation steps**:
```bash
# 1. Initialize project
mkdir csv-server && cd csv-server
mxcp init --bootstrap

# 2. Setup dbt
mkdir seeds
cp /path/to/file.csv seeds/data.csv

# 3. Create schema
cat > seeds/schema.yml <<EOF
version: 2
seeds:
  - name: data
    description: "User uploaded CSV data"
    columns:
      - name: id
        tests: [unique, not_null]
      # ... add all columns
EOF

# 4. Load seed
dbt seed

# 5. Create tool
cat > tools/query_data.yml <<EOF
mxcp: 1
tool:
  name: query_data
  description: "Query the uploaded CSV data"
  parameters:
    - name: filter_column
      type: string
      required: false
  return:
    type: array
  source:
    code: |
      SELECT * FROM data
      WHERE \$filter_column IS NULL OR column_name = \$filter_column
EOF

# 6. Test
mxcp validate
mxcp test
mxcp serve
```

### Scenario 2: API Integration (OAuth)

**User says**: "Connect to [OAuth-enabled API]"

**Heuristic**:
1. **Check** if template exists (Google, Jira OAuth, Salesforce OAuth)
2. **If exists**: Copy and adapt template
3. **If not**: Copy `google-calendar` template and modify

**Implementation steps**:
```bash
# 1. Copy template
cp -r assets/project-templates/google-calendar my-api-project
cd my-api-project

# 2. Update mxcp-site.yml
vim mxcp-site.yml  # Change project name

# 3. Update config.yml for new OAuth provider
vim config.yml  # Update OAuth endpoints and scopes

# 4. Replace API client
pip install new-api-client-library
vim python/*.py  # Replace google-api-client with new library

# 5. Update tools for new API methods
vim tools/*.yml  # Adapt to new API endpoints

# 6. Test OAuth flow
mxcp serve
# Follow OAuth flow in browser
```

### Scenario 3: API Integration (Token/Basic Auth)

**User says**: "Connect to [API with token]"

**Heuristic**:
1. **Check** if template exists (Jira, Confluence, Salesforce)
2. **If exists**: Copy and adapt template
3. **If not**: Use `python-demo` template

**Implementation steps**:
```bash
# 1. Copy python-demo template
cp -r assets/project-templates/python-demo my-api-project
cd my-api-project

# 2. Create Python endpoint
cat > python/api_client.py <<EOF
import httpx
from mxcp.runtime import get_secret

async def fetch_data(endpoint: str) -> dict:
    secret = get_secret("api_token")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.example.com/{endpoint}",
            headers={"Authorization": f"Bearer {secret['token']}"}
        )
        return response.json()
EOF

# 3. Create tool
# 4. Configure secret in config.yml
# 5. Test
```

### Scenario 4: Complex Data Transformation

**User says**: "Transform this data and provide analytics"

**Heuristic**:
1. **Use** dbt for transformations
2. **Use** SQL tools for queries
3. **Pattern**: seed → model → tool

**Implementation steps**:
```bash
# 1. Load source data (seed or external)
# 2. Create dbt model for transformation
cat > models/analytics.sql <<EOF
{{ config(materialized='table') }}

SELECT
  DATE_TRUNC('month', date) as month,
  category,
  SUM(amount) as total,
  AVG(amount) as average,
  COUNT(*) as count
FROM {{ ref('source_data') }}
GROUP BY month, category
EOF

# 3. Create schema.yml
# 4. Run dbt
dbt run --select analytics
dbt test --select analytics

# 5. Create tool to query model
# 6. Test
```

### Scenario 5: Excel File Integration

**User says**: "I have an Excel file with sales data" or "Read this xlsx file"

**Heuristic**:
1. **If static/one-time**: Convert to CSV, use dbt seed
2. **If user upload**: Python tool with pandas to load into DuckDB
3. **If multi-sheet**: Python tool to process all sheets

**Implementation steps**:
```bash
# Option A: Static Excel → CSV → dbt seed
python -c "import pandas as pd; pd.read_excel('data.xlsx').to_csv('seeds/data.csv', index=False)"
cat > seeds/schema.yml  # Create schema
dbt seed

# Option B: Dynamic upload → Python tool
cat > python/excel_loader.py  # Create loader
cat > tools/load_excel.yml    # Create tool
pip install openpyxl pandas   # Add dependencies
```

See **references/excel-integration.md** for complete patterns.

### Scenario 6: Synthetic Data Generation

**User says**: "Generate test data" or "Create synthetic customer records" or "I need dummy data for testing"

**Heuristic**:
1. **If persistent test data**: dbt model with GENERATE_SERIES
2. **If dynamic/parameterized**: Python tool
3. **If with analysis**: Generate + calculate statistics in one tool

**Implementation steps**:
```bash
# Option A: Persistent via dbt
cat > models/synthetic_customers.sql <<EOF
{{ config(materialized='table') }}
SELECT
  ROW_NUMBER() OVER () AS id,
  'customer' || ROW_NUMBER() OVER () || '@example.com' AS email
FROM GENERATE_SERIES(1, 1000)
EOF

dbt run --select synthetic_customers

# Option B: Dynamic via Python
cat > python/generate_data.py  # Create generator
cat > tools/generate_test_data.yml  # Create tool
```

See **references/synthetic-data-patterns.md** for complete patterns.

### Scenario 7: Python Library Wrapping

**User says**: "Wrap the Stripe API" or "Use pandas for analysis" or "Connect to Redis"

**Heuristic**:
1. **Check** if it's an API client library (stripe, twilio, etc.)
2. **Check** if it's a data/ML library (pandas, sklearn, etc.)
3. **Use** `python-demo` as base
4. **Add** library to requirements.txt
5. **Use** @on_init for initialization if stateful

**Implementation steps**:
```bash
# 1. Copy python-demo template
cp -r assets/project-templates/python-demo my-project

# 2. Install library
echo "stripe>=5.4.0" >> requirements.txt
pip install stripe

# 3. Create wrapper
cat > python/stripe_wrapper.py  # Implement wrapper functions

# 4. Create tools
cat > tools/create_customer.yml  # Map to wrapper functions

# 5. Create project config with secrets
cat > config.yml <<EOF
mxcp: 1
profiles:
  default:
    secrets:
      - name: api_key
        type: env
        parameters:
          env_var: API_KEY
EOF

# User sets: export API_KEY=xxx
# Or user copies to ~/.mxcp/ manually if preferred
```

See **references/python-api.md** (Wrapping External Libraries section) for complete patterns.

### Scenario 8: ML/AI Processing

**User says**: "Analyze sentiment" or "Classify images" or "Train a model"

**Heuristic**:
1. **Use** Python tool (not SQL)
2. **Use** `python-demo` template as base
3. **Add** ML libraries (transformers, scikit-learn, etc.)
4. **Use** @on_init to load models (expensive operation)

**Implementation steps**:
```bash
# 1. Copy python-demo
# 2. Install ML libraries
pip install transformers torch

# 3. Create Python endpoint with model loading
cat > python/ml_tool.py <<EOF
from mxcp.runtime import on_init
from transformers import pipeline

classifier = None

@on_init
def load_model():
    global classifier
    classifier = pipeline("sentiment-analysis")

async def analyze_sentiment(texts: list[str]) -> list[dict]:
    results = classifier(texts)
    return [{"text": t, **r} for t, r in zip(texts, results)]
EOF

# 4. Create tool definition
# 5. Test
```

### Scenario 9: External Database Connection

**User says**: "Connect to my PostgreSQL database" or "Query my MySQL production database"

**Heuristic**:
1. **Ask** if data can be exported to CSV (simpler approach)
2. **Ask** if they need real-time data or can cache it
3. **Decide**: Direct query (ATTACH) vs cached (dbt)

**Implementation steps - Direct Query (ATTACH)**:
```bash
# 1. Create project
mkdir db-connection && cd db-connection
mxcp init --bootstrap

# 2. Create config with credentials
cat > config.yml <<EOF
mxcp: 1
profiles:
  default:
    secrets:
      - name: db_host
        type: env
        parameters:
          env_var: DB_HOST
      - name: db_user
        type: env
        parameters:
          env_var: DB_USER
      - name: db_password
        type: env
        parameters:
          env_var: DB_PASSWORD
      - name: db_name
        type: env
        parameters:
          env_var: DB_NAME
EOF

# 3. Create SQL tool with ATTACH
cat > tools/query_database.yml <<EOF
mxcp: 1
tool:
  name: query_customers
  description: "Query customers from PostgreSQL database"
  parameters:
    - name: country
      type: string
      required: false
  return:
    type: array
  source:
    code: |
      -- Install and attach PostgreSQL
      INSTALL postgres;
      LOAD postgres;
      ATTACH IF NOT EXISTS 'host=\${DB_HOST} port=5432 dbname=\${DB_NAME} user=\${DB_USER} password=\${DB_PASSWORD}'
        AS prod_db (TYPE POSTGRES);

      -- Query attached database
      SELECT customer_id, name, email, country
      FROM prod_db.public.customers
      WHERE \$country IS NULL OR country = \$country
      LIMIT 1000
EOF

# 4. Set credentials and test
export DB_HOST="localhost"
export DB_USER="readonly_user"
export DB_PASSWORD="secure_pass"
export DB_NAME="mydb"

mxcp validate
mxcp run tool query_customers --param country="US"
mxcp serve
```

**Implementation steps - Cached with dbt**:
```bash
# 1. Create project
mkdir db-cache && cd db-cache
mxcp init --bootstrap

# 2. Create dbt source
mkdir -p models
cat > models/sources.yml <<EOF
version: 2
sources:
  - name: production
    database: postgres_db
    schema: public
    tables:
      - name: customers
        columns:
          - name: customer_id
            tests: [unique, not_null]
EOF

# 3. Create dbt model to cache data
cat > models/customer_cache.sql <<EOF
{{ config(materialized='table') }}

-- Attach PostgreSQL
{% set attach_sql %}
INSTALL postgres;
LOAD postgres;
ATTACH IF NOT EXISTS 'host=\${DB_HOST} dbname=\${DB_NAME} user=\${DB_USER} password=\${DB_PASSWORD}'
  AS postgres_db (TYPE POSTGRES);
{% endset %}
{% do run_query(attach_sql) %}

-- Cache data
SELECT * FROM postgres_db.public.customers
EOF

# 4. Create schema
cat > models/schema.yml <<EOF
version: 2
models:
  - name: customer_cache
    columns:
      - name: customer_id
        tests: [unique, not_null]
EOF

# 5. Run dbt to cache data
export DB_HOST="localhost" DB_USER="user" DB_PASSWORD="pass" DB_NAME="mydb"
dbt run --select customer_cache
dbt test --select customer_cache

# 6. Create MXCP tool to query cache (fast!)
cat > tools/query_cached.yml <<EOF
mxcp: 1
tool:
  name: query_customers
  source:
    code: SELECT * FROM customer_cache WHERE \$country IS NULL OR country = \$country
EOF

# 7. Create refresh tool
# (see minimal-working-examples.md Example 7 for complete refresh tool)
```

**When to use which approach**:
- **ATTACH (Direct)**: Real-time data needed, small queries, low query frequency
- **dbt (Cached)**: Large tables, frequent queries, can tolerate staleness, want data quality tests

See **references/database-connections.md** for complete patterns.

## When to Ask for Clarification

**If user request is ambiguous, ask these questions**:

### Data Source Unclear
- "What type of data are you working with? (CSV, API, database, etc.)"
- "Do you have a file to upload, or are you connecting to an external source?"

### API Integration Unclear
- "Does this API require authentication? (OAuth, API token, basic auth, or none)"
- "What operations do you need? (read data, write data, both)"

### Data Volume Unclear
- "How large is the dataset? (<1MB, 1-100MB, >100MB)"
- "How often does the data update? (static, daily, real-time)"

### Security Requirements Unclear
- "Who should have access to this data? (everyone, specific roles, specific users)"
- "Are there any sensitive fields that need protection?"

### Functionality Unclear
- "What questions do you want to ask about this data?"
- "What operations should be available through the MCP server?"

## Heuristics When No Interaction Available

**If cannot ask questions, use these defaults**:

1. **CSV file mentioned** → dbt seed + SQL tool with `SELECT *`
2. **Excel mentioned** → Convert to CSV + dbt seed OR Python pandas tool
3. **API mentioned** → Check for template, otherwise use Python tool with httpx
4. **OAuth mentioned** → Use google-calendar template as base
5. **Database mentioned** → DuckDB ATTACH for direct query OR dbt for caching
6. **PostgreSQL/MySQL mentioned** → Use ATTACH with read-only user
7. **Transformation needed** → dbt model
8. **Complex logic** → Python tool
9. **Security not mentioned** → No policies (user can add later)
10. **No auth mentioned for API** → Assume token/basic auth

## Configuration Management

### Project-Local Config (Recommended)

**ALWAYS create `config.yml` in the project directory, NOT `~/.mxcp/config.yml`**

**Why?**
- User maintains control over global config
- Project is self-contained and portable
- Safer for agents (no global config modification)
- User can review before copying to ~/.mxcp/

**Basic config.yml template**:
```yaml
# config.yml (in project root)
mxcp: 1

profiles:
  default:
    # Secrets via environment variables (recommended)
    secrets:
      - name: api_token
        type: env
        parameters:
          env_var: API_TOKEN

    # Database configuration (optional, default is data/db-default.duckdb)
    database:
      path: "data/db-default.duckdb"

    # Authentication (if needed)
    auth:
      provider: github  # or google, microsoft, etc.

  production:
    database:
      path: "prod.duckdb"
    audit:
      enabled: true
      path: "audit.jsonl"
```

**Usage options**:
```bash
# Option 1: Auto-discover (mxcp looks for ./config.yml)
mxcp serve

# Option 2: Explicit path via environment variable
MXCP_CONFIG=./config.yml mxcp serve

# Option 3: User manually copies to global location
cp config.yml ~/.mxcp/config.yml
mxcp serve
```

**In skill implementations**:
```bash
# CORRECT: Create local config
cat > config.yml <<EOF
mxcp: 1
profiles:
  default:
    secrets:
      - name: github_token
        type: env
        parameters:
          env_var: GITHUB_TOKEN
EOF

echo "Config created at ./config.yml"
echo "Set environment variable: export GITHUB_TOKEN=your_token"
echo "Or copy to global config: cp config.yml ~/.mxcp/config.yml"
```

```bash
# WRONG: Don't edit user's global config
# DON'T DO THIS:
# vim ~/.mxcp/config.yml  # ❌ Never do this!
```

### Secrets Management

**Three approaches (in order of preference)**:

1. **Environment Variables** (Best for development):
```yaml
# config.yml
secrets:
  - name: api_key
    type: env
    parameters:
      env_var: API_KEY
```
```bash
export API_KEY=your_secret_key
mxcp serve
```

2. **Vault/1Password** (Best for production):
```yaml
# config.yml
secrets:
  - name: database_creds
    type: vault
    parameters:
      path: secret/data/myapp/db
      field: password
```

3. **Direct in config.yml** (Only for non-sensitive or example values):
```yaml
# config.yml - ONLY for non-sensitive data
secrets:
  - name: api_endpoint
    type: python
    parameters:
      url: "https://api.example.com"  # Not sensitive
```

**Instructions for users**:
```bash
# After agent creates config.yml, user can:

# Option A: Use environment variables
export API_KEY=xxx
export DB_PASSWORD=yyy
mxcp serve

# Option B: Copy to global config and edit
cp config.yml ~/.mxcp/config.yml
vim ~/.mxcp/config.yml  # User edits their own config
mxcp serve

# Option C: Use with explicit path
MXCP_CONFIG=./config.yml mxcp serve
```

## Security-First Checklist

**ALWAYS consider security**:

- [ ] **Authentication**: What auth method is needed?
- [ ] **Authorization**: Who can access this data?
- [ ] **Input validation**: Add parameter validation in tool definition
- [ ] **Output filtering**: Use policies to filter sensitive fields
- [ ] **Secrets management**: Use Vault/1Password, never hardcode
- [ ] **Audit logging**: Enable for production systems
- [ ] **SQL injection**: Use parameterized queries (`$param`)
- [ ] **Rate limiting**: Consider for external API calls

## Robustness Checklist

**ALWAYS ensure robustness**:

- [ ] **Error handling**: Add try/catch in Python, handle nulls in SQL
- [ ] **Type validation**: Define return types and parameter types
- [ ] **Tests**: Create test cases for all tools
- [ ] **Data validation**: Add dbt tests for seeds and models
- [ ] **Documentation**: Add descriptions to all tools/resources
- [ ] **Schema validation**: Create schema.yml for all dbt seeds/models

## Testing Checklist

**ALWAYS test before deployment**:

- [ ] `mxcp validate` - Structure validation
- [ ] `mxcp test` - Functional testing
- [ ] `mxcp lint` - Metadata quality
- [ ] `dbt test` - Data quality (if using dbt)
- [ ] Manual testing with `mxcp run tool <name>`
- [ ] Test with invalid inputs
- [ ] Test with edge cases (empty data, nulls, etc.)

## Summary

**Quick reference for common requests**:

| User Request | Approach | Template | Key Steps |
|--------------|----------|----------|-----------|
| "Query my CSV" | dbt seed + SQL tool | None | seed → schema.yml → dbt seed/test → SQL tool |
| "Read Excel file" | Convert to CSV + dbt seed OR pandas tool | None | Excel→CSV → seed OR pandas → DuckDB table |
| "Connect to PostgreSQL" | ATTACH + SQL tool OR dbt cache | None | ATTACH → SQL tool OR dbt source/model → SQL tool |
| "Connect to MySQL" | ATTACH + SQL tool OR dbt cache | None | ATTACH → SQL tool OR dbt source/model → SQL tool |
| "Generate test data" | dbt model or Python | None | GENERATE_SERIES → dbt model or Python tool |
| "Wrap library X" | Python wrapper | python-demo | Install lib → wrap functions → create tools |
| "Connect to Google Calendar" | OAuth + Python | google-calendar | Copy template → configure OAuth |
| "Connect to Jira" | Token + Python | jira or jira-oauth | Copy template → configure token |
| "Transform data" | dbt model | None | seed/source → model → schema.yml → dbt run/test → SQL tool |
| "Complex logic" | Python tool | python-demo | Copy template → implement function |
| "ML/AI task" | Python + libraries | python-demo | Add ML libs → implement model |
| "External API" | Python + httpx | python-demo | Implement client → create tool |

**Priority order**:
1. Security (auth, policies, validation)
2. Robustness (error handling, types, tests)
3. Testing (validate, test, lint)
4. Features (based on user needs)
