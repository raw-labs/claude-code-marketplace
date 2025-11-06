# dbt Core Guide for MXCP

Essential dbt (data build tool) knowledge for building MXCP servers.

## What is dbt?

dbt (data build tool) is a transformation workflow tool that enables data analysts and engineers to transform data in their data warehouse using SQL SELECT statements. In MXCP, dbt transforms raw data into clean, queryable tables that MXCP endpoints can access.

**Core principle**: dbt creates the tables → MXCP queries them

## Core Concepts

### 1. Seeds

**Seeds are CSV files** that dbt loads into your database as tables. They are perfect for:
- Static reference data (country codes, status mappings, etc.)
- Small lookup tables (<10,000 rows)
- User-provided data files that need to be queried

**Location**: Place CSV files in `seeds/` directory

**Loading seeds**:
```bash
dbt seed                    # Load all seeds
dbt seed --select my_file   # Load specific seed
mxcp dbt seed               # Load via MXCP
```

**Example use case**: User provides `customers.csv` → dbt loads it as a table → MXCP tools query it

**Critical for MXCP**: Seeds are the primary way to make CSV files queryable via MXCP tools.

### 2. Models

**Models are SQL SELECT statements** that transform data. Each `.sql` file in `models/` becomes a table or view.

**Basic model** (`models/customer_summary.sql`):
```sql
{{ config(materialized='table') }}

SELECT
  customer_id,
  COUNT(*) as order_count,
  SUM(amount) as total_spent
FROM {{ ref('orders') }}
GROUP BY customer_id
```

**Materialization types**:
- `table` - Creates a table (fast queries, slower builds)
- `view` - Creates a view (slow queries, instant builds)
- `incremental` - Appends new data only (best for large datasets)

### 3. Schema Files (schema.yml)

**Schema files define structure, tests, and documentation** for seeds and models.

**ALWAYS create schema.yml files** - they are critical for:
- Type validation
- Data quality tests
- Documentation
- Column descriptions

**Example** (`seeds/schema.yml`):
```yaml
version: 2

seeds:
  - name: customers
    description: "Customer master data from CSV upload"
    columns:
      - name: customer_id
        description: "Unique customer identifier"
        tests:
          - unique
          - not_null
      - name: email
        description: "Customer email address"
        tests:
          - not_null
      - name: created_at
        description: "Account creation timestamp"
        data_type: timestamp
```

**Example** (`models/schema.yml`):
```yaml
version: 2

models:
  - name: customer_summary
    description: "Aggregated customer metrics"
    columns:
      - name: customer_id
        tests:
          - unique
          - not_null
      - name: total_spent
        tests:
          - not_null
      - name: order_count
        tests:
          - not_null
```

### 4. Sources

**Sources represent raw data** already in your database (not managed by dbt).

**Example** (`models/sources.yml`):
```yaml
version: 2

sources:
  - name: raw_data
    tables:
      - name: transactions
        description: "Raw transaction data"
      - name: users
        description: "User accounts"
```

**Use in models**:
```sql
SELECT * FROM {{ source('raw_data', 'transactions') }}
```

## MXCP + dbt Workflow

### Pattern 1: CSV File to MXCP Tool

**User request**: "I need to query my sales.csv file"

**Steps**:

1. **Create seed** - Place `sales.csv` in `seeds/` directory
2. **Create schema** - Define structure in `seeds/schema.yml`:
   ```yaml
   version: 2

   seeds:
     - name: sales
       description: "Sales data from CSV upload"
       columns:
         - name: sale_id
           tests: [unique, not_null]
         - name: amount
           tests: [not_null]
         - name: sale_date
           data_type: date
           tests: [not_null]
         - name: region
           tests: [not_null]
   ```

3. **Load seed**:
   ```bash
   dbt seed --select sales
   ```

4. **Create MXCP tool** (`tools/get_sales.yml`):
   ```yaml
   mxcp: 1
   tool:
     name: get_sales
     description: "Query sales data by region and date range"
     parameters:
       - name: region
         type: string
         required: false
       - name: start_date
         type: string
         format: date
         required: false
       - name: end_date
         type: string
         format: date
         required: false
     return:
       type: array
       items:
         type: object
     source:
       code: |
         SELECT * FROM sales
         WHERE ($region IS NULL OR region = $region)
           AND ($start_date IS NULL OR sale_date >= $start_date)
           AND ($end_date IS NULL OR sale_date <= $end_date)
         ORDER BY sale_date DESC
   ```

5. **Test**:
   ```bash
   dbt test --select sales
   mxcp validate
   mxcp test tool get_sales
   ```

### Pattern 2: Transform Then Query

**User request**: "Analyze monthly sales trends from my CSV"

1. **Seed the raw data** (as above)
2. **Create transformation model** (`models/monthly_sales.sql`):
   ```sql
   {{ config(materialized='table') }}

   SELECT
     region,
     DATE_TRUNC('month', sale_date) as month,
     SUM(amount) as total_sales,
     COUNT(*) as transaction_count,
     AVG(amount) as avg_sale
   FROM {{ ref('sales') }}
   GROUP BY region, month
   ```

3. **Create schema** (`models/schema.yml`):
   ```yaml
   version: 2

   models:
     - name: monthly_sales
       description: "Monthly sales aggregations"
       columns:
         - name: region
           tests: [not_null]
         - name: month
           tests: [not_null]
         - name: total_sales
           tests: [not_null]
   ```

4. **Run dbt**:
   ```bash
   dbt seed
   dbt run --select monthly_sales
   dbt test --select monthly_sales
   ```

5. **Create MXCP tool** to query the model:
   ```yaml
   tool:
     name: monthly_trends
     source:
       code: |
         SELECT * FROM monthly_sales
         WHERE region = $region
         ORDER BY month DESC
   ```

## Project Structure

```
mxcp-project/
├── mxcp-site.yml           # MXCP configuration
├── dbt_project.yml         # dbt configuration
├── seeds/                  # CSV files
│   ├── customers.csv
│   └── schema.yml          # Seed schemas (REQUIRED)
├── models/                 # SQL transformations
│   ├── staging/
│   ├── intermediate/
│   ├── marts/
│   └── schema.yml          # Model schemas (REQUIRED)
├── tools/                  # MXCP tools that query seeds/models
└── target/                 # dbt build output (gitignored)
```

## dbt Commands for MXCP

```bash
# Initialize dbt project
dbt init

# Load CSV seeds into database
dbt seed                    # Load all seeds
dbt seed --select sales     # Load specific seed

# Run transformations
dbt run                     # Run all models
dbt run --select model_name # Run specific model
dbt run --select +model_name # Run model and upstream dependencies

# Test data quality
dbt test                    # Run all tests
dbt test --select sales     # Test specific seed/model

# Documentation
dbt docs generate           # Generate documentation
dbt docs serve              # Serve documentation site

# Via MXCP wrapper
mxcp dbt seed
mxcp dbt run
mxcp dbt test
```

## Schema.yml Best Practices

**ALWAYS include these in schema.yml**:

1. **Version declaration**: `version: 2`
2. **Description for every seed/model**: Helps LLMs and humans understand purpose
3. **Column-level descriptions**: Document what each field contains
4. **Data type declarations**: Ensure proper typing (`data_type: timestamp`, etc.)
5. **Tests for key columns**:
   - `unique` - No duplicates
   - `not_null` - Required field
   - `accepted_values` - Enum validation
   - `relationships` - Foreign key validation

**Example comprehensive schema.yml**:
```yaml
version: 2

seeds:
  - name: employees
    description: "Employee master data"
    columns:
      - name: employee_id
        description: "Unique employee identifier"
        data_type: varchar
        tests:
          - unique
          - not_null
      - name: department
        description: "Department code"
        data_type: varchar
        tests:
          - not_null
          - accepted_values:
              values: ['engineering', 'sales', 'marketing']
      - name: salary
        description: "Annual salary in USD"
        data_type: decimal
        tests:
          - not_null
      - name: hire_date
        description: "Date of hire"
        data_type: date
        tests:
          - not_null
```

## DuckDB Integration

MXCP uses **DuckDB** as its default database. dbt can target DuckDB directly.

**Auto-configured by MXCP** - no manual setup needed:
```yaml
# profiles.yml (auto-generated)
my_project:
  outputs:
    dev:
      type: duckdb
      path: "{{ env_var('MXCP_DUCKDB_PATH', 'data.duckdb') }}"
  target: dev
```

**DuckDB reads CSVs directly**:
```sql
-- In dbt models, you can read CSVs without seeding
SELECT * FROM read_csv_auto('path/to/file.csv')
```

**But prefer seeds for user data** - they provide version control and validation.

## Common Issues

**Issue**: Seed file not loading
**Solution**: Check CSV format, ensure no special characters in filename, verify schema.yml exists

**Issue**: Model not found
**Solution**: Run `dbt compile` to check for syntax errors, ensure model is in `models/` directory

**Issue**: Tests failing
**Solution**: Review test output, check data quality, adjust tests or fix data

**Issue**: Type errors
**Solution**: Add explicit `data_type` declarations in schema.yml

## Summary for MXCP Builders

When building MXCP servers:

1. **For CSV files** → Use dbt seeds
2. **Always create** `schema.yml` files with tests and types
3. **Load with** `dbt seed`
4. **Transform with** dbt models if needed
5. **Query from** MXCP tools using `SELECT * FROM <table>`
6. **Validate with** `dbt test` before deploying

This ensures data quality, type safety, and proper documentation for all data sources.
