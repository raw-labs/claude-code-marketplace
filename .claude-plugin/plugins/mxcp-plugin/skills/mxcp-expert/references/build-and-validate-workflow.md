# Build and Validate Workflow

**Mandatory workflow to ensure MXCP servers always work correctly.**

## Definition of Done

An MXCP server is **DONE** only when ALL of these criteria are met:

- [ ] **Virtual environment created**: `uv venv` completed (if Python tools exist)
- [ ] **Dependencies installed**: `uv pip install mxcp black pyright pytest pytest-asyncio pytest-httpx pytest-cov` (if Python tools exist)
- [ ] **Structure valid**: `mxcp validate` passes with no errors
- [ ] **MXCP tests pass**: `mxcp test` passes for all tools
- [ ] **Python code formatted**: `black python/` passes (if Python tools exist)
- [ ] **Type checking passes**: `pyright python/` passes with 0 errors (if Python tools exist)
- [ ] **Python unit tests pass**: `pytest tests/ -v` passes (if Python tools exist)
- [ ] **Data quality**: `dbt test` passes (if using dbt)
- [ ] **Result correctness verified**: Tests check actual values, not just structure
- [ ] **Mocking implemented**: External API calls are mocked in unit tests
- [ ] **Concurrency safe**: Python tools avoid race conditions
- [ ] **Documentation quality verified**: LLMs can understand tools with zero context
- [ ] **Error handling implemented**: Python tools return structured errors
- [ ] **Manual verification**: At least one manual test per tool succeeds
- [ ] **Security reviewed**: Checklist completed (see below)
- [ ] **Config provided**: Project has config.yml with usage instructions
- [ ] **Dependencies listed**: requirements.txt includes all dev dependencies

**NEVER declare a project complete without ALL checkboxes checked.**

## Mandatory Build Order

Follow this exact order to ensure correctness:

### Phase 1: Foundation (Must complete before Phase 2)

1. **Initialize project**
   ```bash
   mkdir project-name && cd project-name
   mxcp init --bootstrap
   ```

2. **Set up Python virtual environment** (CRITICAL - do this BEFORE any MXCP commands)
   ```bash
   # Create virtual environment with uv
   uv venv

   # Activate virtual environment
   source .venv/bin/activate  # On Unix/macOS
   # OR
   .venv\Scripts\activate     # On Windows

   # Verify activation (prompt should show (.venv))
   which python
   # Output: /path/to/project-name/.venv/bin/python

   # Install MXCP and development tools
   uv pip install mxcp black pyright pytest pytest-asyncio pytest-httpx pytest-cov

   # Create requirements.txt for reproducibility
   cat > requirements.txt <<'EOF'
mxcp>=0.1.0
black>=24.0.0
pyright>=1.1.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-httpx>=0.21.0
pytest-cov>=4.0.0
EOF
   ```

   **IMPORTANT**: Virtual environment must be active for ALL subsequent commands. If you close your terminal, re-activate with `source .venv/bin/activate`.

3. **Create project structure**
   ```bash
   mkdir -p seeds models tools resources prompts python tests
   touch tests/__init__.py
   ```

4. **Set up dbt (if needed)**
   ```bash
   # Create dbt_project.yml if needed
   # Create profiles.yml connection
   ```

5. **Validation checkpoint**: Verify structure
   ```bash
   # Ensure virtual environment is active
   echo $VIRTUAL_ENV  # Should show: /path/to/project-name/.venv

   ls -la  # Confirm directories exist
   mxcp validate  # Should pass (no tools yet, but structure valid)
   ```

**CRITICAL: Directory Structure Enforcement**

MXCP **enforces** organized directory structure. Files in wrong directories are **ignored** by discovery commands:

- ✅ Tools MUST be in `tools/*.yml`
- ✅ Resources MUST be in `resources/*.yml`
- ✅ Prompts MUST be in `prompts/*.yml`
- ❌ Tool files in root directory will be **ignored**
- ❌ Tool files in wrong directories will be **ignored**

**Common mistake to avoid**:
```bash
# ❌ WRONG - tool in root directory (will be ignored)
my_tool.yml

# ✅ CORRECT - tool in tools/ directory
tools/my_tool.yml
```

Use `mxcp init --bootstrap` to create proper structure automatically.

### Phase 2: Data Layer (if applicable)

1. **Add data source** (CSV, Excel, etc.)
   ```bash
   # Option A: CSV seed
   cp data.csv seeds/

   # Option B: Excel conversion
   python -c "import pandas as pd; pd.read_excel('data.xlsx').to_csv('seeds/data.csv', index=False)"
   ```

2. **Create schema.yml** (CRITICAL - don't skip!)
   ```yaml
   # seeds/schema.yml
   version: 2
   seeds:
     - name: data
       description: "Data description here"
       columns:
         - name: id
           tests: [unique, not_null]
         # Add ALL columns with tests
   ```

3. **Load and test data**
   ```bash
   dbt seed --select data
   dbt test --select data
   ```

4. **Validation checkpoint**: Data quality verified
   ```bash
   # Check data loaded
   mxcp query "SELECT COUNT(*) FROM data"
   # Should return row count
   ```

### Phase 3: Build Tools ONE AT A TIME

**CRITICAL: Build ONE tool, validate, test, THEN move to next.**

For EACH tool:

#### Step 1: Create Test FIRST (with LLM-friendly documentation)

```yaml
# tools/my_tool.yml
mxcp: 1
tool:
  name: my_tool
  description: "Retrieve data from table by filtering on column. Returns array of matching records. Use this to query specific records by their identifier."
  parameters:
    - name: param1
      type: string
      description: "Filter value for column (e.g., 'value123'). Must match exact column value."
      required: true
      examples: ["value123", "test_value"]
  return:
    type: array
    description: "Array of matching records"
    items:
      type: object
      properties:
        id: { type: integer, description: "Record identifier" }
        column: { type: string, description: "Filtered column value" }
  source:
    code: |
      SELECT * FROM data WHERE column = $param1
  tests:
    - name: "basic_test"
      arguments:
        - key: param1
          value: "test_value"
      result:
        # Expected result structure with actual values to verify
        - id: 1
          column: "test_value"
```

**Documentation requirements (check before proceeding)**:
- [ ] Tool description explains WHAT, returns WHAT, WHEN to use
- [ ] Parameters have descriptions with examples
- [ ] Return type properties all described
- [ ] An LLM with zero context could understand how to use this

#### Step 2: Validate Structure

```bash
mxcp validate
# Must pass before proceeding
```

**Common errors at this stage:**
- Indentation wrong (use spaces, not tabs)
- Missing required fields (name, description, return)
- Type mismatch (array vs object)
- Invalid SQL syntax

**If validation fails:**
1. Read error message carefully
2. Check YAML indentation (use yamllint)
3. Verify all required fields present
4. Check type definitions match return data
5. Fix and re-validate

#### Step 3: Test Functionality

**A. MXCP Integration Tests**

```bash
# Run the test case
mxcp test tool my_tool

# Run manually with different inputs
mxcp run tool my_tool --param param1=test_value
```

**If test fails:**
1. Check SQL syntax in source
2. Verify table/column names exist
3. Test SQL directly: `mxcp query "SELECT ..."`
4. Check parameter binding ($param1 syntax)
5. Verify return type matches actual data
6. Fix and re-test

**B. Python Code Quality (For Python Tools)**

**MANDATORY workflow after creating or editing ANY Python file:**

```bash
# CRITICAL: Always ensure virtual environment is active first
source .venv/bin/activate

# Step 1: Format code with black
black python/
# Must see: "All done! ✨ 🍰 ✨" or "N file(s) reformatted"

# Step 2: Type check with pyright
pyright python/
# Must see: "0 errors, 0 warnings, 0 informations"

# Step 3: Run unit tests
pytest tests/ -v
# Must see: All tests PASSED

# If ANY step fails, fix before proceeding!
```

**Create Unit Tests:**

```bash
# Create test file
cat > tests/test_my_tool.py <<'EOF'
"""Tests for my_module."""

import pytest
from python.my_module import my_function
from typing import Dict, Any

def test_my_function_correctness():
    """Verify result correctness"""
    result = my_function("test_input")
    assert result["expected_key"] == "expected_value"  # Verify actual value!

@pytest.mark.asyncio
async def test_async_function():
    """Test async functions"""
    result = await async_function()
    assert result is not None
EOF

# Run tests with coverage
pytest tests/ -v --cov=python --cov-report=term-missing
```

**Common Python Type Errors and Fixes:**

```python
# ❌ WRONG: Using 'any' type
from typing import Dict
async def get_data(id: str) -> Dict[str, any]:  # 'any' is not valid
    pass

# ✅ CORRECT: Use proper types
from typing import Dict, Any, Union
async def get_data(id: str) -> Dict[str, Union[str, int, float, bool]]:
    pass

# ✅ BETTER: Define response type
from typing import TypedDict
class DataResponse(TypedDict):
    success: bool
    data: str
    count: int

async def get_data(id: str) -> DataResponse:
    pass
```

**If unit tests fail:**
1. Check function logic
2. Verify test assertions are correct
3. Check imports
4. Fix and re-test

**C. Mocking External Calls (Required for API tools)**

```python
# tests/test_api_tool.py
import pytest
from python.api_wrapper import fetch_data

@pytest.mark.asyncio
async def test_fetch_data_with_mock(httpx_mock):
    """Mock external API call"""
    # Mock the HTTP response
    httpx_mock.add_response(
        url="https://api.example.com/data",
        json={"key": "value", "count": 5}
    )

    # Call function
    result = await fetch_data("param")

    # Verify correctness
    assert result["key"] == "value"
    assert result["count"] == 5
```

**D. Error Handling (Required for Python tools)**

Python tools MUST return structured error objects, never raise exceptions to MXCP.

```python
# python/my_module.py
import httpx

async def fetch_user(user_id: int) -> dict:
    """
    Fetch user with comprehensive error handling.

    Returns:
        Success: {"success": True, "user": {...}}
        Error: {"success": False, "error": "...", "error_code": "..."}
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://api.example.com/users/{user_id}"
            )

            if response.status_code == 404:
                return {
                    "success": False,
                    "error": f"User with ID {user_id} not found. Use list_users to see available users.",
                    "error_code": "NOT_FOUND",
                    "user_id": user_id
                }

            if response.status_code >= 500:
                return {
                    "success": False,
                    "error": "External API is currently unavailable. Please try again later.",
                    "error_code": "API_ERROR",
                    "status_code": response.status_code
                }

            response.raise_for_status()

            return {
                "success": True,
                "user": response.json()
            }

    except httpx.TimeoutException:
        return {
            "success": False,
            "error": "Request timed out after 10 seconds. The API may be slow or unavailable.",
            "error_code": "TIMEOUT"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "error_code": "UNKNOWN_ERROR"
        }
```

**Test error handling**:
```python
# tests/test_error_handling.py
@pytest.mark.asyncio
async def test_user_not_found(httpx_mock):
    """Verify 404 returns structured error"""
    httpx_mock.add_response(
        url="https://api.example.com/users/999",
        status_code=404
    )

    result = await fetch_user(999)

    assert result["success"] is False
    assert result["error_code"] == "NOT_FOUND"
    assert "999" in result["error"]  # Error mentions the ID
    assert "list_users" in result["error"]  # Actionable suggestion

@pytest.mark.asyncio
async def test_timeout_error(httpx_mock):
    """Verify timeout returns structured error"""
    httpx_mock.add_exception(httpx.TimeoutException("Timeout"))

    result = await fetch_user(123)

    assert result["success"] is False
    assert result["error_code"] == "TIMEOUT"
    assert "timeout" in result["error"].lower()
```

**Error message principles**:
- ✅ Be specific (exactly what went wrong)
- ✅ Be actionable (suggest next steps)
- ✅ Provide context (relevant values/IDs)
- ✅ Use plain language (LLM-friendly)

See **references/error-handling-guide.md** for comprehensive patterns.

**E. Concurrency Safety Tests (For stateful Python tools)**

```python
# tests/test_concurrency.py
import pytest
import asyncio

@pytest.mark.asyncio
async def test_concurrent_calls():
    """Verify no race conditions"""
    tasks = [my_function(i) for i in range(100)]
    results = await asyncio.gather(*tasks)

    # Verify all succeeded
    assert len(results) == 100
    assert all(r is not None for r in results)
```

#### Step 4: Verification Checkpoint

Before moving to next tool:

**For ALL tools:**
- [ ] `mxcp validate` passes
- [ ] `mxcp test tool my_tool` passes
- [ ] Manual test with real data works
- [ ] Tool returns expected data structure
- [ ] Error cases handled (null params, no results, etc.)
- [ ] **Result correctness verified** (not just structure)
- [ ] **Documentation quality verified**:
  - [ ] Tool description explains WHAT, WHAT it returns, WHEN to use
  - [ ] All parameters have descriptions with examples
  - [ ] Return fields all have descriptions
  - [ ] Cross-references to related tools (if applicable)
- [ ] **LLM can understand with zero context** (test: read YAML only, would you know how to use it?)

**For Python tools (additionally):**
- [ ] **Virtual environment active**: `echo $VIRTUAL_ENV` shows path
- [ ] **Code formatted**: `black python/` shows "All done!"
- [ ] **Type checking passes**: `pyright python/` shows "0 errors"
- [ ] `pytest tests/test_my_tool.py -v` passes
- [ ] External calls are mocked (if applicable)
- [ ] Concurrency tests pass (if stateful)
- [ ] No global mutable state OR proper locking used
- [ ] Test coverage >80% (`pytest --cov=python tests/`)
- [ ] **Error handling implemented**:
  - [ ] All try/except blocks return structured errors
  - [ ] Error format: `{"success": False, "error": "...", "error_code": "..."}`
  - [ ] Error messages are specific and actionable
  - [ ] Never raise exceptions to MXCP (return error objects)

**Only proceed to next tool when ALL checks pass.**

### Phase 4: Integration Testing

After all tools created:

1. **Run full validation suite**
   ```bash
   # CRITICAL: Ensure virtual environment is active
   source .venv/bin/activate

   # Python code quality (if Python tools exist)
   black python/                  # Must show: "All done!"
   pyright python/                # Must show: "0 errors"
   pytest tests/ -v --cov=python --cov-report=term  # All tests must pass

   # MXCP validation and integration tests
   mxcp validate  # All tools
   mxcp test      # All tests
   mxcp lint      # Documentation quality

   # dbt tests (if applicable)
   dbt test
   ```

2. **Test realistic scenarios**
   ```bash
   # Test each tool with realistic inputs
   mxcp run tool tool1 --param key=realistic_value
   mxcp run tool tool2 --param key=realistic_value

   # Test error cases
   mxcp run tool tool1 --param key=invalid_value
   mxcp run tool tool1  # Missing required param
   ```

3. **Performance check** (if applicable)
   ```bash
   # Test with large inputs
   mxcp run tool query_data --param limit=1000

   # Check response time is reasonable
   time mxcp run tool my_tool --param key=value
   ```

### Phase 5: Security & Configuration

1. **Security review checklist**
   - [ ] All SQL uses parameterized queries ($param)
   - [ ] No hardcoded secrets in code
   - [ ] Input validation on all parameters
   - [ ] Sensitive fields filtered with policies (if needed)
   - [ ] Authentication configured (if needed)

2. **Create config.yml**
   ```yaml
   # config.yml
   mxcp: 1
   profiles:
     default:
       secrets:
         - name: secret_name
           type: env
           parameters:
             env_var: SECRET_ENV_VAR
   ```

3. **Create README or usage instructions**
   ```markdown
   # Project Name

   ## Setup
   1. Install dependencies: pip install -r requirements.txt
   2. Set environment variables: export SECRET=xxx
   3. Load data: dbt seed (if applicable)
   4. Start server: mxcp serve

   ## Available Tools
   - tool1: Description
   - tool2: Description
   ```

### Phase 6: Final Validation

**This is the FINAL checklist before declaring DONE:**

```bash
# 0. Activate virtual environment
source .venv/bin/activate
echo $VIRTUAL_ENV  # Must show path

# 1. Python code quality (if Python tools exist)
black python/ && pyright python/ && pytest tests/ -v
# All must pass

# 2. Clean start test
cd .. && cd project-name
mxcp validate
# Should pass

# 3. All tests pass
mxcp test
# Should show all tests passing

# 4. Manual smoke test
mxcp run tool <main_tool> --param key=value
# Should return valid data

# 5. Lint check
mxcp lint
# Should have no critical issues

# 6. dbt tests (if applicable)
dbt test
# All data quality tests pass

# 7. Serve test
mxcp serve --transport http --port 8080 &
SERVER_PID=$!
sleep 2
curl http://localhost:8080/health || true
kill $SERVER_PID
# Server should start without errors
```

## Common Failure Patterns & Fixes

### YAML Validation Errors

**Error**: "Invalid YAML: expected <thing>"
```yaml
# WRONG: Mixed spaces and tabs
tool:
  name: my_tool
    description: "..."  # Tab here

# CORRECT: Consistent spaces (2 or 4)
tool:
  name: my_tool
  description: "..."
```

**Error**: "Missing required field: description"
```yaml
# WRONG: Missing description
tool:
  name: my_tool
  parameters: [...]

# CORRECT: All required fields
tool:
  name: my_tool
  description: "What this tool does"
  parameters: [...]
```

**Error**: "Invalid type for field 'return'"
```yaml
# WRONG: String instead of type object
return: "array"

# CORRECT: Proper type definition
return:
  type: array
  items:
    type: object
```

### SQL Errors

**Error**: "Table 'xyz' not found"
```sql
-- WRONG: Table doesn't exist
SELECT * FROM xyz

-- FIX: Check table name, run dbt seed
SELECT * FROM actual_table_name

-- VERIFY: List tables
-- mxcp query "SHOW TABLES"
```

**Error**: "Column 'abc' not found"
```sql
-- WRONG: Column name typo or doesn't exist
SELECT abc FROM table

-- FIX: Check exact column name (case-sensitive in some DBs)
SELECT actual_column_name FROM table

-- VERIFY: List columns
-- mxcp query "DESCRIBE table"
```

**Error**: "Unbound parameter: $param1"
```yaml
# WRONG: Parameter not defined in parameters list
parameters:
  - name: other_param
source:
  code: SELECT * FROM table WHERE col = $param1

# CORRECT: Define all parameters used in SQL
parameters:
  - name: param1
    type: string
source:
  code: SELECT * FROM table WHERE col = $param1
```

### Type Mismatch Errors

**Error**: "Expected object, got array"
```yaml
# WRONG: Return type doesn't match actual data
return:
  type: object
source:
  code: SELECT * FROM table  # Returns multiple rows (array)

# CORRECT: Match return type to SQL result
return:
  type: array
  items:
    type: object
source:
  code: SELECT * FROM table
```

**Error**: "Expected string, got number"
```yaml
# WRONG: Parameter type doesn't match usage
parameters:
  - name: age
    type: string
source:
  code: SELECT * FROM users WHERE age > $age  # Numeric comparison

# CORRECT: Use appropriate type
parameters:
  - name: age
    type: integer
source:
  code: SELECT * FROM users WHERE age > $age
```

### Python Import Errors

**Error**: "ModuleNotFoundError: No module named 'pandas'"
```bash
# WRONG: Library not installed OR virtual environment not active
import pandas as pd

# FIX:
# 1. Ensure virtual environment is active
source .venv/bin/activate

# 2. Add to requirements.txt
echo "pandas>=2.0.0" >> requirements.txt

# 3. Install using uv
uv pip install pandas
```

**Error**: "ImportError: cannot import name 'db' from 'mxcp.runtime'"
```python
# WRONG: Import path incorrect
from mxcp import db

# CORRECT: Import from runtime
from mxcp.runtime import db
```

### Python Code Quality Errors

**Error**: Black formatting fails with "INTERNAL ERROR"
```bash
# WRONG: Syntax error in Python code
# FIX: Check syntax first
python -m py_compile python/your_file.py
# Fix syntax errors, then run black
black python/
```

**Error**: Pyright shows "Type of 'any' is unknown"
```python
# WRONG: Using lowercase 'any'
def get_data() -> Dict[str, any]:
    pass

# CORRECT: Use 'Any' from typing
from typing import Dict, Any
def get_data() -> Dict[str, Any]:
    pass
```

**Error**: "command not found: mxcp"
```bash
# WRONG: Virtual environment not active
mxcp validate

# FIX: Activate virtual environment
source .venv/bin/activate
which mxcp  # Should show: /path/to/project/.venv/bin/mxcp
mxcp validate
```

### dbt Errors

**Error**: "Seed file not found"
```bash
# WRONG: File not in seeds/ directory
dbt seed --select data

# FIX: Check file location
ls seeds/
# Ensure data.csv exists in seeds/

# Or check seed name matches filename
# seeds/my_data.csv → dbt seed --select my_data
```

**Error**: "Test failed: unique_column_id"
```yaml
# Data has duplicates
# FIX: Clean data or remove test
seeds:
  - name: data
    columns:
      - name: id
        tests: [unique]  # Remove if duplicates are valid
```

## Debugging Workflow

When something doesn't work:

### Step 1: Identify the Layer

- **YAML layer**: `mxcp validate` fails → YAML structure issue
- **SQL layer**: `mxcp test` fails but validate passes → SQL issue
- **Data layer**: SQL syntax OK but wrong results → Data issue
- **Type layer**: Runtime error about types → Type mismatch
- **Python layer**: Import or runtime error → Python code issue

### Step 2: Isolate the Problem

```bash
# Test YAML structure
mxcp validate --debug

# Test SQL directly
mxcp query "SELECT * FROM table LIMIT 5"

# Test tool with minimal input
mxcp run tool my_tool --param key=simple_value

# Check logs
mxcp serve --debug
# Look for error messages
```

### Step 3: Fix Incrementally

1. **Fix one error at a time**
2. **Re-validate after each fix**
3. **Don't move forward until green**

### Step 4: Verify Fix

```bash
# After fixing, run full suite
mxcp validate && mxcp test && mxcp lint

# If all pass, manual test
mxcp run tool my_tool --param key=test_value
```

## Self-Checking for Agents

**Before declaring a project complete, agent must verify:**

### 0. Is virtual environment set up? (CRITICAL)
```bash
# Check virtual environment exists
ls .venv/bin/activate  # Must exist

# Activate it
source .venv/bin/activate

# Verify activation
echo $VIRTUAL_ENV  # Must show: /path/to/project/.venv
which python  # Must show: /path/to/project/.venv/bin/python
```

### 1. Can project be initialized?
```bash
cd project-directory
ls mxcp-site.yml  # Must exist
```

### 2. Python code quality passes? (if Python tools exist)
```bash
# Ensure venv active first
source .venv/bin/activate

# Check formatting
black --check python/
# Exit code 0 = success

# Check types
pyright python/
# Must show: "0 errors, 0 warnings, 0 informations"

# Check tests
pytest tests/ -v
# All tests show PASSED
```

### 3. Does MXCP validation pass?
```bash
# Ensure venv active
source .venv/bin/activate

mxcp validate
# Exit code 0 = success
```

### 4. Do MXCP tests pass?
```bash
# Ensure venv active
source .venv/bin/activate

mxcp test
# All tests show PASSED
```

### 5. Can tools be executed?
```bash
# Ensure venv active
source .venv/bin/activate

mxcp run tool <each_tool> --param key=value
# Returns data without errors
```

### 6. Is configuration complete?
```bash
ls config.yml  # Exists
cat config.yml | grep "mxcp: 1"  # Valid
```

### 7. Are dependencies listed?
```bash
# Must have requirements.txt with all dependencies
ls requirements.txt  # Exists
cat requirements.txt  # Has mxcp, black, pyright, pytest
```

### 8. Can server start?
```bash
# Ensure venv active
source .venv/bin/activate

timeout 5 mxcp serve --transport http --port 8080 || true
# Should start without immediate errors
```

## Retry Strategy

If validation fails:

### Attempt 1: Fix Based on Error Message
- Read error message carefully
- Apply specific fix
- Re-validate

### Attempt 2: Check Examples
- Compare with working examples
- Verify structure matches pattern
- Re-validate

### Attempt 3: Simplify
- Remove optional features
- Test minimal version
- Add features back incrementally

### If Still Failing:
- Report exact error to user
- Provide working minimal example
- Ask for clarification on requirements

## Summary: The Golden Rule

**Build → Validate → Test → Verify → THEN Next**

Never skip steps. Never batch multiple tools without validating each one. Always verify before declaring done.

**If validation fails, the project is NOT done. Fix until all checks pass.**
