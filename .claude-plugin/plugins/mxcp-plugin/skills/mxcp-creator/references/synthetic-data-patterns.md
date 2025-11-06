# Synthetic Data Generation Patterns

Guide for creating synthetic data in DuckDB and MXCP for testing, demos, and development.

## Overview

Synthetic data is useful for:
- **Testing** - Validate tools without real data
- **Demos** - Show functionality with realistic-looking data
- **Development** - Build endpoints before real data is available
- **Privacy** - Mask or replace sensitive data
- **Performance testing** - Generate large datasets

## DuckDB Synthetic Data Functions

### GENERATE_SERIES

**Create sequences of numbers or dates**:

```sql
-- Generate 1000 rows with sequential IDs
SELECT * FROM GENERATE_SERIES(1, 1000) AS t(id)

-- Generate date range
SELECT * FROM GENERATE_SERIES(
  DATE '2024-01-01',
  DATE '2024-12-31',
  INTERVAL '1 day'
) AS t(date)

-- Generate timestamp range (hourly)
SELECT * FROM GENERATE_SERIES(
  TIMESTAMP '2024-01-01 00:00:00',
  TIMESTAMP '2024-01-31 23:59:59',
  INTERVAL '1 hour'
) AS t(timestamp)
```

### Random Functions

**Generate random values**:

```sql
-- Random integer between 1 and 100
SELECT FLOOR(RANDOM() * 100 + 1)::INTEGER AS random_int

-- Random float between 0 and 1
SELECT RANDOM() AS random_float

-- Random UUID
SELECT UUID() AS id

-- Random boolean
SELECT RANDOM() < 0.5 AS random_bool

-- Random element from array
SELECT LIST_ELEMENT(['A', 'B', 'C'], FLOOR(RANDOM() * 3 + 1)::INTEGER) AS random_choice
```

### String Generation

```sql
-- Random string from characters
SELECT
  'USER_' || UUID() AS user_id,
  'user' || FLOOR(RANDOM() * 10000)::INTEGER || '@example.com' AS email,
  LIST_ELEMENT(['John', 'Jane', 'Alice', 'Bob'], FLOOR(RANDOM() * 4 + 1)::INTEGER) AS first_name,
  LIST_ELEMENT(['Smith', 'Doe', 'Johnson', 'Williams'], FLOOR(RANDOM() * 4 + 1)::INTEGER) AS last_name
```

## Common Synthetic Data Patterns

### Pattern 1: Customer Records

```sql
-- Generate 1000 synthetic customers
CREATE TABLE customers AS
SELECT
  ROW_NUMBER() OVER () AS customer_id,
  'CUST_' || UUID() AS customer_code,
  first_name || ' ' || last_name AS full_name,
  LOWER(first_name) || '.' || LOWER(last_name) || '@example.com' AS email,
  CASE
    WHEN RANDOM() < 0.3 THEN 'bronze'
    WHEN RANDOM() < 0.7 THEN 'silver'
    ELSE 'gold'
  END AS tier,
  DATE '2020-01-01' + (RANDOM() * 1460)::INTEGER * INTERVAL '1 day' AS signup_date,
  FLOOR(RANDOM() * 100000 + 10000)::INTEGER / 100.0 AS lifetime_value,
  RANDOM() < 0.9 AS is_active
FROM GENERATE_SERIES(1, 1000) AS t(id)
CROSS JOIN (
  SELECT unnest(['John', 'Jane', 'Alice', 'Bob', 'Charlie', 'Diana']) AS first_name
) AS names1
CROSS JOIN (
  SELECT unnest(['Smith', 'Doe', 'Johnson', 'Williams', 'Brown', 'Jones']) AS last_name
) AS names2
LIMIT 1000;
```

### Pattern 2: Transaction/Sales Data

```sql
-- Generate 10,000 synthetic transactions
CREATE TABLE transactions AS
SELECT
  ROW_NUMBER() OVER (ORDER BY transaction_date) AS transaction_id,
  'TXN_' || UUID() AS transaction_code,
  FLOOR(RANDOM() * 1000 + 1)::INTEGER AS customer_id,
  transaction_date,
  FLOOR(RANDOM() * 50000 + 1000)::INTEGER / 100.0 AS amount,
  LIST_ELEMENT(['credit_card', 'debit_card', 'bank_transfer', 'paypal'], FLOOR(RANDOM() * 4 + 1)::INTEGER) AS payment_method,
  LIST_ELEMENT(['completed', 'pending', 'failed'], FLOOR(RANDOM() * 10 + 1)::INTEGER) AS status,
  LIST_ELEMENT(['electronics', 'clothing', 'food', 'books', 'home'], FLOOR(RANDOM() * 5 + 1)::INTEGER) AS category
FROM GENERATE_SERIES(
  TIMESTAMP '2024-01-01 00:00:00',
  TIMESTAMP '2024-12-31 23:59:59',
  INTERVAL '52 minutes'  -- Roughly 10k records over a year
) AS t(transaction_date);
```

### Pattern 3: Time Series Data

```sql
-- Generate hourly metrics for a year
CREATE TABLE metrics AS
SELECT
  timestamp,
  -- Simulated daily pattern (peak at 2pm)
  50 + 30 * SIN(2 * PI() * EXTRACT(hour FROM timestamp) / 24 - PI()/2) + RANDOM() * 20 AS requests_per_min,
  -- Random response time between 50-500ms
  FLOOR(RANDOM() * 450 + 50)::INTEGER AS avg_response_ms,
  -- Error rate 0-5%
  RANDOM() * 5 AS error_rate,
  -- Random CPU usage
  FLOOR(RANDOM() * 60 + 20)::INTEGER AS cpu_usage_pct
FROM GENERATE_SERIES(
  TIMESTAMP '2024-01-01 00:00:00',
  TIMESTAMP '2024-12-31 23:59:59',
  INTERVAL '1 hour'
) AS t(timestamp);
```

### Pattern 4: Relational Data with Foreign Keys

```sql
-- Create related tables: Users → Orders → Order Items

-- Users
CREATE TABLE users AS
SELECT
  user_id,
  'user' || user_id || '@example.com' AS email,
  DATE '2020-01-01' + (RANDOM() * 1460)::INTEGER * INTERVAL '1 day' AS created_at
FROM GENERATE_SERIES(1, 100) AS t(user_id);

-- Orders
CREATE TABLE orders AS
SELECT
  order_id,
  FLOOR(RANDOM() * 100 + 1)::INTEGER AS user_id,  -- FK to users
  order_date,
  LIST_ELEMENT(['pending', 'shipped', 'delivered'], FLOOR(RANDOM() * 3 + 1)::INTEGER) AS status
FROM GENERATE_SERIES(1, 500) AS t(order_id)
CROSS JOIN (
  SELECT DATE '2024-01-01' + (RANDOM() * 365)::INTEGER * INTERVAL '1 day' AS order_date
) AS dates;

-- Order Items
CREATE TABLE order_items AS
SELECT
  ROW_NUMBER() OVER () AS item_id,
  order_id,
  'PRODUCT_' || FLOOR(RANDOM() * 50 + 1)::INTEGER AS product_id,
  FLOOR(RANDOM() * 5 + 1)::INTEGER AS quantity,
  FLOOR(RANDOM() * 20000 + 500)::INTEGER / 100.0 AS price
FROM orders
CROSS JOIN GENERATE_SERIES(1, FLOOR(RANDOM() * 5 + 1)::INTEGER) AS t(n);
```

### Pattern 5: Geographic Data

```sql
-- Generate synthetic locations
CREATE TABLE locations AS
SELECT
  location_id,
  LIST_ELEMENT(['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'], FLOOR(RANDOM() * 5 + 1)::INTEGER) AS city,
  LIST_ELEMENT(['NY', 'CA', 'IL', 'TX', 'AZ'], FLOOR(RANDOM() * 5 + 1)::INTEGER) AS state,
  -- Random US ZIP code
  LPAD(FLOOR(RANDOM() * 99999)::INTEGER::VARCHAR, 5, '0') AS zip_code,
  -- Random coordinates (simplified for demo)
  ROUND((RANDOM() * 50 + 25)::DECIMAL, 6) AS latitude,
  ROUND((RANDOM() * 60 - 125)::DECIMAL, 6) AS longitude
FROM GENERATE_SERIES(1, 200) AS t(location_id);
```

## MXCP Integration Patterns

### Pattern 1: dbt Model for Synthetic Data

**Use case**: Generate test data that persists across runs

```sql
-- models/synthetic_customers.sql
{{ config(materialized='table') }}

WITH name_options AS (
  SELECT unnest(['John', 'Jane', 'Alice', 'Bob', 'Charlie']) AS first_name
), surname_options AS (
  SELECT unnest(['Smith', 'Doe', 'Johnson', 'Brown']) AS last_name
)
SELECT
  ROW_NUMBER() OVER () AS customer_id,
  first_name || ' ' || last_name AS full_name,
  LOWER(first_name) || '.' || LOWER(last_name) || '@example.com' AS email,
  DATE '2020-01-01' + (RANDOM() * 1000)::INTEGER * INTERVAL '1 day' AS signup_date
FROM name_options
CROSS JOIN surname_options
CROSS JOIN GENERATE_SERIES(1, 50)  -- 5 * 4 * 50 = 1000 customers
```

```yaml
# models/schema.yml
version: 2

models:
  - name: synthetic_customers
    description: "Synthetic customer data for testing"
    columns:
      - name: customer_id
        tests: [unique, not_null]
      - name: email
        tests: [unique, not_null]
```

**Build and query**:
```bash
dbt run --select synthetic_customers
```

```yaml
# tools/query_test_customers.yml
mxcp: 1
tool:
  name: query_test_customers
  description: "Query synthetic customer data"
  return:
    type: array
  source:
    code: |
      SELECT * FROM synthetic_customers LIMIT 100
```

### Pattern 2: Python Tool for Dynamic Generation

**Use case**: Generate data on-the-fly based on parameters

```python
# python/data_generator.py
from mxcp.runtime import db
import uuid
from datetime import datetime, timedelta
import random

def generate_transactions(
    count: int = 100,
    start_date: str = "2024-01-01",
    end_date: str = "2024-12-31"
) -> dict:
    """Generate synthetic transaction data"""

    # Create temporary table
    table_name = f"temp_transactions_{uuid.uuid4().hex[:8]}"

    # Parse dates
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    date_range = (end - start).days

    db.execute(f"""
        CREATE TABLE {table_name} AS
        SELECT
          ROW_NUMBER() OVER () AS id,
          DATE '{start_date}' + (RANDOM() * {date_range})::INTEGER * INTERVAL '1 day' AS transaction_date,
          FLOOR(RANDOM() * 100000 + 1000)::INTEGER / 100.0 AS amount,
          LIST_ELEMENT(['completed', 'pending', 'failed'], FLOOR(RANDOM() * 10 + 1)::INTEGER) AS status
        FROM GENERATE_SERIES(1, {count})
    """)

    # Get sample
    sample = db.execute(f"SELECT * FROM {table_name} LIMIT 10").fetchall()

    return {
        "table_name": table_name,
        "rows_generated": count,
        "sample": sample,
        "query_hint": f"SELECT * FROM {table_name}"
    }

def generate_customers(count: int = 100) -> dict:
    """Generate synthetic customer records"""

    table_name = f"temp_customers_{uuid.uuid4().hex[:8]}"

    first_names = ['John', 'Jane', 'Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank']
    last_names = ['Smith', 'Doe', 'Johnson', 'Williams', 'Brown', 'Jones', 'Miller']
    tiers = ['bronze', 'silver', 'gold', 'platinum']

    db.execute(f"""
        CREATE TABLE {table_name} AS
        WITH names AS (
          SELECT
            unnest({first_names}) AS first_name,
            unnest({last_names}) AS last_name
        )
        SELECT
          ROW_NUMBER() OVER () AS customer_id,
          first_name || ' ' || last_name AS full_name,
          LOWER(first_name) || '.' || LOWER(last_name) || FLOOR(RANDOM() * 1000)::INTEGER || '@example.com' AS email,
          LIST_ELEMENT({tiers}, FLOOR(RANDOM() * {len(tiers)} + 1)::INTEGER) AS tier,
          DATE '2020-01-01' + (RANDOM() * 1460)::INTEGER * INTERVAL '1 day' AS created_at
        FROM names
        CROSS JOIN GENERATE_SERIES(1, CEIL({count} / (SELECT COUNT(*) FROM names))::INTEGER)
        LIMIT {count}
    """)

    stats = db.execute(f"""
        SELECT
          COUNT(*) as total,
          COUNT(DISTINCT tier) as tiers,
          MIN(created_at) as earliest,
          MAX(created_at) as latest
        FROM {table_name}
    """).fetchone()

    return {
        "table_name": table_name,
        "rows_generated": stats["total"],
        "statistics": dict(stats),
        "query_hint": f"SELECT * FROM {table_name}"
    }
```

```yaml
# tools/generate_test_data.yml
mxcp: 1
tool:
  name: generate_test_data
  description: "Generate synthetic data for testing"
  language: python
  parameters:
    - name: data_type
      type: string
      examples: ["transactions", "customers"]
    - name: count
      type: integer
      default: 100
  return:
    type: object
  source:
    file: ../python/data_generator.py
    function: |
      if data_type == "transactions":
          return generate_transactions(count)
      elif data_type == "customers":
          return generate_customers(count)
      else:
          raise ValueError(f"Unknown data_type: {data_type}")
```

### Pattern 3: Statistics Tool for Synthetic Data

**Use case**: Generate data and immediately calculate statistics

```yaml
# tools/synthetic_analytics.yml
mxcp: 1
tool:
  name: synthetic_analytics
  description: "Generate synthetic sales data and calculate statistics"
  language: python
  parameters:
    - name: days
      type: integer
      default: 365
    - name: transactions_per_day
      type: integer
      default: 100
  return:
    type: object
    properties:
      daily_stats: { type: array }
      overall_stats: { type: object }
  source:
    code: |
      from mxcp.runtime import db

      total = days * transactions_per_day

      # Generate data
      db.execute(f"""
        CREATE OR REPLACE TEMP TABLE temp_sales AS
        SELECT
          DATE '2024-01-01' + (RANDOM() * {days})::INTEGER * INTERVAL '1 day' AS sale_date,
          FLOOR(RANDOM() * 50000 + 1000)::INTEGER / 100.0 AS amount,
          LIST_ELEMENT(['online', 'retail', 'wholesale'], FLOOR(RANDOM() * 3 + 1)::INTEGER) AS channel
        FROM GENERATE_SERIES(1, {total})
      """)

      # Calculate statistics
      daily_stats = db.execute("""
        SELECT
          sale_date,
          COUNT(*) as transactions,
          SUM(amount) as total_sales,
          AVG(amount) as avg_sale
        FROM temp_sales
        GROUP BY sale_date
        ORDER BY sale_date
      """).fetchall()

      overall = db.execute("""
        SELECT
          COUNT(*) as total_transactions,
          SUM(amount) as total_revenue,
          AVG(amount) as avg_transaction,
          MIN(amount) as min_transaction,
          MAX(amount) as max_transaction,
          STDDEV(amount) as std_dev
        FROM temp_sales
      """).fetchone()

      return {
        "daily_stats": daily_stats,
        "overall_stats": dict(overall)
      }
```

## Advanced Patterns

### Realistic Distributions

**Normal distribution** (for things like heights, test scores):
```sql
-- Box-Muller transform for normal distribution
SELECT
  SQRT(-2 * LN(RANDOM())) * COS(2 * PI() * RANDOM()) * 15 + 100 AS iq_score
FROM GENERATE_SERIES(1, 1000)
```

**Power law distribution** (for things like city populations):
```sql
SELECT
  FLOOR(POWER(RANDOM(), -0.5) * 1000)::INTEGER AS followers
FROM GENERATE_SERIES(1, 1000)
```

**Seasonal patterns**:
```sql
-- Sales with seasonal pattern (peak in Dec, low in Feb)
SELECT
  date,
  -- Base level + seasonal component + random noise
  1000 + 500 * SIN(2 * PI() * EXTRACT(month FROM date) / 12 - PI()/2) + RANDOM() * 200 AS daily_sales
FROM GENERATE_SERIES(DATE '2024-01-01', DATE '2024-12-31', INTERVAL '1 day') AS t(date)
```

### Data Masking/Anonymization

**Replace real data with synthetic**:
```sql
-- Anonymize customer data
CREATE TABLE customers_anonymized AS
SELECT
  customer_id,  -- Keep ID for joins
  'USER_' || customer_id || '@example.com' AS email,  -- Fake email
  LIST_ELEMENT(['John', 'Jane', 'Alice', 'Bob'], (customer_id % 4) + 1) AS first_name,  -- Fake name
  LEFT(phone, 3) || '-XXX-XXXX' AS masked_phone,  -- Mask phone
  FLOOR(age / 10) * 10 AS age_bucket  -- Generalize age
FROM customers_real;
```

## Complete Example: Synthetic Analytics Server

**Scenario**: Demo server with synthetic e-commerce data

```bash
# Project structure
synthetic-analytics/
├── mxcp-site.yml
├── models/
│   ├── synthetic_customers.sql
│   ├── synthetic_orders.sql
│   └── schema.yml
├── python/
│   └── generators.py
└── tools/
    ├── generate_data.yml
    ├── customer_analytics.yml
    └── sales_trends.yml
```

```sql
-- models/synthetic_customers.sql
{{ config(materialized='table') }}

SELECT
  customer_id,
  'customer' || customer_id || '@example.com' AS email,
  LIST_ELEMENT(['bronze', 'silver', 'gold'], (customer_id % 3) + 1) AS tier,
  DATE '2020-01-01' + (RANDOM() * 1000)::INTEGER * INTERVAL '1 day' AS signup_date
FROM GENERATE_SERIES(1, 500) AS t(customer_id)
```

```sql
-- models/synthetic_orders.sql
{{ config(materialized='table') }}

SELECT
  order_id,
  FLOOR(RANDOM() * 500 + 1)::INTEGER AS customer_id,
  order_date,
  FLOOR(RANDOM() * 100000 + 1000)::INTEGER / 100.0 AS amount,
  LIST_ELEMENT(['completed', 'shipped', 'pending'], FLOOR(RANDOM() * 3 + 1)::INTEGER) AS status
FROM GENERATE_SERIES(1, 5000) AS t(order_id)
CROSS JOIN (
  SELECT DATE '2024-01-01' + (RANDOM() * 365)::INTEGER * INTERVAL '1 day' AS order_date
) AS dates
```

```yaml
# tools/customer_analytics.yml
mxcp: 1
tool:
  name: customer_analytics
  description: "Get customer analytics from synthetic data"
  parameters:
    - name: tier
      type: string
      required: false
  return:
    type: array
  source:
    code: |
      SELECT
        c.tier,
        COUNT(DISTINCT c.customer_id) as customers,
        COUNT(o.order_id) as total_orders,
        SUM(o.amount) as total_revenue,
        AVG(o.amount) as avg_order_value
      FROM synthetic_customers c
      LEFT JOIN synthetic_orders o ON c.customer_id = o.customer_id
      WHERE $tier IS NULL OR c.tier = $tier
      GROUP BY c.tier
      ORDER BY total_revenue DESC
```

## Best Practices

1. **Use dbt for persistent data**: Synthetic data that should be consistent across queries
2. **Use Python for dynamic data**: Data that changes based on parameters
3. **Seed random number generator**: For reproducible results, use `SETSEED()` in DuckDB
4. **Realistic distributions**: Use appropriate statistical distributions
5. **Maintain referential integrity**: Ensure foreign keys match
6. **Add noise**: Real data isn't perfectly distributed, add randomness
7. **Document data generation**: Explain how synthetic data was created
8. **Test with synthetic first**: Validate tools before using real data

## Summary

For synthetic data in MXCP:

1. **DuckDB patterns**: `GENERATE_SERIES`, `RANDOM()`, `LIST_ELEMENT()`, `UUID()`
2. **dbt models**: For persistent, version-controlled synthetic data
3. **Python tools**: For dynamic generation based on parameters
4. **Statistics**: Generate data → calculate metrics in one tool
5. **Testing**: Use synthetic data to test tools before real data
6. **Privacy**: Anonymize real data by generating synthetic replacements
