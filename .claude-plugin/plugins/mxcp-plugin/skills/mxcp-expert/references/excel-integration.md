# Excel File Integration

Guide for working with Excel files (.xlsx, .xls) in MXCP servers.

## Overview

Excel files are common data sources that can be integrated into MXCP servers. DuckDB provides multiple ways to read Excel files, and dbt can be used to manage Excel data as seeds or sources.

## Reading Excel Files in DuckDB

### Method 1: Direct Reading with spatial Extension

DuckDB's spatial extension includes `st_read` which can read Excel files:

```sql
-- Install and load spatial extension (includes Excel support)
INSTALL spatial;
LOAD spatial;

-- Read Excel file
SELECT * FROM st_read('data.xlsx');

-- Read specific sheet
SELECT * FROM st_read('data.xlsx', layer='Sheet2');
```

### Method 2: Using Python with pandas

For more control, use Python with pandas:

```python
# python/excel_reader.py
from mxcp.runtime import db
import pandas as pd

def load_excel_to_duckdb(filepath: str, table_name: str, sheet_name: str = None) -> dict:
    """Load Excel file into DuckDB table"""
    # Read Excel with pandas
    df = pd.read_excel(filepath, sheet_name=sheet_name)

    # Register DataFrame in DuckDB
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

### Method 3: Convert to CSV, then use dbt seed

**Best practice for user-uploaded Excel files**:

```bash
# Convert Excel to CSV using Python
python -c "import pandas as pd; pd.read_excel('data.xlsx').to_csv('seeds/data.csv', index=False)"

# Then follow standard dbt seed workflow
cat > seeds/schema.yml <<EOF
version: 2
seeds:
  - name: data
    columns:
      - name: id
        tests: [unique, not_null]
EOF

dbt seed
```

## Common Patterns

### Pattern 1: Excel Upload → Query Tool

**User request**: "I have an Excel file with sales data, let me query it"

**Implementation**:

```yaml
# tools/upload_excel.yml
mxcp: 1
tool:
  name: upload_excel
  description: "Load Excel file into queryable table"
  language: python
  parameters:
    - name: filepath
      type: string
      description: "Path to Excel file"
    - name: sheet_name
      type: string
      required: false
      description: "Sheet name (default: first sheet)"
  return:
    type: object
    properties:
      table_name: { type: string }
      rows: { type: integer }
      columns: { type: array }
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

    # Read Excel
    df = pd.read_excel(filepath, sheet_name=sheet_name or 0)

    # Generate table name from filename
    table_name = os.path.splitext(os.path.basename(filepath))[0].replace('-', '_').replace(' ', '_')

    # Load into DuckDB
    db.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")

    return {
        "table_name": table_name,
        "rows": len(df),
        "columns": list(df.columns),
        "message": f"Excel loaded. Query with: SELECT * FROM {table_name}"
    }
```

```yaml
# tools/query_excel_data.yml
mxcp: 1
tool:
  name: query_excel_data
  description: "Query data from uploaded Excel file"
  parameters:
    - name: table_name
      type: string
      description: "Table name (from upload_excel result)"
    - name: filter_column
      type: string
      required: false
    - name: filter_value
      type: string
      required: false
  return:
    type: array
  source:
    code: |
      SELECT * FROM {{ table_name }}
      WHERE $filter_column IS NULL
         OR CAST({{ filter_column }} AS VARCHAR) = $filter_value
      LIMIT 1000
```

**Validation workflow for Pattern 1**:
```bash
# 1. Validate MXCP structure
mxcp validate

# 2. Test upload tool
mxcp test tool upload_excel

# 3. Manual test with real Excel file
mxcp run tool upload_excel --param filepath="./test.xlsx"

# 4. Test query tool
mxcp run tool query_excel_data --param table_name="test"

# 5. All validations must pass before deployment
```

### Pattern 2: Excel → dbt Python Model → Analytics

**User request**: "Process this Excel file with complex formatting and transform the data"

**RECOMMENDED for complex Excel processing** - Use dbt Python models when:
- Excel has complex formatting or multiple sheets
- Need pandas operations (pivoting, melting, complex string manipulation)
- Data cleaning requires Python logic

**Implementation**:

1. **Create dbt Python model** (`models/process_excel.py`):
```python
import pandas as pd

def model(dbt, session):
    # Read Excel file
    df = pd.read_excel('data/sales_data.xlsx', sheet_name='Sales')

    # Clean data
    df = df.dropna(how='all')  # Remove empty rows
    df = df.dropna(axis=1, how='all')  # Remove empty columns

    # Normalize column names
    df.columns = df.columns.str.lower().str.replace(' ', '_')

    # Complex transformations using pandas
    df['sale_date'] = pd.to_datetime(df['sale_date'])
    df['month'] = df['sale_date'].dt.to_period('M').astype(str)

    # Aggregate
    result = df.groupby(['region', 'month']).agg({
        'amount': 'sum',
        'quantity': 'sum'
    }).reset_index()

    return result  # Returns DataFrame that becomes a DuckDB table
```

2. **Create schema** (`models/schema.yml`):
```yaml
version: 2

models:
  - name: process_excel
    description: "Processed sales data from Excel"
    config:
      materialized: table
    columns:
      - name: region
        tests: [not_null]
      - name: month
        tests: [not_null]
      - name: amount
        tests: [not_null]
```

3. **Run the Python model**:
```bash
dbt run --select process_excel
dbt test --select process_excel
```

4. **Create MXCP tool**:
```yaml
# tools/sales_analytics.yml
mxcp: 1
tool:
  name: sales_analytics
  description: "Get processed sales data from Excel"
  parameters:
    - name: region
      type: string
      default: null
  return:
    type: array
  source:
    code: |
      SELECT * FROM process_excel
      WHERE $region IS NULL OR region = $region
      ORDER BY month DESC
```

5. **Validate**:
```bash
mxcp validate
mxcp test tool sales_analytics
```

### Pattern 3: Excel → dbt seed → Analytics

**User request**: "Analyze this Excel file with aggregations"

**Use this approach for simpler Excel files** - Convert to CSV first when:
- Excel file is simple with standard formatting
- Want version control for the data (CSV in git)
- Data is static and doesn't change

**Implementation**:

1. **Convert Excel to CSV seed**:
```bash
# One-time conversion
python -c "
import pandas as pd
df = pd.read_excel('sales_data.xlsx')
df.to_csv('seeds/sales_data.csv', index=False)
print(f'Converted {len(df)} rows')
"
```

2. **Create seed schema**:
```yaml
# seeds/schema.yml
version: 2

seeds:
  - name: sales_data
    description: "Sales data from Excel upload"
    columns:
      - name: sale_id
        tests: [unique, not_null]
      - name: sale_date
        data_type: date
        tests: [not_null]
      - name: amount
        data_type: decimal
        tests: [not_null]
      - name: region
        tests: [not_null]
      - name: product
        tests: [not_null]
```

3. **Load seed and validate**:
```bash
# Load CSV into DuckDB
dbt seed --select sales_data

# Run data quality tests
dbt test --select sales_data

# Verify data loaded correctly
dbt run-operation show_table --args '{"table_name": "sales_data"}'
```

**CRITICAL**: Always run `dbt test` after loading seeds to ensure data quality.

4. **Create analytics model**:
```sql
-- models/sales_analytics.sql
{{ config(materialized='table') }}

SELECT
  region,
  product,
  DATE_TRUNC('month', sale_date) as month,
  COUNT(*) as transaction_count,
  SUM(amount) as total_sales,
  AVG(amount) as avg_sale,
  MIN(amount) as min_sale,
  MAX(amount) as max_sale
FROM {{ ref('sales_data') }}
GROUP BY region, product, month
```

5. **Create query tool**:
```yaml
# tools/sales_analytics.yml
mxcp: 1
tool:
  name: sales_analytics
  description: "Get sales analytics by region and product"
  parameters:
    - name: region
      type: string
      required: false
    - name: product
      type: string
      required: false
  return:
    type: array
  source:
    code: |
      SELECT * FROM sales_analytics
      WHERE ($region IS NULL OR region = $region)
        AND ($product IS NULL OR product = $product)
      ORDER BY month DESC, total_sales DESC
```

6. **Validate and test MXCP tool**:
```bash
# Validate MXCP structure
mxcp validate

# Test tool execution
mxcp test tool sales_analytics

# Manual verification
mxcp run tool sales_analytics --param region="North"

# All checks must pass before deployment
```

### Pattern 4: Multi-Sheet Excel Processing

**User request**: "My Excel has multiple sheets, process them all"

```python
# python/multi_sheet_loader.py
from mxcp.runtime import db
import pandas as pd

def load_all_sheets(filepath: str) -> dict:
    """Load all sheets from Excel file as separate tables"""
    # Read all sheets
    excel_file = pd.ExcelFile(filepath)

    results = {}
    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(filepath, sheet_name=sheet_name)

        # Clean table name
        table_name = sheet_name.lower().replace(' ', '_').replace('-', '_')

        # Load to DuckDB
        db.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")

        results[sheet_name] = {
            "table_name": table_name,
            "rows": len(df),
            "columns": list(df.columns)
        }

    return {
        "sheets_loaded": len(results),
        "sheets": results
    }
```

## Excel-Specific Considerations

### Data Type Inference

Excel doesn't have strict types. Handle type ambiguity:

```python
def clean_excel_types(df: pd.DataFrame) -> pd.DataFrame:
    """Clean common Excel type issues"""
    for col in df.columns:
        # Convert Excel dates properly
        if df[col].dtype == 'object':
            try:
                df[col] = pd.to_datetime(df[col])
            except:
                pass

        # Strip whitespace from strings
        if df[col].dtype == 'object':
            df[col] = df[col].str.strip()

    return df
```

### Handling Headers

Excel files may have inconsistent headers:

```python
def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize Excel column names"""
    df.columns = (
        df.columns
        .str.lower()
        .str.replace(' ', '_')
        .str.replace('-', '_')
        .str.replace('[^a-z0-9_]', '', regex=True)
    )
    return df
```

### Empty Rows/Columns

Excel often has empty rows:

```python
def clean_excel_data(filepath: str, sheet_name: str = None) -> pd.DataFrame:
    """Read and clean Excel data"""
    df = pd.read_excel(filepath, sheet_name=sheet_name)

    # Remove completely empty rows
    df = df.dropna(how='all')

    # Remove completely empty columns
    df = df.dropna(axis=1, how='all')

    # Normalize headers
    df = normalize_headers(df)

    # Clean types
    df = clean_excel_types(df)

    return df
```

## Complete Example: Excel Analytics Server

**Scenario**: User uploads Excel file, wants to query and get statistics

```bash
# Project structure
excel-analytics/
├── mxcp-site.yml
├── python/
│   ├── excel_loader.py
│   └── excel_analytics.py
├── tools/
│   ├── load_excel.yml
│   ├── query_data.yml
│   └── get_statistics.yml
└── seeds/
    └── schema.yml (if using dbt seed approach)
```

**Implementation**:

```python
# python/excel_loader.py
from mxcp.runtime import db
import pandas as pd
import os

def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('[^a-z0-9_]', '', regex=True)
    return df

def load_excel(filepath: str, sheet_name: str = None) -> dict:
    """Load Excel file with cleaning"""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    # Read and clean
    df = pd.read_excel(filepath, sheet_name=sheet_name or 0)
    df = df.dropna(how='all').dropna(axis=1, how='all')
    df = normalize_headers(df)

    # Table name from filename
    table_name = os.path.splitext(os.path.basename(filepath))[0]
    table_name = table_name.lower().replace('-', '_').replace(' ', '_')

    # Load to DuckDB
    db.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")

    # Get column info
    col_info = db.execute(f"DESCRIBE {table_name}").fetchall()

    return {
        "table_name": table_name,
        "rows": len(df),
        "columns": [{"name": c["column_name"], "type": c["column_type"]} for c in col_info]
    }

def get_statistics(table_name: str, numeric_columns: list[str] = None) -> dict:
    """Calculate statistics for numeric columns"""
    # Get numeric columns if not specified
    if not numeric_columns:
        schema = db.execute(f"DESCRIBE {table_name}").fetchall()
        numeric_columns = [
            c["column_name"] for c in schema
            if c["column_type"] in ('INTEGER', 'BIGINT', 'DOUBLE', 'DECIMAL', 'FLOAT')
        ]

    if not numeric_columns:
        return {"error": "No numeric columns found"}

    # Build statistics query
    stats_parts = []
    for col in numeric_columns:
        stats_parts.append(f"""
            '{col}' as column,
            COUNT({col}) as count,
            AVG({col}) as mean,
            STDDEV({col}) as std_dev,
            MIN({col}) as min,
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {col}) as q25,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {col}) as median,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {col}) as q75,
            MAX({col}) as max
        """)

    query = f"""
        SELECT * FROM (
            {' UNION ALL '.join(f'SELECT {part} FROM {table_name}' for part in stats_parts)}
        )
    """

    results = db.execute(query).fetchall()
    return {"statistics": results}
```

```yaml
# tools/load_excel.yml
mxcp: 1
tool:
  name: load_excel
  description: "Load Excel file for querying and analysis"
  language: python
  parameters:
    - name: filepath
      type: string
      description: "Path to Excel file"
    - name: sheet_name
      type: string
      required: false
  return:
    type: object
  source:
    file: ../python/excel_loader.py
  tests:
    - name: "load_test_file"
      arguments:
        - key: filepath
          value: "test_data.xlsx"
      result:
        rows: 100
```

## Dependencies

Add to `requirements.txt`:
```
openpyxl>=3.0.0    # For .xlsx files
xlrd>=2.0.0        # For .xls files (optional)
pandas>=2.0.0      # For Excel processing
```

## Best Practices

1. **Always clean Excel data**: Remove empty rows/columns, normalize headers
2. **Type validation**: Excel types are unreliable, validate and cast
3. **Use dbt seeds for static data**: Convert Excel → CSV → seed for version control
4. **Use Python for dynamic uploads**: For user-uploaded files during runtime
5. **Document expected format**: Tell users what Excel structure is expected
6. **Error handling**: Excel files can be malformed, handle errors gracefully
7. **Sheet validation**: Check sheet names exist before processing
8. **Memory considerations**: Large Excel files can be slow, consider pagination

## Troubleshooting

**Issue**: "No module named 'openpyxl'"
**Solution**: `pip install openpyxl`

**Issue**: "Excel file empty after loading"
**Solution**: Check for empty rows/columns, use `dropna()`

**Issue**: "Column names have special characters"
**Solution**: Use `normalize_headers()` function

**Issue**: "Date columns appear as numbers"
**Solution**: Use `pd.to_datetime()` to convert Excel serial dates

**Issue**: "Out of memory with large Excel files"
**Solution**: Convert to CSV first, use dbt seed, or process in chunks

## Summary

For Excel integration in MXCP:

1. **User uploads** → Python tool with pandas → DuckDB table → Query tools
2. **Static data** → Convert to CSV → dbt seed → Schema validation → Query tools
3. **Multi-sheet** → Load all sheets as separate tables
4. **Always validate** → Clean headers, types, empty rows
5. **Add statistics tools** → Provide insights on numeric columns
