# Validation Reference

Debugging helpers for investigating test failures.

## Query Data in DuckDB

```bash
mxcp query "SELECT COUNT(*) FROM {table}"
mxcp query "SELECT SUM({column}) FROM {table}"
mxcp query "SELECT * FROM {table} WHERE {pk} = {value}"
mxcp query "SELECT * FROM {table} LIMIT 5"
```

## Compare Source vs Database

```python
import pandas as pd
import subprocess
import json

# Source value
df = pd.read_excel('source.xlsx', sheet_name='Sheet1')
source_sum = df['amount'].sum()

# Database value
result = subprocess.run(
    ["mxcp", "query", "SELECT SUM(amount) as s FROM orders", "--format", "json"],
    capture_output=True, text=True
)
db_sum = json.loads(result.stdout)[0]["s"]

print(f"Source: {source_sum}, DB: {db_sum}, Match: {abs(source_sum - db_sum) < 0.01}")
```

## Common Discrepancy Sources

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Row count differs | `dropna()` removed rows | Check for rows with all NaN |
| Sum differs | Type conversion | Check string-to-number conversion |
| Column not found | Name normalization | Check special chars, spaces |
| Duplicate rows | No dedup in model | Add `.drop_duplicates()` |
| NULL values | Empty cells | Check `fillna()` or `COALESCE` |

## Validate Sample Rows

```python
def check_row(table, pk_col, pk_val, source_df):
    # Get from source
    expected = source_df[source_df[pk_col] == pk_val].to_dict('records')[0]

    # Get from DB
    result = subprocess.run(
        ["mxcp", "query", f"SELECT * FROM {table} WHERE {pk_col} = {pk_val}", "--format", "json"],
        capture_output=True, text=True
    )
    actual = json.loads(result.stdout)[0]

    # Compare
    for k, v in expected.items():
        if str(actual.get(k)) != str(v):
            print(f"Mismatch: {k} - expected {v}, got {actual.get(k)}")
```
