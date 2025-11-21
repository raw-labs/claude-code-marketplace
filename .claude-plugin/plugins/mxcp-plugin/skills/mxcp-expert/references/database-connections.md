# Database Connections Guide

Complete guide for connecting MXCP to external databases (PostgreSQL, MySQL, SQLite, SQL Server) using DuckDB's ATTACH functionality and dbt integration.

## Overview

MXCP can connect to external databases in two ways:
1. **Direct querying** via DuckDB ATTACH (read data from external databases)
2. **dbt integration** (transform external data using dbt sources and models)

**Key principle**: External databases → DuckDB (via ATTACH or dbt) → MXCP tools

## When to Use Database Connections

**Use database connections when**:
- You have existing data in PostgreSQL, MySQL, or other SQL databases
- You want to query production databases (read-only recommended)
- You need to join external data with local data
- You want to cache/materialize external data locally

**Don't use database connections when**:
- You can export data to CSV (use dbt seeds instead - simpler and safer)
- You need real-time writes (MXCP is read-focused)
- The database has complex security requirements (use API wrapper instead)

## Method 1: Direct Database Access with ATTACH

### PostgreSQL Connection

#### Basic ATTACH Syntax

```sql
-- Attach PostgreSQL database
INSTALL postgres;
LOAD postgres;

ATTACH 'host=localhost port=5432 dbname=mydb user=myuser password=mypass'
  AS postgres_db (TYPE POSTGRES);

-- Query attached database
SELECT * FROM postgres_db.public.customers WHERE country = 'US';
```

#### Complete Working Example

**Project structure**:
```
postgres-query/
├── mxcp-site.yml
├── config.yml           # Database credentials
├── tools/
│   ├── query_customers.yml
│   └── get_orders.yml
└── sql/
    └── setup.sql        # ATTACH commands
```

**Step 1: Create config.yml with database credentials**

```yaml
# config.yml (in project directory)
mxcp: 1

profiles:
  default:
    secrets:
      - name: postgres_connection
        type: env
        parameters:
          env_var: POSTGRES_CONNECTION_STRING

      # Alternative: separate credentials
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
```

**Step 2: Set environment variables**

```bash
# Option 1: Connection string
export POSTGRES_CONNECTION_STRING="host=localhost port=5432 dbname=mydb user=myuser password=mypass"

# Option 2: Separate credentials
export DB_HOST="localhost"
export DB_USER="myuser"
export DB_PASSWORD="mypass"
```

**Step 3: Create SQL setup file**

```sql
-- sql/setup.sql
-- Install and load PostgreSQL extension
INSTALL postgres;
LOAD postgres;

-- Attach database (connection string from environment)
ATTACH 'host=${DB_HOST} port=5432 dbname=mydb user=${DB_USER} password=${DB_PASSWORD}'
  AS prod_db (TYPE POSTGRES);
```

**Step 4: Create query tool**

```yaml
# tools/query_customers.yml
mxcp: 1
tool:
  name: query_customers
  description: "Query customers from PostgreSQL database by country"
  parameters:
    - name: country
      type: string
      description: "Filter by country code (e.g., 'US', 'UK')"
      required: false
  return:
    type: array
    items:
      type: object
      properties:
        customer_id: { type: integer }
        name: { type: string }
        email: { type: string }
        country: { type: string }
  source:
    code: |
      -- First ensure PostgreSQL is attached
      INSTALL postgres;
      LOAD postgres;
      ATTACH IF NOT EXISTS 'host=${DB_HOST} port=5432 dbname=mydb user=${DB_USER} password=${DB_PASSWORD}'
        AS prod_db (TYPE POSTGRES);

      -- Query attached database
      SELECT
        customer_id,
        name,
        email,
        country
      FROM prod_db.public.customers
      WHERE $country IS NULL OR country = $country
      ORDER BY customer_id
      LIMIT 1000
  tests:
    - name: "test_connection"
      arguments: []
      # Test will verify connection works
```

**Step 5: Validate and test**

```bash
# Set credentials
export DB_HOST="localhost"
export DB_USER="myuser"
export DB_PASSWORD="mypass"

# Validate structure
mxcp validate

# Test tool
mxcp run tool query_customers --param country="US"

# Start server
mxcp serve
```

### MySQL Connection

```sql
-- Install MySQL extension
INSTALL mysql;
LOAD mysql;

-- Attach MySQL database
ATTACH 'host=localhost port=3306 database=mydb user=root password=pass'
  AS mysql_db (TYPE MYSQL);

-- Query
SELECT * FROM mysql_db.orders WHERE order_date >= '2024-01-01';
```

**Complete tool example**:

```yaml
# tools/query_mysql_orders.yml
mxcp: 1
tool:
  name: query_mysql_orders
  description: "Query orders from MySQL database"
  parameters:
    - name: start_date
      type: string
      format: date
      required: false
    - name: status
      type: string
      required: false
  return:
    type: array
    items:
      type: object
  source:
    code: |
      INSTALL mysql;
      LOAD mysql;
      ATTACH IF NOT EXISTS 'host=${MYSQL_HOST} database=${MYSQL_DB} user=${MYSQL_USER} password=${MYSQL_PASSWORD}'
        AS mysql_db (TYPE MYSQL);

      SELECT
        order_id,
        customer_id,
        order_date,
        total_amount,
        status
      FROM mysql_db.orders
      WHERE ($start_date IS NULL OR order_date >= $start_date)
        AND ($status IS NULL OR status = $status)
      ORDER BY order_date DESC
      LIMIT 1000
```

### SQLite Connection

```sql
-- Attach SQLite database
ATTACH 'path/to/database.db' AS sqlite_db (TYPE SQLITE);

-- Query
SELECT * FROM sqlite_db.users WHERE active = true;
```

**Tool example**:

```yaml
# tools/query_sqlite.yml
mxcp: 1
tool:
  name: query_sqlite_users
  description: "Query users from SQLite database"
  parameters:
    - name: active_only
      type: boolean
      default: true
  return:
    type: array
  source:
    code: |
      ATTACH IF NOT EXISTS '${SQLITE_DB_PATH}' AS sqlite_db (TYPE SQLITE);

      SELECT user_id, username, email, created_at
      FROM sqlite_db.users
      WHERE $active_only = false OR active = true
      ORDER BY created_at DESC
```

### SQL Server Connection

```sql
-- Install SQL Server extension
INSTALL sqlserver;
LOAD sqlserver;

-- Attach SQL Server database
ATTACH 'Server=localhost;Database=mydb;Uid=user;Pwd=pass;'
  AS sqlserver_db (TYPE SQLSERVER);

-- Query
SELECT * FROM sqlserver_db.dbo.products WHERE category = 'Electronics';
```

## Method 2: dbt Integration with External Databases

**Use dbt when**:
- You want to materialize/cache external data locally
- You need to transform external data before querying
- You want data quality tests on external data
- You prefer declarative SQL over ATTACH statements

### dbt Sources for External Databases

**Pattern**: External DB → dbt source → dbt model → MXCP tool

#### Step 1: Configure dbt profile for external database

```yaml
# profiles.yml (auto-generated by MXCP, or manually edit)
my_project:
  outputs:
    dev:
      type: postgres  # or mysql, sqlserver, etc.
      host: localhost
      port: 5432
      user: "{{ env_var('DB_USER') }}"
      password: "{{ env_var('DB_PASSWORD') }}"
      dbname: mydb
      schema: public
      threads: 4

    # Hybrid: use DuckDB for local, Postgres for source
    hybrid:
      type: duckdb
      path: "{{ env_var('MXCP_DUCKDB_PATH', 'data/db-default.duckdb') }}"
  target: hybrid
```

#### Step 2: Define external database as dbt source

```yaml
# models/sources.yml
version: 2

sources:
  - name: production_db
    description: "Production PostgreSQL database"
    database: postgres_db  # Matches ATTACH name
    schema: public
    tables:
      - name: customers
        description: "Customer master data"
        columns:
          - name: customer_id
            description: "Unique customer identifier"
            tests:
              - unique
              - not_null
          - name: email
            tests:
              - not_null
          - name: country
            tests:
              - not_null

      - name: orders
        description: "Order transactions"
        columns:
          - name: order_id
            tests:
              - unique
              - not_null
          - name: customer_id
            tests:
              - not_null
              - relationships:
                  to: source('production_db', 'customers')
                  field: customer_id
```

#### Step 3: Create dbt model to cache/transform external data

```sql
-- models/customer_summary.sql
{{ config(
    materialized='table',
    description='Customer summary from production database'
) }}

SELECT
  c.customer_id,
  c.name,
  c.email,
  c.country,
  COUNT(o.order_id) as order_count,
  COALESCE(SUM(o.total_amount), 0) as total_spent,
  MAX(o.order_date) as last_order_date
FROM {{ source('production_db', 'customers') }} c
LEFT JOIN {{ source('production_db', 'orders') }} o
  ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name, c.email, c.country
```

```yaml
# models/schema.yml
version: 2

models:
  - name: customer_summary
    description: "Aggregated customer metrics from production"
    columns:
      - name: customer_id
        tests:
          - unique
          - not_null
      - name: order_count
        tests:
          - not_null
      - name: total_spent
        tests:
          - not_null
```

#### Step 4: Run dbt to materialize data

```bash
# Test connection to external database
dbt debug

# Run models (fetches from external DB, materializes in DuckDB)
dbt run --select customer_summary

# Test data quality
dbt test --select customer_summary
```

#### Step 5: Create MXCP tool to query materialized data

```yaml
# tools/get_customer_summary.yml
mxcp: 1
tool:
  name: get_customer_summary
  description: "Get customer summary statistics from cached production data"
  parameters:
    - name: country
      type: string
      required: false
    - name: min_orders
      type: integer
      default: 0
  return:
    type: array
    items:
      type: object
      properties:
        customer_id: { type: integer }
        name: { type: string }
        order_count: { type: integer }
        total_spent: { type: number }
  source:
    code: |
      SELECT
        customer_id,
        name,
        email,
        country,
        order_count,
        total_spent,
        last_order_date
      FROM customer_summary
      WHERE ($country IS NULL OR country = $country)
        AND order_count >= $min_orders
      ORDER BY total_spent DESC
      LIMIT 100
```

#### Step 6: Refresh data periodically

```bash
# Manual refresh
dbt run --select customer_summary

# Or create Python tool to trigger refresh
```

```yaml
# tools/refresh_data.yml
mxcp: 1
tool:
  name: refresh_customer_data
  description: "Refresh customer summary from production database"
  language: python
  return:
    type: object
  source:
    file: ../python/refresh.py
```

```python
# python/refresh.py
from mxcp.runtime import reload_duckdb
import subprocess

def refresh_customer_data() -> dict:
    """Refresh customer summary from external database"""

    def run_dbt():
        result = subprocess.run(
            ["dbt", "run", "--select", "customer_summary"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise Exception(f"dbt run failed: {result.stderr}")

        test_result = subprocess.run(
            ["dbt", "test", "--select", "customer_summary"],
            capture_output=True,
            text=True
        )
        if test_result.returncode != 0:
            raise Exception(f"dbt test failed: {test_result.stderr}")

    # Run dbt with exclusive database access
    reload_duckdb(
        payload_func=run_dbt,
        description="Refreshing customer data from production"
    )

    return {
        "status": "success",
        "message": "Customer data refreshed from production database"
    }
```

### Incremental dbt Models for Large Tables

For large external tables, use incremental materialization:

```sql
-- models/orders_incremental.sql
{{ config(
    materialized='incremental',
    unique_key='order_id',
    on_schema_change='fail'
) }}

SELECT
  order_id,
  customer_id,
  order_date,
  total_amount,
  status
FROM {{ source('production_db', 'orders') }}

{% if is_incremental() %}
  -- Only fetch new/updated orders
  WHERE order_date > (SELECT MAX(order_date) FROM {{ this }})
{% endif %}
```

```bash
# First run: fetch all historical data
dbt run --select orders_incremental --full-refresh

# Subsequent runs: only fetch new data
dbt run --select orders_incremental
```

## Connection Patterns and Best Practices

### Pattern 1: Read-Only Querying

**Use case**: Query production database directly without caching

```yaml
tool:
  name: query_live_data
  source:
    code: |
      ATTACH IF NOT EXISTS 'connection_string' AS prod (TYPE POSTGRES);
      SELECT * FROM prod.public.table WHERE ...
```

**Pros**: Always fresh data
**Cons**: Slower queries, database load

### Pattern 2: Cached/Materialized Data

**Use case**: Cache external data in DuckDB for fast queries

```sql
-- dbt model caches external data
SELECT * FROM {{ source('external_db', 'table') }}
```

```yaml
# MXCP tool queries cache
tool:
  source:
    code: SELECT * FROM cached_table WHERE ...
```

**Pros**: Fast queries, no database load
**Cons**: Data staleness, needs refresh

### Pattern 3: Hybrid (Cache + Live)

**Use case**: Cache most data, query live for real-time needs

```sql
-- Combine cached and live data
SELECT * FROM cached_historical_orders
UNION ALL
SELECT * FROM prod.public.orders WHERE order_date >= CURRENT_DATE - INTERVAL '7 days'
```

### Security Best Practices

#### 1. Use Read-Only Database Users

```sql
-- PostgreSQL: Create read-only user
CREATE USER readonly_user WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE mydb TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
```

#### 2. Store Credentials in Secrets

```yaml
# config.yml - NEVER commit passwords
secrets:
  - name: db_password
    type: env
    parameters:
      env_var: DB_PASSWORD

  # Production: use Vault
  - name: prod_db_password
    type: vault
    parameters:
      path: secret/data/myapp/database
      field: password
```

#### 3. Use Connection Pooling (for Python approach)

```python
# python/db_client.py
from mxcp.runtime import on_init, on_shutdown
import psycopg2.pool

connection_pool = None

@on_init
def setup_pool():
    global connection_pool
    connection_pool = psycopg2.pool.SimpleConnectionPool(
        minconn=1,
        maxconn=5,
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

@on_shutdown
def close_pool():
    global connection_pool
    if connection_pool:
        connection_pool.closeall()

def query_database(sql: str) -> list[dict]:
    conn = connection_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        return results
    finally:
        connection_pool.putconn(conn)
```

### Error Handling

#### Handle Connection Failures

```yaml
# tools/query_with_error_handling.yml
tool:
  name: safe_query
  language: python
  source:
    file: ../python/safe_query.py
```

```python
# python/safe_query.py
from mxcp.runtime import db
import duckdb

def safe_query(table_name: str) -> dict:
    """Query external database with error handling"""
    try:
        # Try to attach if not already attached
        db.execute("""
            INSTALL postgres;
            LOAD postgres;
            ATTACH IF NOT EXISTS 'host=${DB_HOST} dbname=${DB_NAME} user=${DB_USER} password=${DB_PASSWORD}'
              AS prod (TYPE POSTGRES);
        """)

        # Query
        results = db.execute(f"SELECT * FROM prod.public.{table_name} LIMIT 100").fetchall()

        return {
            "success": True,
            "row_count": len(results),
            "data": results
        }

    except duckdb.CatalogException as e:
        return {
            "success": False,
            "error": "Table not found",
            "message": f"Table {table_name} does not exist in external database",
            "suggestion": "Check table name and database connection"
        }

    except duckdb.IOException as e:
        return {
            "success": False,
            "error": "Connection failed",
            "message": "Could not connect to external database",
            "suggestion": "Check database credentials and network connectivity"
        }

    except Exception as e:
        return {
            "success": False,
            "error": "Unexpected error",
            "message": str(e)
        }
```

### Performance Optimization

#### 1. Add Indexes on Frequently Filtered Columns

```sql
-- On external database (PostgreSQL)
CREATE INDEX idx_customers_country ON customers(country);
CREATE INDEX idx_orders_date ON orders(order_date);
```

#### 2. Limit Result Sets

```sql
-- Always add LIMIT for large tables
SELECT * FROM prod.public.orders
WHERE order_date >= '2024-01-01'
LIMIT 1000  -- Prevent overwhelming queries
```

#### 3. Materialize Complex Joins

```sql
-- Instead of complex join on every query
-- Create dbt model to materialize the join
{{ config(materialized='table') }}

SELECT ... complex join logic ...
FROM {{ source('prod', 'table1') }} t1
JOIN {{ source('prod', 'table2') }} t2 ...
```

## Complete Example: PostgreSQL to MXCP

**Scenario**: Query production PostgreSQL customer database

```bash
# 1. Create project
mkdir postgres-customers && cd postgres-customers
mxcp init --bootstrap

# 2. Create config
cat > config.yml <<'EOF'
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
EOF

# 3. Create tool
cat > tools/query_customers.yml <<'EOF'
mxcp: 1
tool:
  name: query_customers
  description: "Query customers from PostgreSQL"
  parameters:
    - name: country
      type: string
      required: false
  return:
    type: array
  source:
    code: |
      INSTALL postgres;
      LOAD postgres;
      ATTACH IF NOT EXISTS 'host=${DB_HOST} port=5432 dbname=customers user=${DB_USER} password=${DB_PASSWORD}'
        AS prod (TYPE POSTGRES);

      SELECT customer_id, name, email, country
      FROM prod.public.customers
      WHERE $country IS NULL OR country = $country
      LIMIT 100
EOF

# 4. Set credentials
export DB_HOST="localhost"
export DB_USER="readonly_user"
export DB_PASSWORD="secure_password"

# 5. Test
mxcp validate
mxcp run tool query_customers --param country="US"

# 6. Start server
mxcp serve
```

## Summary

**For external database connections**:

1. **Direct querying** → Use ATTACH with parameterized connection strings
2. **Cached data** → Use dbt sources + models for materialization
3. **Always use read-only users** for security
4. **Store credentials in environment variables** or Vault
5. **Handle connection errors** gracefully in Python tools
6. **Test with** `mxcp validate && mxcp run tool <name>`
7. **Use dbt for** large tables (incremental models) and transformations

**Decision guide**:
- Small queries, real-time data needed → ATTACH
- Large tables, can tolerate staleness → dbt materialization
- Complex transformations → dbt models
- Simple SELECT queries → ATTACH

This approach gives you full SQL database access while maintaining MXCP's security, validation, and testing workflow.
