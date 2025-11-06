# DuckDB Essentials for MXCP

Essential DuckDB knowledge for building MXCP servers with embedded analytics.

## What is DuckDB?

**DuckDB is an embedded, in-process SQL OLAP database** - think "SQLite for analytics". It runs directly in your MXCP server process without needing a separate database server.

**Key characteristics**:
- **Embedded**: No server setup, no configuration
- **Fast**: Vectorized execution engine, parallel processing
- **Versatile**: Reads CSV, Parquet, JSON directly from disk or URLs
- **SQL**: Full SQL support with analytical extensions
- **Portable**: Single-file database, easy to move/backup

**MXCP uses DuckDB by default** for all SQL-based tools and resources.

## Core Features for MXCP

### 1. Direct File Reading

**DuckDB can query files without importing them first**:

```sql
-- Query CSV directly
SELECT * FROM 'data/sales.csv'

-- Query with explicit reader
SELECT * FROM read_csv_auto('data/sales.csv')

-- Query Parquet
SELECT * FROM 'data/sales.parquet'

-- Query JSON
SELECT * FROM read_json_auto('data/events.json')

-- Query from URL
SELECT * FROM 'https://example.com/data.csv'
```

**Auto-detection**: DuckDB automatically infers:
- Column names from headers
- Data types from values
- CSV delimiters, quotes, etc.

### 2. CSV Import and Export

**Import CSV to table**:
```sql
-- Create table from CSV
CREATE TABLE sales AS
SELECT * FROM read_csv_auto('sales.csv')

-- Or use COPY
COPY sales FROM 'sales.csv' (AUTO_DETECT TRUE)
```

**Export to CSV**:
```sql
-- Export query results
COPY (SELECT * FROM sales WHERE region = 'US')
TO 'us_sales.csv' (HEADER, DELIMITER ',')
```

**CSV reading options**:
```sql
SELECT * FROM read_csv_auto(
  'data.csv',
  header = true,
  delim = ',',
  quote = '"',
  dateformat = '%Y-%m-%d'
)
```

### 3. Data Types

**Common DuckDB types** (important for MXCP type validation):

```sql
-- Numeric
INTEGER, BIGINT, DECIMAL(10,2), DOUBLE

-- String
VARCHAR, TEXT

-- Temporal
DATE, TIME, TIMESTAMP, INTERVAL

-- Complex
ARRAY, STRUCT, MAP, JSON

-- Boolean
BOOLEAN
```

**Type casting**:
```sql
-- Cast to specific type
SELECT CAST(amount AS DECIMAL(10,2)) FROM sales

-- Short syntax
SELECT amount::DECIMAL(10,2) FROM sales

-- Date parsing
SELECT CAST('2025-01-15' AS DATE)
```

### 4. SQL Extensions

**DuckDB adds useful SQL extensions beyond standard SQL**:

**EXCLUDE clause** (select all except):
```sql
-- Select all columns except sensitive ones
SELECT * EXCLUDE (ssn, salary) FROM employees
```

**REPLACE clause** (modify columns in SELECT *):
```sql
-- Replace amount with rounded version
SELECT * REPLACE (ROUND(amount, 2) AS amount) FROM sales
```

**List aggregation**:
```sql
-- Aggregate into arrays
SELECT
  region,
  LIST(product) AS products,
  LIST(DISTINCT customer) AS customers
FROM sales
GROUP BY region
```

**String aggregation**:
```sql
SELECT
  department,
  STRING_AGG(employee_name, ', ') AS team_members
FROM employees
GROUP BY department
```

### 5. Analytical Functions

**Window functions**:
```sql
-- Running totals
SELECT
  date,
  amount,
  SUM(amount) OVER (ORDER BY date) AS running_total
FROM sales

-- Ranking
SELECT
  product,
  sales,
  RANK() OVER (ORDER BY sales DESC) AS rank
FROM product_sales

-- Partitioned windows
SELECT
  region,
  product,
  sales,
  AVG(sales) OVER (PARTITION BY region) AS regional_avg
FROM sales
```

**Percentiles and statistics**:
```sql
SELECT
  PERCENTILE_CONT(0.5) AS median,
  PERCENTILE_CONT(0.95) AS p95,
  STDDEV(amount) AS std_dev,
  CORR(amount, quantity) AS correlation
FROM sales
```

### 6. Date and Time Functions

```sql
-- Current timestamp
SELECT CURRENT_TIMESTAMP

-- Date arithmetic
SELECT date + INTERVAL '7 days' AS next_week
SELECT date - INTERVAL '1 month' AS last_month

-- Date truncation
SELECT DATE_TRUNC('month', timestamp) AS month
SELECT DATE_TRUNC('week', timestamp) AS week

-- Date parts
SELECT
  YEAR(date) AS year,
  MONTH(date) AS month,
  DAYOFWEEK(date) AS day_of_week
```

### 7. JSON Support

**Parse JSON strings**:
```sql
-- Extract JSON fields
SELECT
  json_extract(data, '$.user_id') AS user_id,
  json_extract(data, '$.event_type') AS event_type
FROM events

-- Arrow notation (shorthand)
SELECT
  data->'user_id' AS user_id,
  data->>'event_type' AS event_type
FROM events
```

**Read JSON files**:
```sql
SELECT * FROM read_json_auto('events.json')
```

### 8. Performance Features

**Parallel execution** (automatic):
- DuckDB uses all CPU cores automatically
- No configuration needed

**Larger-than-memory processing**:
- Spills to disk when needed
- Handles datasets larger than RAM

**Columnar storage**:
- Efficient for analytical queries
- Fast aggregations and filters

**Indexes** (for point lookups):
```sql
CREATE INDEX idx_customer ON sales(customer_id)
```

## MXCP Integration

### Database Connection

**Automatic in MXCP** - no setup needed:
```yaml
# mxcp-site.yml
# DuckDB is the default, no configuration required
```

**Environment variable** for custom path:
```bash
export MXCP_DUCKDB_PATH="/path/to/data.duckdb"
mxcp serve
```

**Profile-specific databases**:
```yaml
# mxcp-site.yml
profiles:
  development:
    database:
      path: "dev.duckdb"
  production:
    database:
      path: "prod.duckdb"
```

### Using DuckDB in MXCP Tools

**Direct SQL queries**:
```yaml
# tools/query_sales.yml
mxcp: 1
tool:
  name: query_sales
  source:
    code: |
      SELECT
        region,
        SUM(amount) as total,
        COUNT(*) as count
      FROM sales
      WHERE sale_date >= $start_date
      GROUP BY region
      ORDER BY total DESC
```

**Query CSV files directly**:
```yaml
tool:
  name: analyze_upload
  source:
    code: |
      SELECT
        COUNT(*) as rows,
        COUNT(DISTINCT customer_id) as unique_customers,
        SUM(amount) as total_revenue
      FROM 'uploads/$filename'
```

**Complex analytical queries**:
```yaml
tool:
  name: customer_cohorts
  source:
    code: |
      WITH first_purchase AS (
        SELECT
          customer_id,
          MIN(DATE_TRUNC('month', purchase_date)) AS cohort_month
        FROM purchases
        GROUP BY customer_id
      ),
      cohort_size AS (
        SELECT
          cohort_month,
          COUNT(DISTINCT customer_id) AS cohort_size
        FROM first_purchase
        GROUP BY cohort_month
      )
      SELECT
        fp.cohort_month,
        DATE_TRUNC('month', p.purchase_date) AS activity_month,
        COUNT(DISTINCT p.customer_id) AS active_customers,
        cs.cohort_size,
        COUNT(DISTINCT p.customer_id)::FLOAT / cs.cohort_size AS retention_rate
      FROM purchases p
      JOIN first_purchase fp ON p.customer_id = fp.customer_id
      JOIN cohort_size cs ON fp.cohort_month = cs.cohort_month
      GROUP BY fp.cohort_month, activity_month, cs.cohort_size
      ORDER BY fp.cohort_month, activity_month
```

### Using DuckDB in Python Endpoints

**Access via MXCP runtime**:
```python
from mxcp.runtime import db

def analyze_data(region: str) -> dict:
    # Execute query
    result = db.execute(
        "SELECT SUM(amount) as total FROM sales WHERE region = $1",
        {"region": region}
    )

    # Fetch results
    row = result.fetchone()
    return {"total": row["total"]}

def batch_insert(records: list[dict]) -> dict:
    # Insert data
    db.execute(
        "INSERT INTO logs (timestamp, event) VALUES ($1, $2)",
        [(r["timestamp"], r["event"]) for r in records]
    )

    return {"inserted": len(records)}
```

**Read files in Python**:
```python
def import_csv(filepath: str) -> dict:
    # Create table from CSV
    db.execute(f"""
        CREATE TABLE imported_data AS
        SELECT * FROM read_csv_auto('{filepath}')
    """)

    # Get stats
    result = db.execute("SELECT COUNT(*) as count FROM imported_data")
    return {"rows_imported": result.fetchone()["count"]}
```

## Best Practices for MXCP

### 1. Use Parameter Binding

**ALWAYS use parameterized queries** to prevent SQL injection:

✅ **Correct**:
```yaml
source:
  code: |
    SELECT * FROM sales WHERE region = $region
```

❌ **WRONG** (SQL injection risk):
```yaml
source:
  code: |
    SELECT * FROM sales WHERE region = '$region'
```

### 2. Optimize Queries

**Index frequently filtered columns**:
```sql
CREATE INDEX idx_customer ON orders(customer_id)
CREATE INDEX idx_date ON orders(order_date)
```

**Use EXPLAIN to analyze queries**:
```sql
EXPLAIN SELECT * FROM large_table WHERE id = 123
```

**Materialize complex aggregations** (via dbt models):
```sql
-- Instead of computing on every query
-- Create a materialized view via dbt
CREATE TABLE daily_summary AS
SELECT
  DATE_TRUNC('day', timestamp) AS date,
  COUNT(*) AS count,
  SUM(amount) AS total
FROM transactions
GROUP BY date
```

### 3. Handle Large Datasets

**For large CSVs** (>100MB):
- Use Parquet format instead (much faster)
- Create tables rather than querying files directly
- Use dbt to materialize transformations

**Conversion to Parquet**:
```sql
COPY (SELECT * FROM 'large_data.csv')
TO 'large_data.parquet' (FORMAT PARQUET)
```

### 4. Data Types in MXCP

**Match DuckDB types to MXCP types**:

```yaml
# MXCP tool definition
parameters:
  - name: amount
    type: number        # → DuckDB DOUBLE
  - name: quantity
    type: integer       # → DuckDB INTEGER
  - name: description
    type: string        # → DuckDB VARCHAR
  - name: created_at
    type: string
    format: date-time   # → DuckDB TIMESTAMP
  - name: is_active
    type: boolean       # → DuckDB BOOLEAN
```

### 5. Database File Management

**Backup**:
```bash
# DuckDB is a single file - just copy it
cp data.duckdb data.duckdb.backup
```

**Export to SQL**:
```sql
EXPORT DATABASE 'backup_directory'
```

**Import from SQL**:
```sql
IMPORT DATABASE 'backup_directory'
```

## Common Patterns in MXCP

### Pattern 1: CSV → Table → Query

```bash
# 1. Load CSV via dbt seed
dbt seed --select customers

# 2. Query from MXCP tool
SELECT * FROM customers WHERE country = $country
```

### Pattern 2: External Data Caching

```sql
-- dbt model: cache_external_data.sql
{{ config(materialized='table') }}

SELECT * FROM read_csv_auto('https://example.com/data.csv')
```

### Pattern 3: Multi-File Aggregation

```sql
-- Query multiple CSVs
SELECT * FROM 'data/*.csv'

-- Union multiple Parquet files
SELECT * FROM 'archive/2025-*.parquet'
```

### Pattern 4: Real-time + Historical

```sql
-- Combine recent API data with historical cache
SELECT * FROM read_json_auto('https://api.com/recent')
UNION ALL
SELECT * FROM historical_data WHERE date < CURRENT_DATE - INTERVAL '7 days'
```

## Troubleshooting

**Issue**: "Table does not exist"
**Solution**: Ensure dbt models/seeds have been run, check table name spelling

**Issue**: "Type mismatch"
**Solution**: Add explicit CAST() or update schema.yml with correct data types

**Issue**: "Out of memory"
**Solution**: Reduce query scope, add WHERE filters, materialize intermediate results

**Issue**: "CSV parsing error"
**Solution**: Use read_csv_auto with explicit options (delim, quote, etc.)

**Issue**: "Slow queries"
**Solution**: Add indexes, materialize via dbt, use Parquet instead of CSV

## Summary for MXCP Builders

When building MXCP servers with DuckDB:

1. **Use parameterized queries** (`$param`) to prevent injection
2. **Load CSVs via dbt seeds** for version control and validation
3. **Materialize complex queries** as dbt models
4. **Index frequently filtered columns** for performance
5. **Use Parquet for large datasets** (>100MB)
6. **Match MXCP types to DuckDB types** in tool definitions
7. **Leverage DuckDB extensions** (EXCLUDE, REPLACE, window functions)

DuckDB is the powerhouse behind MXCP's data capabilities - understanding it enables building robust, high-performance MCP servers.
