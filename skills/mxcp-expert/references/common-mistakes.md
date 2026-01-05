# Common Mistakes to Avoid

**Read this before creating any tools.** These mistakes cause validation errors.

## 1. Missing `tool:` Wrapper

```yaml
# WRONG
mxcp: 1
name: get_calendar
description: ...

# CORRECT
mxcp: 1
tool:
  name: get_calendar
  description: ...
```

## 2. Missing Parameter Description

```yaml
# WRONG - causes validation error
parameters:
  - name: user_id
    type: string

# CORRECT
parameters:
  - name: user_id
    type: string
    description: The unique user identifier
```

## 3. Invalid Type Names

Valid types: `string`, `number`, `integer`, `boolean`, `array`, `object`

```yaml
# WRONG
type: map      # Use 'object'
type: strng    # Typo
type: int      # Use 'integer'

# CORRECT
type: object
type: string
type: integer
```

## 4. Invalid Parameter Names

Parameter names must match `^[a-zA-Z_][a-zA-Z0-9_]*$`

```yaml
# WRONG
name: user-name    # Hyphens not allowed
name: 1st_param    # Can't start with number

# CORRECT
name: user_name
name: first_param
```

## 5. Invalid Format Values

Valid formats: `email`, `uri`, `date`, `time`, `date-time`, `duration`, `timestamp`

```yaml
# WRONG
format: datetime   # Missing hyphen

# CORRECT
format: date-time
```

## 6. Both `code` and `file` in Source

Source must have exactly one of `code` or `file`:

```yaml
# WRONG
source:
  code: "SELECT 1"
  file: "query.sql"  # Can't have both

# CORRECT
source:
  code: "SELECT 1"
# OR
source:
  file: ../sql/query.sql
```

## 7. Using `required: false` for Optional Parameters

MXCP uses `default` to make parameters optional, NOT `required: false`:

```yaml
# WRONG - required field doesn't exist
parameters:
  - name: limit
    type: integer
    required: false

# CORRECT - use default to make optional
parameters:
  - name: limit
    type: integer
    description: Max results to return
    default: 10
```

## 8. Missing `language: python` for Python Tools

Python tools MUST specify `language: python`:

```yaml
# WRONG - treated as SQL
tool:
  name: process_data
  source:
    file: ../python/process.py

# CORRECT
tool:
  name: process_data
  language: python
  source:
    file: ../python/process.py
```

## 9. Enum with Null Default

If `default: null`, the enum MUST include `null`:

```yaml
# WRONG - null not in enum
parameters:
  - name: status
    type: string
    enum: ["active", "inactive"]
    default: null

# CORRECT - either include null in enum
parameters:
  - name: status
    type: string
    enum: ["active", "inactive", null]
    default: null

# OR - remove default if null not allowed
parameters:
  - name: status
    type: string
    enum: ["active", "inactive"]
```

## 10. Invalid Test Assertions

Only these test assertions exist:

```yaml
# VALID assertions
tests:
  - name: test_user
    arguments: [{key: id, value: 1}]
    result: {"id": 1, "name": "Alice"}        # Exact match
    result_contains: {id: 1}                   # Partial match
    result_not_contains: ["password", "ssn"]   # Fields must NOT exist
    result_contains_item: {status: "active"}   # Array contains item
    result_contains_all: [{id: 1}, {id: 2}]    # Array contains all
    result_length: 5                           # Array length
    result_contains_text: "success"            # String contains

# WRONG - these don't exist
    expect_error: true           # NOT VALID
    result_count: 5              # NOT VALID (use result_length)
    result_count_min: 1          # NOT VALID
    result_matches: "pattern"    # NOT VALID
```

## 11. Type Mismatch with SQL Aggregates

DuckDB aggregate functions return floats. Cast to integer if needed:

```sql
-- WRONG - SUM returns float but declared as integer
SELECT SUM(quantity) as total FROM orders

-- CORRECT - cast to match declared type
SELECT CAST(SUM(quantity) AS INTEGER) as total FROM orders
SELECT CAST(COALESCE(SUM(quantity), 0) AS INTEGER) as total FROM orders
```

## 12. Custom Authentication Instead of Built-in

NEVER build custom auth. MXCP has built-in OAuth:

```yaml
# WRONG - custom API key table
tool:
  name: authenticate_user
  source:
    code: SELECT * FROM api_keys WHERE key = $api_key

# CORRECT - use built-in OAuth in ~/.mxcp/config.yml
# Then use policies for authorization
policies:
  input:
    - condition: "user.role != 'admin'"
      action: deny
```

## 13. Database-Specific SQL Syntax

DuckDB has its own SQL dialect. Verify syntax in [DuckDB docs](https://duckdb.org/docs/sql/introduction). Common issues:

```sql
-- WRONG - syntax from other databases
INSERT OR REPLACE INTO users VALUES (1, 'Alice');
INSERT OR IGNORE INTO users VALUES (1, 'Alice');

-- CORRECT - DuckDB syntax
INSERT INTO users VALUES (1, 'Alice')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;

-- OR use DELETE + INSERT
DELETE FROM users WHERE id = 1;
INSERT INTO users VALUES (1, 'Alice');
```

When in doubt, check [duckdb.md](duckdb.md) or the official DuckDB documentation.

## 14. Testing Policy Denials in YAML

Policy denial tests (where access is blocked) CANNOT be tested via YAML test assertions. Use CLI testing instead:

```yaml
# WRONG - no expect_error or similar assertion exists
tests:
  - name: guest_denied
    user_context: {role: guest}
    expect_error: true  # NOT VALID
```

```bash
# CORRECT - test denials via CLI
mxcp run tool my_tool --param id=1 --user-context '{"role": "guest"}'
# Expect: "Policy enforcement failed: ..."
```

## 15. Enum with Optional Parameter

When using enum with an optional parameter, either include `null` in enum or remove enum entirely:

```yaml
# WRONG - parameter is optional but null not in enum
parameters:
  - name: category
    type: string
    enum: [Electronics, Clothing, Food]
    default: null

# CORRECT Option 1 - include null in enum
parameters:
  - name: category
    type: string
    enum: [Electronics, Clothing, Food, null]
    default: null

# CORRECT Option 2 - remove enum, document in description
parameters:
  - name: category
    type: string
    description: "Filter by category. Valid: Electronics, Clothing, Food"
    default: null
```

## Quick Reference

| Mistake | Fix |
|---------|-----|
| Missing `tool:` wrapper | Add `tool:` before name/description |
| Missing parameter description | Add `description:` to every parameter |
| `type: int` | Use `type: integer` |
| `type: map` | Use `type: object` |
| `format: datetime` | Use `format: date-time` |
| `name: user-name` | Use `name: user_name` (no hyphens) |
| Both `code:` and `file:` | Use only one |
| `required: false` | Use `default: value` for optional params |
| Missing `language: python` | Add for Python tools |
| `default: null` with enum | Include `null` in enum list or remove enum |
| `expect_error`, `result_count` | Use valid assertions only |
| `SUM()` returns float | Cast: `CAST(SUM(x) AS INTEGER)` |
| Custom API key auth | Use built-in OAuth + policies |
| DB-specific SQL syntax | Verify in DuckDB docs, use `ON CONFLICT` |
| Testing policy denials | Use CLI `--user-context`, not YAML tests |
| Enum + optional param | Include `null` in enum or document in description |
