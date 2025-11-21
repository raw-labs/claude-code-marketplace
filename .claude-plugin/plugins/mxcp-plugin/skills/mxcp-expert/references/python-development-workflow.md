# Python Development Workflow for MXCP

**Complete guide for Python development in MXCP projects using uv, black, pyright, and pytest.**

## Overview

MXCP Python development requires specific tooling to ensure code quality, type safety, and testability. This guide covers the complete workflow from project setup to deployment.

## Required Tools

### uv - Fast Python Package Manager
**Why**: Faster than pip, better dependency resolution, virtual environment management
**Install**: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### black - Code Formatter
**Why**: Consistent code style, zero configuration
**Install**: Via uv (see below)

### pyright - Type Checker
**Why**: Catch type errors before runtime, better IDE support
**Install**: Via uv (see below)

### pytest - Testing Framework
**Why**: Simple, powerful, async support, mocking capabilities
**Install**: Via uv (see below)

## Complete Workflow

### Phase 1: Project Initialization

```bash
# 1. Create project directory
mkdir my-mxcp-server
cd my-mxcp-server

# 2. Create virtual environment with uv
uv venv

# Output:
# Using CPython 3.11.x interpreter at: /usr/bin/python3
# Creating virtual environment at: .venv
# Activate with: source .venv/bin/activate

# 3. Activate virtual environment
source .venv/bin/activate

# Verify activation (prompt should show (.venv))
which python
# Output: /path/to/my-mxcp-server/.venv/bin/python

# 4. Install MXCP and development tools
uv pip install mxcp black pyright pytest pytest-asyncio pytest-httpx pytest-cov

# 5. Initialize MXCP project
mxcp init --bootstrap

# 6. Create requirements.txt for reproducibility
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

### Phase 2: Writing Python Code

**CRITICAL: Always activate virtual environment before any work.**

```bash
# Check if virtual environment is active
echo $VIRTUAL_ENV
# Should show: /path/to/your/project/.venv

# If not active, activate it
source .venv/bin/activate
```

#### Create Python Tool

```bash
# Create Python module
cat > python/customer_tools.py <<'EOF'
"""Customer management tools."""

from mxcp.runtime import db
from typing import Dict, List, Optional


async def get_customer_summary(customer_id: str) -> Dict[str, any]:
    """
    Get comprehensive customer summary.

    Args:
        customer_id: Customer identifier

    Returns:
        Customer summary with orders and spending info
    """
    # Get customer data
    customer = db.execute(
        "SELECT * FROM customers WHERE id = $id",
        {"id": customer_id}
    ).fetchone()

    if not customer:
        return {
            "success": False,
            "error": f"Customer {customer_id} not found",
            "error_code": "NOT_FOUND",
        }

    # Get order summary
    orders = db.execute(
        """
        SELECT
            COUNT(*) as order_count,
            COALESCE(SUM(total), 0) as total_spent
        FROM orders
        WHERE customer_id = $id
        """,
        {"id": customer_id}
    ).fetchone()

    return {
        "success": True,
        "customer_id": customer["id"],
        "name": customer["name"],
        "email": customer["email"],
        "order_count": orders["order_count"],
        "total_spent": float(orders["total_spent"]),
    }
EOF
```

#### Format Code with Black

**ALWAYS run after creating or editing Python files:**

```bash
# Format specific directory
black python/

# Output:
# reformatted python/customer_tools.py
# All done! ✨ 🍰 ✨
# 1 file reformatted.

# Format specific file
black python/customer_tools.py

# Check what would be formatted (dry-run)
black --check python/

# See diff of changes
black --diff python/
```

**Black configuration** (optional):
```toml
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py311']
```

#### Run Type Checker

**ALWAYS run after creating or editing Python files:**

```bash
# Check all Python files
pyright python/

# Output if types are correct:
# 0 errors, 0 warnings, 0 informations

# Output if there are issues:
# python/customer_tools.py:15:12 - error: Type of "any" is unknown
# 1 error, 0 warnings, 0 informations

# Check specific file
pyright python/customer_tools.py

# Check with verbose output
pyright --verbose python/
```

**Fix common type issues**:

```python
# ❌ WRONG: Using 'any' type
async def get_customer_summary(customer_id: str) -> Dict[str, any]:
    pass

# ✅ CORRECT: Use proper types
from typing import Dict, Any, Union

async def get_customer_summary(customer_id: str) -> Dict[str, Union[str, int, float, bool]]:
    pass

# ✅ BETTER: Define response type
from typing import TypedDict

class CustomerSummary(TypedDict):
    success: bool
    customer_id: str
    name: str
    email: str
    order_count: int
    total_spent: float

async def get_customer_summary(customer_id: str) -> CustomerSummary:
    pass
```

**Pyright configuration** (optional):
```json
// pyrightconfig.json
{
  "include": ["python"],
  "exclude": [".venv", "**/__pycache__"],
  "typeCheckingMode": "strict",
  "reportMissingTypeStubs": false
}
```

### Phase 3: Writing Tests

**Create tests in `tests/` directory:**

```bash
# Create test directory structure
mkdir -p tests
touch tests/__init__.py

# Create test file
cat > tests/test_customer_tools.py <<'EOF'
"""Tests for customer_tools module."""

import pytest
from python.customer_tools import get_customer_summary
from unittest.mock import Mock, patch


@pytest.mark.asyncio
async def test_get_customer_summary_success():
    """Test successful customer summary retrieval."""
    # Mock database responses
    with patch("python.customer_tools.db") as mock_db:
        # Mock customer query
        mock_db.execute.return_value.fetchone.side_effect = [
            {"id": "CUST_123", "name": "John Doe", "email": "john@example.com"},
            {"order_count": 5, "total_spent": 1000.50}
        ]

        result = await get_customer_summary("CUST_123")

        assert result["success"] is True
        assert result["customer_id"] == "CUST_123"
        assert result["name"] == "John Doe"
        assert result["order_count"] == 5
        assert result["total_spent"] == 1000.50


@pytest.mark.asyncio
async def test_get_customer_summary_not_found():
    """Test customer not found error handling."""
    with patch("python.customer_tools.db") as mock_db:
        mock_db.execute.return_value.fetchone.return_value = None

        result = await get_customer_summary("CUST_999")

        assert result["success"] is False
        assert result["error_code"] == "NOT_FOUND"
        assert "CUST_999" in result["error"]
EOF
```

#### Run Tests

```bash
# Run all tests with verbose output
pytest tests/ -v

# Output:
# tests/test_customer_tools.py::test_get_customer_summary_success PASSED
# tests/test_customer_tools.py::test_get_customer_summary_not_found PASSED
# ======================== 2 passed in 0.15s ========================

# Run with coverage
pytest tests/ --cov=python --cov-report=term-missing

# Output:
# Name                           Stmts   Miss  Cover   Missing
# ------------------------------------------------------------
# python/customer_tools.py          25      0   100%
# ------------------------------------------------------------
# TOTAL                             25      0   100%

# Run specific test
pytest tests/test_customer_tools.py::test_get_customer_summary_success -v

# Run with output capture disabled (see prints)
pytest tests/ -v -s
```

### Phase 4: Complete Code Edit Cycle

**MANDATORY workflow after every Python code edit:**

```bash
# 1. Ensure virtual environment is active
source .venv/bin/activate

# 2. Format code
black python/
# Must see: "All done! ✨ 🍰 ✨"

# 3. Type check
pyright python/
# Must see: "0 errors, 0 warnings, 0 informations"

# 4. Run tests
pytest tests/ -v
# Must see: All tests PASSED

# 5. Only after ALL pass, proceed with next step
```

**If any check fails, fix before proceeding!**

### Phase 5: MXCP Validation and Testing

```bash
# Ensure virtual environment is active
source .venv/bin/activate

# 1. Validate structure
mxcp validate

# 2. Run MXCP integration tests
mxcp test

# 3. Run manual test
mxcp run tool get_customer_summary --param customer_id=CUST_123

# 4. Check documentation quality
mxcp lint
```

## Complete Checklist

Before declaring Python code complete:

### Setup Checklist
- [ ] Virtual environment created: `uv venv`
- [ ] Virtual environment activated: `source .venv/bin/activate`
- [ ] Dependencies installed: `uv pip install mxcp black pyright pytest pytest-asyncio pytest-httpx pytest-cov`
- [ ] `requirements.txt` created with all dependencies

### Code Quality Checklist
- [ ] Code formatted: `black python/` shows "All done!"
- [ ] Type checking passes: `pyright python/` shows "0 errors"
- [ ] All functions have type hints
- [ ] All functions have docstrings
- [ ] Error handling returns structured dicts

### Testing Checklist
- [ ] Unit tests created in `tests/`
- [ ] All tests pass: `pytest tests/ -v`
- [ ] External calls are mocked
- [ ] Test coverage >80%: `pytest --cov=python tests/`
- [ ] Result correctness verified (not just structure)
- [ ] Concurrency safety verified (if stateful)

### MXCP Checklist
- [ ] MXCP validation passes: `mxcp validate`
- [ ] MXCP tests pass: `mxcp test`
- [ ] Manual test succeeds: `mxcp run tool <name>`
- [ ] Documentation complete: `mxcp lint` passes

## Common Issues and Solutions

### Issue 1: Virtual Environment Not Active

**Symptom**: Commands not found or using wrong Python

```bash
# Check if active
which python
# Should show: /path/to/project/.venv/bin/python

# If not, activate
source .venv/bin/activate
```

### Issue 2: Black Formatting Fails

**Symptom**: Syntax errors in Python code

```bash
# Fix syntax errors first
python -m py_compile python/your_file.py

# Then format
black python/
```

### Issue 3: Pyright Type Errors

**Symptom**: "Type of X is unknown"

```python
# Add type hints
from typing import Dict, List, Optional, Any

# Use proper return types
def my_function() -> Dict[str, Any]:
    return {"key": "value"}
```

### Issue 4: Pytest Import Errors

**Symptom**: "ModuleNotFoundError: No module named 'python'"

```bash
# Ensure you're running from project root
pwd  # Should show project directory

# Ensure virtual environment is active
source .venv/bin/activate

# Run pytest from project root
pytest tests/ -v
```

### Issue 5: MXCP Commands Not Found

**Symptom**: "command not found: mxcp"

```bash
# Virtual environment not active
source .venv/bin/activate

# Verify mxcp is installed
which mxcp
# Should show: /path/to/project/.venv/bin/mxcp
```

## Integration with CI/CD

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Create virtual environment
        run: uv venv

      - name: Install dependencies
        run: |
          source .venv/bin/activate
          uv pip install -r requirements.txt

      - name: Format check
        run: |
          source .venv/bin/activate
          black --check python/

      - name: Type check
        run: |
          source .venv/bin/activate
          pyright python/

      - name: Run unit tests
        run: |
          source .venv/bin/activate
          pytest tests/ -v --cov=python --cov-report=xml

      - name: MXCP validate
        run: |
          source .venv/bin/activate
          mxcp validate

      - name: MXCP test
        run: |
          source .venv/bin/activate
          mxcp test
```

## Summary

**Python development workflow for MXCP**:

1. ✅ Create virtual environment with `uv venv`
2. ✅ Install tools: `uv pip install mxcp black pyright pytest ...`
3. ✅ Always activate before work: `source .venv/bin/activate`
4. ✅ After every edit: `black → pyright → pytest`
5. ✅ Before MXCP commands: Ensure venv active
6. ✅ Definition of Done: All checks pass

**Remember**: Virtual environment MUST be active for all MXCP and Python commands!
