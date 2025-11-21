# Minimal Working Examples

**Guaranteed-to-work examples for common MXCP patterns. Copy, test, then customize.**

## Example 1: CSV File to Queryable Tool

**Use case**: User has a CSV file, wants to query it.

**This example is TESTED and WORKS.**

### Setup

```bash
# 1. Create project
mkdir csv-query-example && cd csv-query-example
mxcp init --bootstrap

# 2. Create test CSV
cat > seeds/customers.csv <<'EOF'
customer_id,name,email,city,signup_date
1,John Doe,john@example.com,New York,2024-01-15
2,Jane Smith,jane@example.com,Los Angeles,2024-02-20
3,Bob Johnson,bob@example.com,Chicago,2024-03-10
EOF

# 3. Create schema
cat > seeds/schema.yml <<'EOF'
version: 2

seeds:
  - name: customers
    description: "Customer master data"
    columns:
      - name: customer_id
        data_type: integer
        tests:
          - unique
          - not_null
      - name: name
        data_type: varchar
        tests:
          - not_null
      - name: email
        data_type: varchar
        tests:
          - not_null
      - name: city
        data_type: varchar
      - name: signup_date
        data_type: date
EOF

# 4. Load data
dbt seed
dbt test

# 5. Create query tool
cat > tools/get_customers.yml <<'EOF'
mxcp: 1
tool:
  name: get_customers
  description: "Query customers by city or get all customers"
  parameters:
    - name: city
      type: string
      description: "Filter by city (optional)"
      default: null
  return:
    type: array
    items:
      type: object
      properties:
        customer_id: { type: integer }
        name: { type: string }
        email: { type: string }
        city: { type: string }
        signup_date: { type: string }
  source:
    code: |
      SELECT
        customer_id,
        name,
        email,
        city,
        signup_date::VARCHAR as signup_date
      FROM customers
      WHERE $city IS NULL OR city = $city
      ORDER BY customer_id
  tests:
    - name: "get_all"
      arguments: []
      result:
        - customer_id: 1
        - customer_id: 2
        - customer_id: 3
    - name: "filter_by_city"
      arguments:
        - key: city
          value: "Chicago"
      result:
        - customer_id: 3
          name: "Bob Johnson"
EOF

# 6. Validate and test
mxcp validate
mxcp test

# 7. Manual test
mxcp run tool get_customers
mxcp run tool get_customers --param city="New York"

# 8. Start server
mxcp serve
```

**Expected result**: All commands succeed, server starts without errors.

---

## Example 2: Python Tool with API Call

**Use case**: Wrap an HTTP API as an MCP tool.

**This example is TESTED and WORKS.**

### Setup

```bash
# 1. Create project
mkdir api-wrapper-example && cd api-wrapper-example
mxcp init --bootstrap

# 2. Create requirements.txt
cat > requirements.txt <<'EOF'
httpx>=0.24.0
EOF

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create Python wrapper
mkdir -p python
cat > python/api_wrapper.py <<'EOF'
import httpx

async def fetch_users(limit: int = 10) -> dict:
    """Fetch users from JSONPlaceholder API"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://jsonplaceholder.typicode.com/users"
            )
            response.raise_for_status()
            users = response.json()

        # Limit results
        limited_users = users[:limit]

        return {
            "count": len(limited_users),
            "users": [
                {
                    "id": user["id"],
                    "name": user["name"],
                    "email": user["email"],
                    "city": user["address"]["city"]
                }
                for user in limited_users
            ]
        }
    except httpx.HTTPError as e:
        return {"error": str(e), "users": []}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}", "users": []}

async def fetch_user(user_id: int) -> dict:
    """Fetch single user by ID"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://jsonplaceholder.typicode.com/users/{user_id}"
            )
            response.raise_for_status()
            user = response.json()

        return {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "city": user["address"]["city"],
            "company": user["company"]["name"]
        }
    except httpx.HTTPError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
EOF

# 5. Create tools
cat > tools/list_users.yml <<'EOF'
mxcp: 1
tool:
  name: list_users
  description: "Get list of users from API"
  language: python
  parameters:
    - name: limit
      type: integer
      default: 10
      description: "Maximum number of users to return"
  return:
    type: object
    properties:
      count: { type: integer }
      users: { type: array }
  source:
    file: ../python/api_wrapper.py
  tests:
    - name: "default_limit"
      arguments: []
      result:
        count: 10
EOF

cat > tools/get_user.yml <<'EOF'
mxcp: 1
tool:
  name: get_user
  description: "Get single user by ID"
  language: python
  parameters:
    - name: user_id
      type: integer
      description: "User ID to fetch"
  return:
    type: object
    properties:
      id: { type: integer }
      name: { type: string }
      email: { type: string }
  source:
    file: ../python/api_wrapper.py
  tests:
    - name: "fetch_user_1"
      arguments:
        - key: user_id
          value: 1
      result:
        id: 1
        name: "Leanne Graham"
EOF

# 6. Validate and test
mxcp validate
mxcp test

# 7. Manual test
mxcp run tool list_users --param limit=5
mxcp run tool get_user --param user_id=1

# 8. Start server
mxcp serve
```

**Expected result**: All commands succeed, API calls work, server starts.

---

## Example 3: Synthetic Data Generation

**Use case**: Generate test data for development.

**This example is TESTED and WORKS.**

### Setup

```bash
# 1. Create project
mkdir synthetic-data-example && cd synthetic-data-example
mxcp init --bootstrap

# 2. Create dbt model for synthetic data
mkdir -p models
cat > models/synthetic_orders.sql <<'EOF'
{{ config(materialized='table') }}

SELECT
  ROW_NUMBER() OVER () AS order_id,
  FLOOR(RANDOM() * 100 + 1)::INTEGER AS customer_id,
  order_date,
  FLOOR(RANDOM() * 50000 + 1000)::INTEGER / 100.0 AS amount,
  LIST_ELEMENT(['pending', 'shipped', 'delivered', 'cancelled'], FLOOR(RANDOM() * 4 + 1)::INTEGER) AS status,
  LIST_ELEMENT(['credit_card', 'paypal', 'bank_transfer'], FLOOR(RANDOM() * 3 + 1)::INTEGER) AS payment_method
FROM GENERATE_SERIES(
  DATE '2024-01-01',
  DATE '2024-12-31',
  INTERVAL '6 hours'
) AS t(order_date)
EOF

# 3. Create schema
cat > models/schema.yml <<'EOF'
version: 2

models:
  - name: synthetic_orders
    description: "Synthetically generated order data for testing"
    columns:
      - name: order_id
        tests: [unique, not_null]
      - name: customer_id
        tests: [not_null]
      - name: order_date
        tests: [not_null]
      - name: amount
        tests: [not_null]
      - name: status
        tests: [not_null, accepted_values: { values: ['pending', 'shipped', 'delivered', 'cancelled'] }]
EOF

# 4. Run dbt
dbt run --select synthetic_orders
dbt test --select synthetic_orders

# 5. Create query tool
cat > tools/get_orders.yml <<'EOF'
mxcp: 1
tool:
  name: get_orders
  description: "Query synthetic orders with filters"
  parameters:
    - name: status
      type: string
      description: "Filter by status"
      default: null
    - name: limit
      type: integer
      default: 100
      description: "Maximum results"
  return:
    type: array
    items:
      type: object
  source:
    code: |
      SELECT
        order_id,
        customer_id,
        order_date,
        amount,
        status,
        payment_method
      FROM synthetic_orders
      WHERE $status IS NULL OR status = $status
      ORDER BY order_date DESC
      LIMIT $limit
  tests:
    - name: "get_pending"
      arguments:
        - key: status
          value: "pending"
        - key: limit
          value: 10
EOF

# 6. Create statistics tool
cat > tools/order_statistics.yml <<'EOF'
mxcp: 1
tool:
  name: order_statistics
  description: "Get order statistics by status"
  return:
    type: array
    items:
      type: object
      properties:
        status: { type: string }
        order_count: { type: integer }
        total_amount: { type: number }
        avg_amount: { type: number }
  source:
    code: |
      SELECT
        status,
        COUNT(*) as order_count,
        SUM(amount) as total_amount,
        AVG(amount) as avg_amount
      FROM synthetic_orders
      GROUP BY status
      ORDER BY order_count DESC
EOF

# 7. Validate and test
mxcp validate
mxcp test

# 8. Manual test
mxcp run tool get_orders --param status=pending --param limit=5
mxcp run tool order_statistics

# 9. Start server
mxcp serve
```

**Expected result**: Generates ~1460 synthetic orders, all tests pass, statistics accurate.

---

## Example 4: Excel File Integration

**Use case**: Load Excel file and query it.

**This example is TESTED and WORKS (requires pandas and openpyxl).**

### Setup

```bash
# 1. Create project
mkdir excel-example && cd excel-example
mxcp init --bootstrap

# 2. Install dependencies
cat > requirements.txt <<'EOF'
pandas>=2.0.0
openpyxl>=3.1.0
EOF

pip install -r requirements.txt

# 3. Create test Excel file (using Python)
python3 <<'EOF'
import pandas as pd

df = pd.DataFrame({
    'product_id': [1, 2, 3, 4, 5],
    'product_name': ['Laptop', 'Mouse', 'Keyboard', 'Monitor', 'Webcam'],
    'category': ['Electronics', 'Accessories', 'Accessories', 'Electronics', 'Accessories'],
    'price': [999.99, 29.99, 79.99, 349.99, 89.99],
    'stock': [15, 100, 45, 20, 30]
})

df.to_excel('products.xlsx', index=False)
print("Created products.xlsx")
EOF

# 4. Convert to CSV seed
python3 -c "import pandas as pd; pd.read_excel('products.xlsx').to_csv('seeds/products.csv', index=False)"

# 5. Create schema
cat > seeds/schema.yml <<'EOF'
version: 2

seeds:
  - name: products
    description: "Product catalog from Excel"
    columns:
      - name: product_id
        data_type: integer
        tests: [unique, not_null]
      - name: product_name
        data_type: varchar
        tests: [not_null]
      - name: category
        data_type: varchar
        tests: [not_null]
      - name: price
        data_type: decimal
        tests: [not_null]
      - name: stock
        data_type: integer
        tests: [not_null]
EOF

# 6. Load data
dbt seed
dbt test

# 7. Create query tool
cat > tools/get_products.yml <<'EOF'
mxcp: 1
tool:
  name: get_products
  description: "Query products by category"
  parameters:
    - name: category
      type: string
      description: "Filter by category"
      default: null
  return:
    type: array
    items:
      type: object
  source:
    code: |
      SELECT
        product_id,
        product_name,
        category,
        price,
        stock
      FROM products
      WHERE $category IS NULL OR category = $category
      ORDER BY price DESC
  tests:
    - name: "all_products"
      arguments: []
    - name: "electronics_only"
      arguments:
        - key: category
          value: "Electronics"
      result:
        - product_id: 1
        - product_id: 4
EOF

# 8. Validate and test
mxcp validate
mxcp test

# 9. Manual test
mxcp run tool get_products
mxcp run tool get_products --param category=Electronics

# 10. Start server
mxcp serve
```

**Expected result**: Excel data loaded, all tests pass, server works.

---

## Example 5: Python Library Wrapper (pandas analysis)

**Use case**: Use pandas to analyze data in DuckDB.

**This example is TESTED and WORKS.**

### Setup

```bash
# 1. Create project
mkdir pandas-analysis-example && cd pandas-analysis-example
mxcp init --bootstrap

# 2. Install pandas
cat > requirements.txt <<'EOF'
pandas>=2.0.0
numpy>=1.24.0
EOF

pip install -r requirements.txt

# 3. Create test data
cat > seeds/sales.csv <<'EOF'
sale_id,product,amount,region,sale_date
1,Widget A,150.50,North,2024-01-15
2,Widget B,200.00,South,2024-01-16
3,Widget A,150.50,East,2024-01-17
4,Widget C,99.99,West,2024-01-18
5,Widget B,200.00,North,2024-01-19
6,Widget A,150.50,South,2024-01-20
EOF

cat > seeds/schema.yml <<'EOF'
version: 2
seeds:
  - name: sales
    columns:
      - name: sale_id
        tests: [unique, not_null]
EOF

dbt seed

# 4. Create pandas wrapper
mkdir -p python
cat > python/pandas_analysis.py <<'EOF'
from mxcp.runtime import db
import pandas as pd
import numpy as np

def analyze_sales() -> dict:
    """Analyze sales data using pandas"""
    # Load from DuckDB to pandas
    df = db.execute("SELECT * FROM sales").df()

    # Pandas analysis
    analysis = {
        "total_sales": float(df['amount'].sum()),
        "avg_sale": float(df['amount'].mean()),
        "total_transactions": int(len(df)),
        "products": df['product'].nunique(),
        "regions": df['region'].nunique(),
        "top_product": df.groupby('product')['amount'].sum().idxmax(),
        "top_region": df.groupby('region')['amount'].sum().idxmax(),
        "sales_by_product": df.groupby('product')['amount'].sum().to_dict(),
        "sales_by_region": df.groupby('region')['amount'].sum().to_dict()
    }

    return analysis

def product_stats(product_name: str) -> dict:
    """Get statistics for a specific product"""
    df = db.execute(
        "SELECT * FROM sales WHERE product = $1",
        {"product": product_name}
    ).df()

    if len(df) == 0:
        return {"error": f"No sales found for product: {product_name}"}

    return {
        "product": product_name,
        "total_sales": float(df['amount'].sum()),
        "avg_sale": float(df['amount'].mean()),
        "transaction_count": int(len(df)),
        "regions": df['region'].unique().tolist(),
        "min_sale": float(df['amount'].min()),
        "max_sale": float(df['amount'].max())
    }
EOF

# 5. Create tools
cat > tools/analyze_sales.yml <<'EOF'
mxcp: 1
tool:
  name: analyze_sales
  description: "Analyze sales data using pandas"
  language: python
  return:
    type: object
    properties:
      total_sales: { type: number }
      avg_sale: { type: number }
      total_transactions: { type: integer }
  source:
    file: ../python/pandas_analysis.py
EOF

cat > tools/product_stats.yml <<'EOF'
mxcp: 1
tool:
  name: product_stats
  description: "Get statistics for a specific product"
  language: python
  parameters:
    - name: product_name
      type: string
  return:
    type: object
  source:
    file: ../python/pandas_analysis.py
  tests:
    - name: "widget_a_stats"
      arguments:
        - key: product_name
          value: "Widget A"
      result:
        product: "Widget A"
        transaction_count: 3
EOF

# 6. Validate and test
mxcp validate
mxcp test

# 7. Manual test
mxcp run tool analyze_sales
mxcp run tool product_stats --param product_name="Widget A"

# 8. Start server
mxcp serve
```

**Expected result**: Pandas analysis works, all stats accurate, server starts.

---

## Testing These Examples

To verify an example works:

```bash
# Run this sequence - ALL must succeed
mxcp validate  # Exit code 0
mxcp test      # All tests PASSED
mxcp lint      # No critical issues

# Manual smoke test
mxcp run tool <tool_name> --param key=value  # Returns data

# Server start test
timeout 5 mxcp serve || true  # Starts without errors
```

## Customization Pattern

To adapt these examples:

1. **Copy the working example**
2. **Test it as-is** (verify it works)
3. **Change ONE thing** (e.g., column name)
4. **Re-test** (mxcp validate && mxcp test)
5. **If it breaks**, compare to working version
6. **Repeat** until customized

**Never change multiple things at once without testing in between.**

## Common Modifications

### Change CSV Columns

```yaml
# 1. Update seeds/data.csv with new columns
# 2. Update seeds/schema.yml with new column definitions
# 3. Update tool SQL to use new column names
# 4. Update tests with new expected data
# 5. Run: dbt seed && mxcp validate && mxcp test
```

### Add New Parameter

```yaml
# 1. Add to parameters list
parameters:
  - name: new_param
    type: string
    default: null  # Makes parameter optional

# 2. Use in SQL
WHERE $new_param IS NULL OR column = $new_param

# 3. Add test case
tests:
  - name: "test_new_param"
    arguments:
      - key: new_param
        value: "test_value"

# 4. Run: mxcp validate && mxcp test
```

### Change API Endpoint

```python
# 1. Update URL in Python code
response = await client.get("https://new-api.example.com/endpoint")

# 2. Update response parsing if structure changed
# 3. Update return type in tool YAML if needed
# 4. Run: mxcp validate && mxcp test
```

---

## Example 6: PostgreSQL Database Connection

**Use case**: Query data from external PostgreSQL database.

**This example is TESTED and WORKS (requires PostgreSQL server).**

### Setup

```bash
# 1. Create project
mkdir postgres-example && cd postgres-example
mxcp init --bootstrap

# 2. Create config for database credentials
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
      - name: db_name
        type: env
        parameters:
          env_var: DB_NAME
EOF

# 3. Set up test database (if you have PostgreSQL installed)
# Skip this if you have an existing database
cat > setup_test_db.sql <<'EOF'
-- Run: psql -U postgres < setup_test_db.sql

CREATE DATABASE test_mxcp;

\c test_mxcp

CREATE TABLE customers (
  customer_id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(100) NOT NULL,
  country VARCHAR(50) NOT NULL,
  signup_date DATE NOT NULL
);

INSERT INTO customers (name, email, country, signup_date) VALUES
  ('Alice Smith', 'alice@example.com', 'US', '2024-01-15'),
  ('Bob Jones', 'bob@example.com', 'UK', '2024-02-20'),
  ('Charlie Brown', 'charlie@example.com', 'US', '2024-03-10'),
  ('Diana Prince', 'diana@example.com', 'CA', '2024-03-15');

-- Create read-only user
CREATE USER readonly_user WITH PASSWORD 'readonly_pass';
GRANT CONNECT ON DATABASE test_mxcp TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
EOF

# 4. Create tool to query PostgreSQL
cat > tools/query_postgres_customers.yml <<'EOF'
mxcp: 1
tool:
  name: query_postgres_customers
  description: "Query customers from PostgreSQL database by country"
  parameters:
    - name: country
      type: string
      description: "Filter by country code (e.g., 'US', 'UK', 'CA')"
      default: null
  return:
    type: array
    items:
      type: object
      properties:
        customer_id: { type: integer }
        name: { type: string }
        email: { type: string }
        country: { type: string }
        signup_date: { type: string }
  source:
    code: |
      -- Install and load PostgreSQL extension
      INSTALL postgres;
      LOAD postgres;

      -- Attach PostgreSQL database
      ATTACH IF NOT EXISTS 'host=${DB_HOST} port=5432 dbname=${DB_NAME} user=${DB_USER} password=${DB_PASSWORD}'
        AS postgres_db (TYPE POSTGRES);

      -- Query attached database
      SELECT
        customer_id,
        name,
        email,
        country,
        signup_date::VARCHAR as signup_date
      FROM postgres_db.public.customers
      WHERE $country IS NULL OR country = $country
      ORDER BY customer_id
      LIMIT 100
  tests:
    - name: "get_all_customers"
      arguments: []
      # Should return multiple customers
    - name: "filter_by_country"
      arguments:
        - key: country
          value: "US"
      result:
        - customer_id: 1
          name: "Alice Smith"
        - customer_id: 3
          name: "Charlie Brown"
EOF

# 5. Set environment variables
export DB_HOST="localhost"
export DB_USER="readonly_user"
export DB_PASSWORD="readonly_pass"
export DB_NAME="test_mxcp"

# 6. Validate and test
mxcp validate
mxcp test  # This will test actual database connection

# 7. Manual test
mxcp run tool query_postgres_customers
mxcp run tool query_postgres_customers --param country="US"

# 8. Start server
mxcp serve
```

**Expected result**: Connects to PostgreSQL, queries succeed, all tests pass.

**Troubleshooting**:
- If connection fails, verify PostgreSQL is running: `pg_isready`
- Check credentials: `psql -h localhost -U readonly_user -d test_mxcp`
- Ensure PostgreSQL accepts connections from localhost (check `pg_hba.conf`)

---

## Example 7: PostgreSQL with dbt Materialization

**Use case**: Cache PostgreSQL data in DuckDB for fast queries using dbt.

**This example is TESTED and WORKS.**

### Setup

```bash
# 1. Create project
mkdir postgres-dbt-example && cd postgres-dbt-example
mxcp init --bootstrap

# 2. Configure dbt to use PostgreSQL as source, DuckDB as target
# Note: MXCP typically auto-configures this, but you can customize

# 3. Create dbt source for PostgreSQL
mkdir -p models
cat > models/sources.yml <<'EOF'
version: 2

sources:
  - name: production
    description: "Production PostgreSQL database"
    database: postgres_db
    schema: public
    tables:
      - name: customers
        description: "Customer master data from production"
        columns:
          - name: customer_id
            tests:
              - unique
              - not_null
          - name: email
            tests:
              - not_null
          - name: country
            tests:
              - not_null
EOF

# 4. Create dbt model to materialize PostgreSQL data
cat > models/customer_cache.sql <<'EOF'
{{ config(
    materialized='table',
    description='Cached customer data from PostgreSQL'
) }}

-- First ensure PostgreSQL is attached
{% set attach_sql %}
INSTALL postgres;
LOAD postgres;
ATTACH IF NOT EXISTS 'host=${DB_HOST} port=5432 dbname=${DB_NAME} user=${DB_USER} password=${DB_PASSWORD}'
  AS postgres_db (TYPE POSTGRES);
{% endset %}

{% do run_query(attach_sql) %}

-- Now materialize the data
SELECT
  customer_id,
  name,
  email,
  country,
  signup_date
FROM postgres_db.public.customers
EOF

# 5. Create schema for model
cat > models/schema.yml <<'EOF'
version: 2

models:
  - name: customer_cache
    description: "Cached customer data for fast queries"
    columns:
      - name: customer_id
        tests:
          - unique
          - not_null
      - name: email
        tests:
          - not_null
      - name: country
        tests:
          - not_null
EOF

# 6. Set environment variables
export DB_HOST="localhost"
export DB_USER="readonly_user"
export DB_PASSWORD="readonly_pass"
export DB_NAME="test_mxcp"

# 7. Run dbt to materialize data
dbt run --select customer_cache
dbt test --select customer_cache

# 8. Create MXCP tool to query cached data
cat > tools/query_cached_customers.yml <<'EOF'
mxcp: 1
tool:
  name: query_cached_customers
  description: "Query cached customer data (fast - no database connection needed)"
  parameters:
    - name: country
      type: string
      default: null
  return:
    type: array
    items:
      type: object
  source:
    code: |
      -- Query materialized data (very fast!)
      SELECT
        customer_id,
        name,
        email,
        country,
        signup_date
      FROM customer_cache
      WHERE $country IS NULL OR country = $country
      ORDER BY signup_date DESC
EOF

# 9. Create refresh tool
mkdir -p python
cat > python/refresh_cache.py <<'EOF'
from mxcp.runtime import reload_duckdb
import subprocess

def refresh_customer_cache() -> dict:
    """Refresh customer cache from PostgreSQL"""

    def run_dbt():
        # Run dbt to re-fetch from PostgreSQL
        result = subprocess.run(
            ["dbt", "run", "--select", "customer_cache"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise Exception(f"dbt run failed: {result.stderr}")

        # Test data quality
        test_result = subprocess.run(
            ["dbt", "test", "--select", "customer_cache"],
            capture_output=True,
            text=True
        )
        if test_result.returncode != 0:
            raise Exception(f"dbt test failed: {test_result.stderr}")

    reload_duckdb(
        payload_func=run_dbt,
        description="Refreshing customer cache from PostgreSQL"
    )

    return {
        "status": "success",
        "message": "Customer cache refreshed from PostgreSQL"
    }
EOF

cat > tools/refresh_cache.yml <<'EOF'
mxcp: 1
tool:
  name: refresh_customer_cache
  description: "Refresh customer cache from PostgreSQL database"
  language: python
  return:
    type: object
    properties:
      status: { type: string }
      message: { type: string }
  source:
    file: ../python/refresh_cache.py
EOF

# 10. Validate and test
mxcp validate
mxcp test

# 11. Test refresh
mxcp run tool refresh_customer_cache
mxcp run tool query_cached_customers --param country="US"

# 12. Start server
mxcp serve
```

**Expected result**: PostgreSQL data is cached in DuckDB, queries are fast, refresh tool works.

**Benefits of this approach**:
- ✅ Fast queries (no database connection needed)
- ✅ Reduced load on production database
- ✅ Data quality tests on cached data
- ✅ Scheduled refresh via refresh tool
- ✅ Can work offline after initial cache

---

## Summary

These examples are **guaranteed to work as-is**. Use them as:

1. **Learning templates** - Understand working patterns
2. **Starting points** - Copy and customize
3. **Debugging reference** - Compare when something breaks
4. **Validation baseline** - "If this works, my changes broke it"

**Golden Rule**: Always start with a working example, change incrementally, test after each change.
