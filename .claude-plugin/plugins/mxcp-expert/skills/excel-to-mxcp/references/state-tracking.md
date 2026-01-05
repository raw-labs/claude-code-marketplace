# State Tracking Reference

## Table of Contents

- [Initial State](#initial-state)
- [State File Schema](#state-file-schema)
- [Primary Key Detection](#primary-key-detection)
- [Extend vs Create Logic](#extend-vs-create-logic)
- [Resolving Pending Relationships](#resolving-pending-relationships)

## Initial State

Create `ingestion_state.json` if it doesn't exist:

```json
{
  "last_updated": null,
  "tables": {},
  "relationships": [],
  "tools": [],
  "rag_chunks": {},
  "pending_relationships": []
}
```

## State File Schema

Full state example after processing:

```json
{
  "last_updated": "2024-01-15T10:30:00Z",
  "tables": {
    "customers": {
      "source": "sales_data.xlsx > Customers",
      "columns": ["id", "name", "email", "created_at"],
      "primary_key": "id",
      "row_count": 1247
    },
    "orders": {
      "source": "sales_data.xlsx > Orders",
      "columns": ["order_id", "customer_id", "amount", "order_date"],
      "primary_key": "order_id",
      "foreign_keys": {"customer_id": "customers.id"},
      "row_count": 5832
    }
  },
  "relationships": [
    {"from": "orders.customer_id", "to": "customers.id", "detected_from": "sales_data.xlsx"}
  ],
  "tools": ["get_customer_by_id", "search_customers", "get_orders_for_customer"],
  "rag_chunks": {
    "sales_notes": {"source": "sales_data.xlsx > Notes", "chunk_count": 5}
  },
  "pending_relationships": [
    {"table": "orders", "column": "product_id", "awaiting": "products"}
  ]
}
```

## Primary Key Detection

Don't assume PK is always "id". Detect it:

```python
def detect_primary_key(df, table_name):
    """Detect the primary key column for a table."""
    # Check common PK patterns
    pk_patterns = [
        'id',
        f'{table_name}_id',
        f'{table_name[:-1]}_id' if table_name.endswith('s') else None,
        'key',
        'code'
    ]

    for pattern in pk_patterns:
        if pattern and pattern in df.columns:
            if df[pattern].is_unique and df[pattern].notna().all():
                return pattern

    # Check for first unique column
    for col in df.columns:
        if df[col].is_unique and df[col].notna().all():
            return col

    return None  # No clear PK
```

## Extend vs Create Logic

```python
def should_extend_table(new_table, existing_state):
    """Determine if new data extends an existing table."""
    for table_name, table_info in existing_state["tables"].items():
        # Same name → extend
        if new_table["name"].lower() == table_name.lower():
            return table_name, "extend"

        # High column overlap (>70%) → likely same entity
        existing_cols = set(table_info["columns"])
        new_cols = set(new_table["columns"])
        overlap = len(existing_cols & new_cols) / max(len(existing_cols), len(new_cols))
        if overlap > 0.7:
            return table_name, "merge_candidate"

    return None, "create_new"
```

### Handling "extend"

When extending an existing table with same columns:

```python
# Option 1: Create UNION view
# models/customers_combined.sql
"""
SELECT * FROM {{ ref('load_file1_customers') }}
UNION ALL
SELECT * FROM {{ ref('load_file2_customers') }}
"""

# Option 2: Modify original model to read multiple files
# models/load_customers.py
def model(dbt, session):
    files = ['file1.xlsx', 'file2.xlsx']
    dfs = [pd.read_excel(f, sheet_name='Customers') for f in files]
    return pd.concat(dfs, ignore_index=True)
```

### Handling "merge_candidate"

When tables have overlapping but not identical columns:
1. Log as merge candidate in state
2. Review column mapping
3. May require user decision or heuristic merge

## Resolving Pending Relationships

When processing a new file, check if any pending relationships can now be resolved:

```python
def resolve_pending_relationships(new_tables, state):
    """Check if new tables satisfy pending FK relationships."""
    resolved = []
    remaining = []

    for pending in state["pending_relationships"]:
        matched = False
        for new_table in new_tables:
            # Check if new table matches awaited table
            if pending["awaiting"].lower() in new_table["name"].lower():
                # Use detected PK, not hardcoded "id"
                pk = new_table.get("primary_key", "id")
                resolved.append({
                    "from": f"{pending['table']}.{pending['column']}",
                    "to": f"{new_table['name']}.{pk}"
                })
                matched = True
                break

        if not matched:
            remaining.append(pending)

    return resolved, remaining
```
