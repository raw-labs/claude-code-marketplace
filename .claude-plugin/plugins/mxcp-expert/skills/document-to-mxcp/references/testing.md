# Testing Guide

Comprehensive guide for dbt and mxcp tests. **All tests are mandatory.**

## Table of Contents

1. [dbt Tests (Schema Validation)](#dbt-tests)
2. [MXCP Tests (Tool Behavior)](#mxcp-tests)
3. [Computing Ground Truth](#computing-ground-truth)
4. [Debugging Test Failures](#debugging-test-failures)

---

## dbt Tests

dbt tests validate data integrity in DuckDB tables.

### schema.yml Format

```yaml
version: 2

models:
  - name: load_sales_data
    description: "Sales transactions from sales_report.xlsx"
    columns:
      - name: order_id
        description: "Unique order identifier"
        tests:
          - not_null
          - unique
      - name: customer_id
        description: "Foreign key to customers table"
        tests:
          - not_null
          - relationships:
              to: ref('load_customers')
              field: customer_id
      - name: amount
        description: "Transaction amount in USD"
        tests:
          - not_null
      - name: status
        description: "Order status: pending, completed, cancelled"
        tests:
          - not_null
          - accepted_values:
              values: ['pending', 'completed', 'cancelled']
      - name: _rag_refs
        description: "JSON array of linked RAG chunk IDs"
```

### Common dbt Tests

| Test | Purpose | When to Use |
|------|---------|-------------|
| `not_null` | No NULL values | Primary keys, required fields |
| `unique` | No duplicates | Primary keys, unique identifiers |
| `relationships` | FK exists in other table | Foreign key columns |
| `accepted_values` | Only allowed values | Categorical/enum columns |

### Running dbt Tests

```bash
# Build models and run tests
mxcp dbt run && mxcp dbt test

# Run specific model tests
mxcp dbt test --select load_sales_data
```

---

## MXCP Tests

MXCP tests validate tool behavior with expected inputs/outputs.

### Tool YAML Test Format

```yaml
mxcp: 1
tool:
  name: get_customer_sales
  description: |
    Get total sales for a customer.
    Returns customer ID and total sales amount.
  parameters:
    - name: customer_id
      type: integer
      required: true
      description: "Customer ID to look up"
  return:
    type: object
    properties:
      customer_id: {type: integer}
      total_sales: {type: number}
      order_count: {type: integer}
  source:
    file: ../sql/get_customer_sales.sql
  tests:
    # Test 1: Customer with sales
    - name: customer_with_multiple_orders
      arguments:
        - {key: customer_id, value: 101}
      result:
        customer_id: 101
        total_sales: 15750.50
        order_count: 3

    # Test 2: Customer with single order
    - name: customer_with_single_order
      arguments:
        - {key: customer_id, value: 102}
      result:
        customer_id: 102
        total_sales: 500.00
        order_count: 1

    # Test 3: Customer with no sales (edge case)
    - name: customer_no_sales
      arguments:
        - {key: customer_id, value: 999}
      result:
        customer_id: 999
        total_sales: 0
        order_count: 0
```

### Required Test Cases

For each tool, include:

1. **Happy path** - Normal use case with expected data
2. **Edge cases** - Empty results, single result, boundary values
3. **Multiple results** - If tool returns lists, test with various counts

### RAG Cross-Reference Tool Tests

```yaml
mxcp: 1
tool:
  name: get_customer_docs
  description: |
    Get RAG document chunks related to a customer.
    Returns chunk IDs containing notes or analysis about this customer.
  parameters:
    - name: customer_id
      type: integer
      required: true
  return:
    type: object
    properties:
      customer_id: {type: integer}
      rag_chunks: {type: array, items: {type: string}}
  source:
    file: ../sql/get_customer_docs.sql
  tests:
    - name: customer_with_docs
      arguments:
        - {key: customer_id, value: 101}
      result:
        customer_id: 101
        rag_chunks: ["chunk_001", "chunk_003", "chunk_007"]

    - name: customer_no_docs
      arguments:
        - {key: customer_id, value: 999}
      result:
        customer_id: 999
        rag_chunks: []
```

### Running MXCP Tests

```bash
# Validate and run all tests
mxcp validate && mxcp test

# Run specific tool tests
mxcp test --tool get_customer_sales
```

---

## Computing Ground Truth

**Always compute expected values from source data BEFORE writing tests.**

### For Numeric Aggregations

```python
import pandas as pd

# Load source data
df = pd.read_excel('source_data/sales_report.xlsx')

# Compute expected values for test cases
customer_101_sales = df[df['customer_id'] == 101]['amount'].sum()
customer_101_count = df[df['customer_id'] == 101].shape[0]

print(f"Customer 101: total={customer_101_sales}, count={customer_101_count}")
# Output: Customer 101: total=15750.50, count=3
# Use these exact values in test result
```

### For RAG Link Tests

```python
import os
import json

# Load manifest
with open('rag_content/manifest.json') as f:
    manifest = json.load(f)

# Find chunks linked to customer 101
customer_chunks = []
for chunk_id, meta in manifest.get('chunks', {}).items():
    if 101 in meta.get('linked_ids', []):
        customer_chunks.append(chunk_id)

print(f"Customer 101 chunks: {customer_chunks}")
# Use this exact list in test result
```

### For Categorical Values

```python
# Get unique values for enum validation
statuses = df['status'].dropna().unique().tolist()
print(f"Valid statuses: {statuses}")
# Add these to accepted_values test
```

---

## Debugging Test Failures

### dbt Test Failures

```bash
# See which rows failed
mxcp dbt test --select load_sales_data --store-failures

# Query the failure table
duckdb data/db-default.duckdb -c "SELECT * FROM dbt_test__audit.not_null_load_sales_data_order_id"
```

**Common causes:**
- NULL values in source data not cleaned
- Duplicate primary keys from data merge
- FK references non-existent records
- Unexpected categorical values

### MXCP Test Failures

```bash
# Run with verbose output
mxcp test --verbose

# Test specific tool
mxcp test --tool get_customer_sales --verbose
```

**Common causes:**
- Expected value doesn't match actual (recompute from source)
- SQL returns wrong type (integer vs float)
- Empty result vs NULL handling
- JSON array formatting differences

### Investigation Process

1. **Re-verify from source**: Recompute expected value from original Excel/Word
2. **Check DuckDB data**: Query the table directly to verify data loaded correctly
3. **Compare types**: Ensure expected/actual have same types (15750 vs 15750.0)
4. **Fix root cause**: Never just change expected value to make test pass

```bash
# Direct DuckDB query to verify data
duckdb data/db-default.duckdb -c "
  SELECT customer_id, SUM(amount) as total, COUNT(*) as cnt
  FROM load_sales_data
  WHERE customer_id = 101
  GROUP BY customer_id
"
```

### Common Discrepancy Sources

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Row count differs | `dropna()` removed rows | Check for rows with all NaN |
| Sum differs | Type conversion | Check string-to-number conversion |
| Column not found | Name normalization | Check special chars, spaces |
| Duplicate rows | No dedup in model | Add `.drop_duplicates()` |
| NULL values | Empty cells | Check `fillna()` or `COALESCE` |
