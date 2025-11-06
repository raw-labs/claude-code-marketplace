# MXCP Debugging Guide

**Systematic approach to debugging MXCP servers when things don't work.**

## Debug Mode

### Enable Debug Logging

```bash
# Option 1: Environment variable
export MXCP_DEBUG=1
mxcp serve

# Option 2: CLI flag
mxcp serve --debug

# Option 3: For specific commands
mxcp validate --debug
mxcp test --debug
mxcp run tool my_tool --param key=value --debug
```

**Debug mode shows**:
- SQL queries being executed
- Parameter values
- Type conversions
- Error stack traces
- Internal MXCP operations

## Debugging Workflow

### Step 1: Identify the Layer

When something fails, determine which layer has the problem:

```
User Request
    ↓
MXCP Validation (YAML structure)
    ↓
Parameter Binding (Type conversion)
    ↓
Python Code Execution (if language: python)
    ↓
SQL Execution (if SQL source)
    ↓
Type Validation (Return type check)
    ↓
Response to LLM
```

**Run these commands in order**:

```bash
# 1. Structure validation
mxcp validate
# If fails → YAML structure issue (go to "YAML Errors" section)

# 2. Test with known inputs
mxcp test
# If fails → Logic or SQL issue (go to "Test Failures" section)

# 3. Manual execution
mxcp run tool my_tool --param key=value
# If fails → Runtime issue (go to "Runtime Errors" section)

# 4. Debug mode
mxcp run tool my_tool --param key=value --debug
# See detailed execution logs
```

## Common Issues and Solutions

### YAML Validation Errors

#### Error: "Invalid YAML syntax"

```bash
# Check YAML syntax
mxcp validate --debug

# Common causes:
# 1. Mixed tabs and spaces (use spaces only)
# 2. Incorrect indentation
# 3. Missing quotes around special characters
# 4. Unclosed quotes or brackets
```

**Solution**:
```bash
# Use yamllint to check
pip install yamllint
yamllint tools/my_tool.yml

# Or use online validator
# https://www.yamllint.com/
```

#### Error: "Missing required field: description"

```yaml
# ❌ WRONG
tool:
  name: my_tool
  parameters: []
  source:
    code: SELECT * FROM table

# ✅ CORRECT
tool:
  name: my_tool
  description: "What this tool does"  # ← Added
  parameters: []
  source:
    code: SELECT * FROM table
```

#### Error: "Invalid type specification"

```yaml
# ❌ WRONG
return:
  type: "object"  # Quoted string
  properties:
    id: "integer"  # Quoted string

# ✅ CORRECT
return:
  type: object  # Unquoted
  properties:
    id: { type: integer }  # Proper structure
```

### Test Failures

#### Error: "Expected X, got Y" in test

```yaml
# Test says: Expected 5 items, got 3

# Debug steps:
# 1. Run SQL directly
mxcp query "SELECT * FROM table WHERE condition"

# 2. Check test data exists
mxcp query "SELECT COUNT(*) FROM table WHERE condition"

# 3. Verify filter logic
mxcp run tool my_tool --param key=test_value --debug
```

**Common causes**:
- Test data not loaded (`dbt seed` not run)
- Wrong filter condition in SQL
- Test expects wrong values

#### Error: "Type mismatch"

```yaml
# Test fails: Expected integer, got string

# Check SQL output types
mxcp query "DESCRIBE table"

# Fix: Cast in SQL
SELECT
  CAST(column AS INTEGER) as column  # Explicit cast
FROM table
```

### SQL Errors

#### Error: "Table 'xyz' does not exist"

```bash
# List all tables
mxcp query "SHOW TABLES"

# Check if dbt models/seeds loaded
dbt seed
dbt run

# Verify table name (case-sensitive)
mxcp query "SELECT * FROM xyz LIMIT 1"
```

#### Error: "Column 'abc' not found"

```bash
# Show table schema
mxcp query "DESCRIBE table_name"

# Check column names (case-sensitive)
mxcp query "SELECT * FROM table_name LIMIT 1"

# Common issue: typo or wrong case
SELECT customer_id  # ← Check exact spelling
```

#### Error: "Syntax error near..."

```bash
# Test SQL directly with debug
mxcp query "YOUR SQL HERE" --debug

# Common SQL syntax errors:
# 1. Missing quotes around strings
# 2. Wrong parameter binding syntax (use $param not :param)
# 3. DuckDB-specific syntax issues
```

### Parameter Binding Errors

#### Error: "Unbound parameter: $param1"

```yaml
# ❌ WRONG: Parameter used but not defined
tool:
  name: my_tool
  parameters:
    - name: other_param
      type: string
  source:
    code: SELECT * FROM table WHERE col = $param1  # ← Not defined!

# ✅ CORRECT: Define all parameters
tool:
  name: my_tool
  parameters:
    - name: param1  # ← Added
      type: string
    - name: other_param
      type: string
  source:
    code: SELECT * FROM table WHERE col = $param1
```

#### Error: "Type mismatch for parameter"

```yaml
# MXCP tries to convert "abc" to integer → fails

# ✅ Solution: Validate types match usage
parameters:
  - name: age
    type: integer  # ← Must be integer for numeric comparison
source:
  code: SELECT * FROM users WHERE age > $age  # Numeric comparison
```

### Python Errors

#### Error: "ModuleNotFoundError: No module named 'xyz'"

```bash
# Check requirements.txt exists
cat requirements.txt

# Install dependencies
pip install -r requirements.txt

# Or install specific module
pip install xyz
```

#### Error: "ImportError: cannot import name 'db'"

```python
# ❌ WRONG import path
from mxcp import db

# ✅ CORRECT import path
from mxcp.runtime import db
```

#### Error: "Function 'xyz' not found in module"

```yaml
# tools/my_tool.yml
source:
  file: ../python/my_module.py  # ← Check file path

# Common issues:
# 1. Wrong file path (use ../ to go up from tools/)
# 2. Function name typo
# 3. Function not exported (not at module level)
```

**Check function exists**:
```bash
# Read Python file
cat python/my_module.py | grep "^def\|^async def"

# Should see your function listed
```

#### Error: "Async function called incorrectly"

```python
# ❌ WRONG: Calling async function without await
def my_tool():
    result = async_function()  # ← Missing await!
    return result

# ✅ CORRECT: Properly handle async
async def my_tool():
    result = await async_function()  # ← Added await
    return result
```

### Return Type Validation Errors

#### Error: "Expected array, got object"

```yaml
# SQL returns multiple rows (array) but type says object

# ❌ WRONG
return:
  type: object  # ← Wrong! SQL returns array
source:
  code: SELECT * FROM table  # Returns multiple rows

# ✅ CORRECT
return:
  type: array  # ← Matches SQL output
  items:
    type: object
source:
  code: SELECT * FROM table
```

#### Error: "Missing required field 'xyz'"

```yaml
# Return type expects field that SQL doesn't return

# ❌ WRONG
return:
  type: object
  properties:
    id: { type: integer }
    missing_field: { type: string }  # ← SQL doesn't return this!
source:
  code: SELECT id FROM table  # Only returns 'id'

# ✅ CORRECT: Match return type to actual SQL output
return:
  type: object
  properties:
    id: { type: integer }  # Only what SQL returns
source:
  code: SELECT id FROM table
```

## Debugging Techniques

### 1. Test SQL Directly

```bash
# Instead of testing whole tool, test SQL first
mxcp query "SELECT * FROM table WHERE condition LIMIT 5"

# Test with parameters manually
mxcp query "SELECT * FROM table WHERE id = 123"

# Check aggregations
mxcp query "SELECT COUNT(*), SUM(amount) FROM table"
```

### 2. Add Debug Prints to Python

```python
# python/my_module.py
import sys

def my_function(param: str) -> dict:
    # Debug output (goes to stderr, won't affect result)
    print(f"DEBUG: param={param}", file=sys.stderr)

    result = process(param)

    print(f"DEBUG: result={result}", file=sys.stderr)

    return result
```

**View debug output**:
```bash
mxcp serve --debug 2>&1 | grep DEBUG
```

### 3. Isolate the Problem

```python
# Break complex function into steps

# ❌ Hard to debug
def complex_function(data):
    return process(transform(validate(data)))

# ✅ Easy to debug
def complex_function(data):
    print("Step 1: Validate", file=sys.stderr)
    validated = validate(data)

    print("Step 2: Transform", file=sys.stderr)
    transformed = transform(validated)

    print("Step 3: Process", file=sys.stderr)
    processed = process(transformed)

    return processed
```

### 4. Test with Minimal Input

```bash
# Start with simplest possible input
mxcp run tool my_tool --param id=1

# Gradually add complexity
mxcp run tool my_tool --param id=1 --param status=active

# Test edge cases
mxcp run tool my_tool --param id=999999  # Non-existent
mxcp run tool my_tool  # Missing required param
```

### 5. Check Logs

```bash
# Server logs (if running)
mxcp serve --debug 2>&1 | tee mxcp.log

# View recent errors
grep -i error mxcp.log

# View SQL queries
grep -i select mxcp.log
```

### 6. Verify Data

```bash
# Check seed data loaded
dbt seed --select my_data
mxcp query "SELECT COUNT(*) FROM my_data"

# Check dbt models built
dbt run --select my_model
mxcp query "SELECT COUNT(*) FROM my_model"

# Verify test fixtures
mxcp query "SELECT * FROM test_fixtures LIMIT 5"
```

## Common Debugging Scenarios

### Scenario 1: Tool Returns Empty Results

```bash
# 1. Check if data exists
mxcp query "SELECT COUNT(*) FROM table"
# → If 0, data not loaded (run dbt seed)

# 2. Check filter condition
mxcp query "SELECT * FROM table WHERE condition"
# → Test condition manually

# 3. Check parameter value
mxcp run tool my_tool --param key=value --debug
# → See actual SQL with parameter values
```

### Scenario 2: Tool Crashes/Returns Error

```bash
# 1. Validate structure
mxcp validate
# → Fix any YAML errors first

# 2. Test in isolation
mxcp test tool my_tool
# → See specific error

# 3. Run with debug
mxcp run tool my_tool --param key=value --debug
# → See full stack trace
```

### Scenario 3: Wrong Data Returned

```bash
# 1. Test SQL directly
mxcp query "SELECT * FROM table LIMIT 5"
# → Verify columns and values

# 2. Check test assertions
# In YAML, verify test expected results match actual

# 3. Verify type conversions
mxcp query "SELECT typeof(column) as type FROM table LIMIT 1"
# → Check DuckDB types
```

### Scenario 4: Performance Issues

```bash
# 1. Check query execution time
time mxcp query "SELECT * FROM large_table"

# 2. Analyze query plan
mxcp query "EXPLAIN SELECT * FROM table WHERE condition"

# 3. Check for missing indexes
mxcp query "PRAGMA show_tables_expanded"

# 4. Limit results during development
SELECT * FROM table LIMIT 100  # Add LIMIT for testing
```

## Debugging Checklist

When something doesn't work:

- [ ] Run `mxcp validate` to check YAML structure
- [ ] Run `mxcp test` to check logic
- [ ] Run `mxcp run tool <name> --debug` to see details
- [ ] Test SQL directly with `mxcp query`
- [ ] Check data loaded with `dbt seed` or `dbt run`
- [ ] Verify Python imports work (`from mxcp.runtime import db`)
- [ ] Check requirements.txt and install dependencies
- [ ] Add debug prints to Python code
- [ ] Test with minimal/simple inputs first
- [ ] Check return types match actual data
- [ ] Review logs for errors

## Getting Help

### Information to Provide

When asking for help or reporting issues:

1. **Error message** (full text)
2. **Command that failed** (exact command)
3. **Tool YAML** (relevant parts)
4. **Debug output** (`--debug` flag)
5. **Environment** (`mxcp --version`, `python --version`)

### Self-Help Steps

Before asking for help:

1. Read the error message carefully
2. Check this debugging guide
3. Search error message in documentation
4. Test components in isolation
5. Create minimal reproduction case

## Summary

**Debugging workflow**:
1. `mxcp validate` → Fix YAML errors
2. `mxcp test` → Fix logic errors
3. `mxcp run --debug` → See detailed execution
4. `mxcp query` → Test SQL directly
5. Add debug prints → Trace Python execution
6. Test in isolation → Identify exact failure point

**Remember**:
- Start simple, add complexity gradually
- Test each layer independently
- Use debug mode liberally
- Check data loaded before testing queries
- Verify types match at every step
