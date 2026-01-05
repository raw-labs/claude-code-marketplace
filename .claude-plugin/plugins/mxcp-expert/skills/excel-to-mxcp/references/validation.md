# Validation Reference

## Table of Contents

- [Cross-Validation Approach](#cross-validation-approach)
- [Using mxcp query](#using-mxcp-query)
- [Validation Checks](#validation-checks)
- [Test Derivation by Tool Type](#test-derivation-by-tool-type)

## Cross-Validation Approach

Validate data from multiple angles to prove correctness. Compare source DataFrame values against database results.

## Using mxcp query

Use `mxcp query` to execute SQL and compare against pandas calculations:

```bash
# Row count
mxcp query "SELECT COUNT(*) as n FROM customers"

# Column sum
mxcp query "SELECT SUM(amount) as total FROM orders"

# Specific row lookup
mxcp query "SELECT * FROM customers WHERE id = 101"
```

## Validation Checks

### Row Count Validation

```python
import subprocess
import json

def validate_row_count(table_name, expected_count):
    """Validate table row count matches source."""
    result = subprocess.run(
        ["mxcp", "query", f"SELECT COUNT(*) as n FROM {table_name}", "--format", "json"],
        capture_output=True, text=True
    )
    actual = json.loads(result.stdout)[0]["n"]
    return {
        "check": "row_count",
        "table": table_name,
        "expected": expected_count,
        "actual": actual,
        "pass": actual == expected_count
    }
```

### Numeric Sum Validation

```python
def validate_column_sum(table_name, column_name, expected_sum):
    """Validate numeric column sum matches source."""
    result = subprocess.run(
        ["mxcp", "query", f"SELECT SUM({column_name}) as s FROM {table_name}", "--format", "json"],
        capture_output=True, text=True
    )
    actual = json.loads(result.stdout)[0]["s"]
    return {
        "check": f"sum_{column_name}",
        "table": table_name,
        "expected": expected_sum,
        "actual": actual,
        "pass": abs(float(actual or 0) - float(expected_sum)) < 0.01
    }
```

### Sample Row Validation

```python
def validate_sample_row(table_name, pk_column, pk_value, expected_row):
    """Validate a specific row matches source."""
    result = subprocess.run(
        ["mxcp", "query", f"SELECT * FROM {table_name} WHERE {pk_column} = {pk_value}", "--format", "json"],
        capture_output=True, text=True
    )
    rows = json.loads(result.stdout)
    actual = rows[0] if rows else None

    if actual is None and expected_row is None:
        return {"check": f"row_{pk_value}", "pass": True}

    if actual is None or expected_row is None:
        return {"check": f"row_{pk_value}", "expected": expected_row, "actual": actual, "pass": False}

    # Compare key fields (ignore minor floating point differences)
    matches = all(
        str(actual.get(k)) == str(v) or
        (isinstance(v, float) and abs(float(actual.get(k, 0)) - v) < 0.01)
        for k, v in expected_row.items()
    )

    return {
        "check": f"row_{pk_value}",
        "expected": expected_row,
        "actual": actual,
        "pass": matches
    }
```

### Full Cross-Validation

```python
def cross_validate(table_name, source_df, pk_column):
    """Run all validation checks for a table."""
    validations = []

    # Row count
    validations.append(validate_row_count(table_name, len(source_df)))

    # Numeric column sums
    for col in source_df.select_dtypes(include=['number']).columns:
        expected_sum = source_df[col].sum()
        validations.append(validate_column_sum(table_name, col, expected_sum))

    # Sample rows (5 random)
    if pk_column and pk_column in source_df.columns:
        sample_pks = source_df[pk_column].sample(min(5, len(source_df))).tolist()
        for pk_val in sample_pks:
            expected = source_df[source_df[pk_column] == pk_val].to_dict('records')[0]
            validations.append(validate_sample_row(table_name, pk_column, pk_val, expected))

    return validations
```

## Test Derivation by Tool Type

| Tool Type | How to Derive Expected Result |
|-----------|------------------------------|
| Lookup | Read specific row from source DataFrame |
| Aggregation | Calculate with pandas (sum, count, mean) |
| Join | pandas.merge() on source DataFrames |
| Search | Filter source DataFrame, verify matches |
| Time series | pandas groupby + agg on source |

### Example: Derive Expected Results

```python
def derive_expected_results(df, tool_type, **kwargs):
    """Calculate expected results from source data (ground truth)."""

    if tool_type == "lookup":
        pk_col = kwargs.get("pk_column", "id")
        pk_val = kwargs["pk_value"]
        rows = df[df[pk_col] == pk_val].to_dict('records')
        return rows[0] if rows else None

    elif tool_type == "aggregation":
        column = kwargs["column"]
        return {
            "total": int(df[column].sum()),
            "count": len(df),
            "average": round(float(df[column].mean()), 2)
        }

    elif tool_type == "search":
        search_col = kwargs["column"]
        search_val = kwargs["value"]
        matches = df[df[search_col].str.contains(search_val, case=False, na=False)]
        return matches.to_dict('records')

    elif tool_type == "join":
        df_a = kwargs["df_a"]
        df_b = kwargs["df_b"]
        join_key = kwargs["join_key"]
        merged = pd.merge(df_a, df_b, on=join_key)
        return merged.to_dict('records')

    elif tool_type == "group_by":
        group_col = kwargs["group_column"]
        agg_col = kwargs["agg_column"]
        agg_func = kwargs.get("agg_func", "sum")
        result = df.groupby(group_col)[agg_col].agg(agg_func).reset_index()
        return result.to_dict('records')
```

### Validation Report

```python
def generate_validation_report(tables_with_dfs):
    """Generate comprehensive validation report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "tables": [],
        "overall_status": "PASS"
    }

    for table_name, source_df, pk_column in tables_with_dfs:
        checks = cross_validate(table_name, source_df, pk_column)
        failed = [c for c in checks if not c["pass"]]

        table_report = {
            "table": table_name,
            "checks": checks,
            "passed": len(checks) - len(failed),
            "failed": len(failed),
            "status": "FAIL" if failed else "PASS"
        }

        if failed:
            table_report["failures"] = failed
            report["overall_status"] = "FAIL"

        report["tables"].append(table_report)

    return report
```
