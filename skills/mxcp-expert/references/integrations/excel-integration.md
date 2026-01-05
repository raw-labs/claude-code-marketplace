---
title: "Excel Integration"
description: "Work with Excel files (.xlsx, .xls) in MXCP servers. Load spreadsheets into DuckDB, process multi-sheet workbooks, and build analytics tools."
sidebar:
  order: 5
---

> **Related Topics:** [DuckDB Integration](/integrations/duckdb) (database engine) | [Python Endpoints](/tutorials/python-endpoints) (Python tools) | [dbt Integration](/integrations/dbt) (seeds and models)

Guide for working with Excel files (.xlsx, .xls) in MXCP servers.

## Overview

Excel files are common data sources that can be integrated into MXCP servers.

**Recommended approach: Use dbt Python models** for loading Excel files. This provides:
- Automatic data cleaning and transformation
- Integration with dbt's testing framework
- Version-controlled transformation logic
- No manual conversion steps

**Avoid:** Converting Excel to CSV and using `dbt seed`. This adds unnecessary manual steps and loses Excel-specific handling (multiple sheets, formatting, type inference).

## Recommended: dbt Python Models

**This is the preferred approach for Excel files.**

```python
# models/load_sales_data.py
import pandas as pd

def model(dbt, session):
    """Load and clean Excel file."""
    df = pd.read_excel('data/sales.xlsx', sheet_name='Sales')

    # Clean data
    df = df.dropna(how='all')
    df.columns = df.columns.str.lower().str.replace(' ', '_')

    # Transform
    df['sale_date'] = pd.to_datetime(df['sale_date'])

    return df
```

Run with: `mxcp dbt run --select load_sales_data`

**Why Python models are better than CSV seeds:**
- No manual Excel → CSV conversion step
- Handles multiple sheets, formatting, dates automatically
- Transformation logic is version-controlled
- Data quality tests apply automatically
- Runs as part of the dbt DAG

## Alternative: Direct SQL Reading

For simple one-time queries, use DuckDB's Excel extension:

### DuckDB read_xlsx

DuckDB's spatial extension includes Excel support:

```sql
-- Read Excel file
SELECT * FROM read_xlsx('data.xlsx');

-- Read specific sheet
SELECT * FROM read_xlsx('report.xlsx', sheet='Data');

-- Read with options
SELECT * FROM read_xlsx('report.xlsx', sheet='Sales', header=true);
```

Enable the extension in `mxcp-site.yml`:

```yaml
extensions:
  - excel
```

### Method 2: Python with pandas

For more control over Excel processing:

```python
# python/excel_reader.py
from mxcp.runtime import db
import pandas as pd

def load_excel_to_duckdb(filepath: str, table_name: str, sheet_name: str = None) -> dict:
    """Load Excel file into DuckDB table"""
    df = pd.read_excel(filepath, sheet_name=sheet_name)
    db.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")
    return {
        "table": table_name,
        "rows": len(df),
        "columns": list(df.columns)
    }

def read_excel_data(filepath: str, sheet_name: str = None) -> list[dict]:
    """Read Excel and return as list of dicts"""
    df = pd.read_excel(filepath, sheet_name=sheet_name)
    return df.to_dict('records')
```

### Method 3: CSV Seeds (NOT Recommended for Excel)

**Avoid this approach for Excel files.** Use dbt Python models instead.

CSV seeds are only appropriate for:
- Small, static reference data (country codes, config values)
- Data that rarely changes and should be in version control
- Simple tabular data without formatting issues

```bash
# Only use for small static reference data, NOT for Excel files
python -c "import pandas as pd; pd.read_excel('data.xlsx').to_csv('seeds/data.csv', index=False)"
mxcp dbt seed
```

**Problems with this approach:**
- Manual conversion step that can be forgotten
- Loses Excel-specific handling (sheets, dates, formatting)
- CSV doesn't preserve data types
- Not suitable for data that changes

## Common Patterns

### Pattern 1: Excel Upload Tool

Create a tool for users to upload and query Excel files:

```yaml
# tools/upload_excel.yml
mxcp: 1
tool:
  name: upload_excel
  description: Load Excel file into queryable table
  language: python
  parameters:
    - name: filepath
      type: string
      description: Path to Excel file
    - name: sheet_name
      type: string
      required: false
      description: Sheet name (default: first sheet)
  return:
    type: object
    properties:
      table_name:
        type: string
      rows:
        type: integer
      columns:
        type: array
        items:
          type: string
  source:
    file: ../python/excel_loader.py
```

```python
# python/excel_loader.py
from mxcp.runtime import db
import pandas as pd
import os

def upload_excel(filepath: str, sheet_name: str = None) -> dict:
    """Load Excel file into DuckDB for querying"""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Excel file not found: {filepath}")

    df = pd.read_excel(filepath, sheet_name=sheet_name or 0)

    # Generate table name from filename
    table_name = os.path.splitext(os.path.basename(filepath))[0]
    table_name = table_name.replace('-', '_').replace(' ', '_').lower()

    db.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")

    return {
        "table_name": table_name,
        "rows": len(df),
        "columns": list(df.columns),
        "message": f"Query with: SELECT * FROM {table_name}"
    }
```

### Pattern 2: dbt Python Model for Complex Excel

Use dbt Python models for complex Excel transformations:

```python
# models/process_excel.py
import pandas as pd

def model(dbt, session):
    """Process Excel file with complex formatting."""
    df = pd.read_excel('data/sales_data.xlsx', sheet_name='Sales')

    # Clean data
    df = df.dropna(how='all')
    df.columns = df.columns.str.lower().str.replace(' ', '_')

    # Transform
    df['sale_date'] = pd.to_datetime(df['sale_date'])
    df['month'] = df['sale_date'].dt.to_period('M').astype(str)

    return df.groupby(['region', 'month']).agg({
        'amount': 'sum',
        'quantity': 'sum'
    }).reset_index()
```

### Pattern 3: Multi-Sheet Processing

Load all sheets from an Excel workbook:

```python
# python/multi_sheet_loader.py
from mxcp.runtime import db
import pandas as pd

def load_all_sheets(filepath: str) -> dict:
    """Load all sheets from Excel file as separate tables"""
    excel_file = pd.ExcelFile(filepath)
    results = {}

    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        table_name = sheet_name.lower().replace(' ', '_').replace('-', '_')

        db.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")

        results[sheet_name] = {
            "table_name": table_name,
            "rows": len(df),
            "columns": list(df.columns)
        }

    return {"sheets_loaded": len(results), "sheets": results}
```

### Pattern 4: Excel Statistics Tool

Provide statistics for uploaded Excel data:

```python
# python/excel_analytics.py
from mxcp.runtime import db

def get_statistics(table_name: str) -> dict:
    """Calculate statistics for numeric columns"""
    schema = db.execute(f"DESCRIBE {table_name}")
    numeric_cols = [
        c["column_name"] for c in schema
        if c["column_type"] in ('INTEGER', 'BIGINT', 'DOUBLE', 'DECIMAL', 'FLOAT')
    ]

    if not numeric_cols:
        return {"error": "No numeric columns found"}

    stats = []
    for col in numeric_cols:
        result = db.execute(f"""
            SELECT
                '{col}' as column_name,
                COUNT({col}) as count,
                AVG({col}) as mean,
                STDDEV({col}) as std_dev,
                MIN({col}) as min_value,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {col}) as median,
                MAX({col}) as max_value
            FROM {table_name}
        """)[0]
        stats.append(result)

    return {"statistics": stats}
```

## Data Cleaning

### Normalize Headers

Excel headers often need cleaning:

```python
def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize Excel column names for SQL compatibility"""
    df.columns = (
        df.columns
        .str.lower()
        .str.replace(' ', '_')
        .str.replace('-', '_')
        .str.replace('[^a-z0-9_]', '', regex=True)
    )
    return df
```

### Handle Empty Rows/Columns

```python
def clean_excel_data(filepath: str, sheet_name: str = None) -> pd.DataFrame:
    """Read and clean Excel data"""
    df = pd.read_excel(filepath, sheet_name=sheet_name)

    # Remove empty rows and columns
    df = df.dropna(how='all')
    df = df.dropna(axis=1, how='all')

    # Normalize headers
    df = normalize_headers(df)

    return df
```

### Fix Data Types

Excel types are unreliable:

```python
def clean_excel_types(df: pd.DataFrame) -> pd.DataFrame:
    """Clean common Excel type issues"""
    for col in df.columns:
        if df[col].dtype == 'object':
            # Try to convert dates
            try:
                df[col] = pd.to_datetime(df[col])
            except:
                # Strip whitespace from strings
                df[col] = df[col].str.strip()
    return df
```

## Dependencies

Add to your project's requirements:

```
openpyxl>=3.0.0    # For .xlsx files
xlrd>=2.0.0        # For .xls files (optional)
pandas>=2.0.0      # For Excel processing
```

## When to Use Each Approach

| Scenario | Approach |
|----------|----------|
| **Excel data loading (PREFERRED)** | **dbt Python model** |
| Simple one-time query | DuckDB `read_xlsx()` |
| User uploads at runtime | Python MXCP tool with pandas |
| Multi-sheet workbooks | dbt Python model or Python tool |
| Small static reference data (not Excel) | CSV → dbt seed |

**Default choice: dbt Python model.** Only use alternatives when you have a specific reason.

## Troubleshooting

### "No module named 'openpyxl'"

```bash
pip install openpyxl
```

### "Excel file empty after loading"

Check for empty rows/columns:

```python
df = df.dropna(how='all').dropna(axis=1, how='all')
```

### "Column names have special characters"

Use header normalization:

```python
df = normalize_headers(df)
```

### "Date columns appear as numbers"

Excel stores dates as serial numbers:

```python
df['date_col'] = pd.to_datetime(df['date_col'])
```

### "Out of memory with large Excel files"

Convert to CSV first, or process in chunks:

```python
# Convert to CSV for better performance
df = pd.read_excel('large.xlsx')
df.to_csv('large.csv', index=False)
# Then use dbt seed or read_csv()
```

## Best Practices

1. **Use dbt Python models for Excel** - Preferred approach for all Excel files
2. **Avoid CSV conversion** - Don't convert Excel → CSV → seed; use Python models directly
3. **Always clean Excel data** - Remove empty rows/columns, normalize headers in Python model
4. **Validate types** - Excel types are unreliable, validate and cast in transformation
5. **Use Python tools for runtime uploads** - When users upload files during operation
6. **Document expected format** - Tell users what Excel structure is expected
7. **Handle errors gracefully** - Excel files can be malformed

## Next Steps

- [DuckDB Integration](/integrations/duckdb) - SQL engine features
- [Python Endpoints](/tutorials/python-endpoints) - Build Python tools
- [dbt Integration](/integrations/dbt) - Data transformation
