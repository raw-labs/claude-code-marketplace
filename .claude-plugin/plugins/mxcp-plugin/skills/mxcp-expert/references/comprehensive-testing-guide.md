# Comprehensive Testing Guide

**Complete testing strategy for MXCP servers: MXCP tests, Python unit tests, mocking, test databases, and concurrency safety.**

## Two Types of Tests

### 1. MXCP Tests (Integration Tests)

**Purpose**: Test the full tool/resource/prompt as it will be called by LLMs.

**Located**: In tool YAML files under `tests:` section

**Run with**: `mxcp test`

**Tests**:
- Tool can be invoked with parameters
- Return type matches specification
- Result structure is correct
- Parameter validation works

**Example**:
```yaml
# tools/get_customers.yml
mxcp: 1
tool:
  name: get_customers
  tests:
    - name: "basic_query"
      arguments:
        - key: city
          value: "Chicago"
      result:
        - customer_id: 3
          name: "Bob Johnson"
```

### 2. Python Unit Tests (Isolation Tests)

**Purpose**: Test Python functions in isolation with mocking, edge cases, concurrency.

**Located**: In `tests/` directory (pytest format)

**Run with**: `pytest` or `python -m pytest`

**Tests**:
- Function logic correctness
- Edge cases and error handling
- Mocked external dependencies
- Concurrency safety
- Result correctness verification

**Example**:
```python
# tests/test_api_wrapper.py
import pytest
from python.api_wrapper import fetch_users

@pytest.mark.asyncio
async def test_fetch_users_correctness():
    """Test that fetch_users returns correct structure"""
    result = await fetch_users(limit=5)

    assert "users" in result
    assert "count" in result
    assert result["count"] == 5
    assert len(result["users"]) == 5
    assert all("id" in user for user in result["users"])
```

## When to Use Which Tests

| Scenario | MXCP Tests | Python Unit Tests |
|----------|------------|-------------------|
| SQL-only tool | ✅ Required | ❌ Not applicable |
| Python tool (no external calls) | ✅ Required | ✅ Recommended |
| Python tool (with API calls) | ✅ Required | ✅ **Required** (with mocking) |
| Python tool (with DB writes) | ✅ Required | ✅ **Required** (test DB) |
| Python tool (async/concurrent) | ✅ Required | ✅ **Required** (concurrency tests) |

## Complete Testing Workflow

### Phase 1: MXCP Tests (Always First)

**For every tool, add test cases to YAML:**

```yaml
tool:
  name: my_tool
  # ... definition ...
  tests:
    - name: "happy_path"
      arguments:
        - key: param1
          value: "test_value"
      result:
        expected_field: "expected_value"

    - name: "edge_case_empty"
      arguments:
        - key: param1
          value: "nonexistent"
      result: []

    - name: "missing_optional_param"
      arguments: []
      # Should work with defaults
```

**Run**:
```bash
mxcp test tool my_tool
```

### Phase 2: Python Unit Tests (For Python Tools)

**Create test file structure**:
```bash
mkdir -p tests
touch tests/__init__.py
touch tests/test_my_module.py
```

**Write unit tests with pytest**:
```python
# tests/test_my_module.py
import pytest
from python.my_module import my_function

def test_my_function_correctness():
    """Verify correct results"""
    result = my_function("input")
    assert result["key"] == "expected_value"
    assert len(result["items"]) == 5

def test_my_function_edge_cases():
    """Test edge cases"""
    assert my_function("") == {"error": "Empty input"}
    assert my_function(None) == {"error": "Invalid input"}
```

**Run**:
```bash
pytest tests/
# Or with coverage
pytest --cov=python tests/
```

## Testing SQL Tools with Test Database

**CRITICAL**: SQL tools must be tested with real data to verify result correctness.

### Pattern 1: Use dbt Seeds for Test Data

```bash
# 1. Create test data seed
cat > seeds/test_data.csv <<'EOF'
id,name,value
1,test1,100
2,test2,200
3,test3,300
EOF

# 2. Create schema
cat > seeds/schema.yml <<'EOF'
version: 2
seeds:
  - name: test_data
    columns:
      - name: id
        tests: [unique, not_null]
EOF

# 3. Load test data
dbt seed --select test_data

# 4. Create tool with tests
cat > tools/query_test_data.yml <<'EOF'
mxcp: 1
tool:
  name: query_test_data
  parameters:
    - name: min_value
      type: integer
  return:
    type: array
  source:
    code: |
      SELECT * FROM test_data WHERE value >= $min_value
  tests:
    - name: "filter_200"
      arguments:
        - key: min_value
          value: 200
      result:
        - id: 2
          value: 200
        - id: 3
          value: 300
EOF

# 5. Test
mxcp test tool query_test_data
```

### Pattern 2: Create Test Fixtures in SQL

```sql
-- models/test_fixtures.sql
{{ config(materialized='table') }}

-- Create predictable test data
SELECT 1 as id, 'Alice' as name, 100 as score
UNION ALL
SELECT 2 as id, 'Bob' as name, 200 as score
UNION ALL
SELECT 3 as id, 'Charlie' as name, 150 as score
```

```yaml
# tools/top_scores.yml
tool:
  name: top_scores
  source:
    code: |
      SELECT * FROM test_fixtures ORDER BY score DESC LIMIT $limit
  tests:
    - name: "top_2"
      arguments:
        - key: limit
          value: 2
      result:
        - id: 2
          name: "Bob"
          score: 200
        - id: 3
          name: "Charlie"
          score: 150
```

### Pattern 3: Verify Aggregation Correctness

```yaml
# tools/calculate_stats.yml
tool:
  name: calculate_stats
  source:
    code: |
      SELECT
        COUNT(*) as total_count,
        SUM(score) as total_score,
        AVG(score) as avg_score,
        MAX(score) as max_score
      FROM test_fixtures
  tests:
    - name: "verify_aggregations"
      arguments: []
      result:
        - total_count: 3
          total_score: 450
          avg_score: 150.0
          max_score: 200
```

**If aggregations don't match expected values, the SQL logic is WRONG.**

## Testing Python Tools with Mocking

**CRITICAL**: Python tools with external API calls MUST use mocking in tests.

### Pattern 1: Mock HTTP Calls with pytest-httpx

```bash
# Install
pip install pytest-httpx
```

```python
# python/api_client.py
import httpx

async def fetch_external_data(api_key: str, user_id: int) -> dict:
    """Fetch data from external API"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.example.com/users/{user_id}",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        response.raise_for_status()
        return response.json()
```

```python
# tests/test_api_client.py
import pytest
from httpx import Response
from python.api_client import fetch_external_data

@pytest.mark.asyncio
async def test_fetch_external_data_success(httpx_mock):
    """Test successful API call with mocked response"""
    # Mock the HTTP call
    httpx_mock.add_response(
        url="https://api.example.com/users/123",
        json={"id": 123, "name": "Test User", "email": "test@example.com"}
    )

    # Call function
    result = await fetch_external_data("fake_api_key", 123)

    # Verify correctness
    assert result["id"] == 123
    assert result["name"] == "Test User"
    assert result["email"] == "test@example.com"

@pytest.mark.asyncio
async def test_fetch_external_data_error(httpx_mock):
    """Test API error handling"""
    httpx_mock.add_response(
        url="https://api.example.com/users/999",
        status_code=404,
        json={"error": "User not found"}
    )

    # Should handle error gracefully
    with pytest.raises(httpx.HTTPStatusError):
        await fetch_external_data("fake_api_key", 999)
```

### Pattern 2: Mock Database Calls

```python
# python/db_operations.py
from mxcp.runtime import db

def get_user_orders(user_id: int) -> list[dict]:
    """Get orders for a user"""
    result = db.execute(
        "SELECT * FROM orders WHERE user_id = $1",
        {"user_id": user_id}
    )
    return result.fetchall()
```

```python
# tests/test_db_operations.py
import pytest
from unittest.mock import Mock, MagicMock
from python.db_operations import get_user_orders

def test_get_user_orders(monkeypatch):
    """Test with mocked database"""
    # Create mock result
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [
        {"order_id": 1, "user_id": 123, "amount": 50.0},
        {"order_id": 2, "user_id": 123, "amount": 75.0}
    ]

    # Mock db.execute
    mock_db = Mock()
    mock_db.execute.return_value = mock_result

    # Inject mock
    import python.db_operations
    monkeypatch.setattr(python.db_operations, "db", mock_db)

    # Test
    orders = get_user_orders(123)

    # Verify
    assert len(orders) == 2
    assert orders[0]["order_id"] == 1
    assert sum(o["amount"] for o in orders) == 125.0
```

### Pattern 3: Mock Third-Party Libraries

```python
# python/stripe_wrapper.py
import stripe

def create_customer(email: str, name: str) -> dict:
    """Create Stripe customer"""
    customer = stripe.Customer.create(email=email, name=name)
    return {"id": customer.id, "email": customer.email}
```

```python
# tests/test_stripe_wrapper.py
import pytest
from unittest.mock import Mock, patch
from python.stripe_wrapper import create_customer

@patch('stripe.Customer.create')
def test_create_customer(mock_create):
    """Test Stripe customer creation with mock"""
    # Mock Stripe response
    mock_customer = Mock()
    mock_customer.id = "cus_test123"
    mock_customer.email = "test@example.com"
    mock_create.return_value = mock_customer

    # Call function
    result = create_customer("test@example.com", "Test User")

    # Verify correctness
    assert result["id"] == "cus_test123"
    assert result["email"] == "test@example.com"

    # Verify Stripe was called correctly
    mock_create.assert_called_once_with(
        email="test@example.com",
        name="Test User"
    )
```

## Result Correctness Verification

**CRITICAL**: Tests must verify results are CORRECT, not just that code doesn't crash.

### Bad Test (Only checks structure):
```python
def test_calculate_total_bad():
    result = calculate_total([10, 20, 30])
    assert "total" in result  # ❌ Doesn't verify correctness
```

### Good Test (Verifies correct value):
```python
def test_calculate_total_good():
    result = calculate_total([10, 20, 30])
    assert result["total"] == 60  # ✅ Verifies correct calculation
    assert result["count"] == 3   # ✅ Verifies correct count
    assert result["average"] == 20.0  # ✅ Verifies correct average
```

### Pattern: Test Edge Cases for Correctness

```python
def test_aggregation_correctness():
    """Test various aggregations for correctness"""
    data = [
        {"id": 1, "value": 100},
        {"id": 2, "value": 200},
        {"id": 3, "value": 150}
    ]

    result = aggregate_data(data)

    # Verify each aggregation
    assert result["sum"] == 450  # 100 + 200 + 150
    assert result["avg"] == 150.0  # 450 / 3
    assert result["min"] == 100
    assert result["max"] == 200
    assert result["count"] == 3

    # Verify derived values
    assert result["range"] == 100  # 200 - 100
    assert result["median"] == 150

def test_empty_data_correctness():
    """Test edge case: empty data"""
    result = aggregate_data([])

    assert result["sum"] == 0
    assert result["avg"] == 0.0
    assert result["count"] == 0
    # Ensure no crashes, correct behavior for empty data
```

## Concurrency Safety for Python Tools

**CRITICAL**: MXCP tools run as a server - multiple requests can happen simultaneously.

### Common Concurrency Issues

#### ❌ WRONG: Global State with Race Conditions

```python
# python/unsafe_counter.py
counter = 0  # ❌ DANGER: Race condition!

def increment_counter() -> dict:
    global counter
    counter += 1  # ❌ Not thread-safe!
    return {"count": counter}

# Two simultaneous requests could both read counter=5,
# both increment to 6, both write 6 -> one increment lost!
```

#### ✅ CORRECT: Use Thread-Safe Approaches

**Option 1: Avoid shared state (stateless)**
```python
# python/safe_stateless.py
def process_request(data: dict) -> dict:
    """Completely stateless - safe for concurrent calls"""
    result = compute_something(data)
    return {"result": result}
    # No global state, no problem!
```

**Option 2: Use thread-safe structures**
```python
# python/safe_with_lock.py
import threading

counter_lock = threading.Lock()
counter = 0

def increment_counter() -> dict:
    global counter
    with counter_lock:  # ✅ Thread-safe
        counter += 1
        current = counter
    return {"count": current}
```

**Option 3: Use atomic operations**
```python
# python/safe_atomic.py
from threading import Lock
from collections import defaultdict

# Thread-safe counter
class SafeCounter:
    def __init__(self):
        self._value = 0
        self._lock = Lock()

    def increment(self):
        with self._lock:
            self._value += 1
            return self._value

counter = SafeCounter()

def increment_counter() -> dict:
    return {"count": counter.increment()}
```

### Concurrency-Safe Patterns

#### Pattern 1: Database as State (DuckDB is thread-safe)

```python
# python/db_counter.py
from mxcp.runtime import db

def increment_counter() -> dict:
    """Use database for state - thread-safe"""
    db.execute("""
        CREATE TABLE IF NOT EXISTS counter (
            id INTEGER PRIMARY KEY,
            value INTEGER
        )
    """)

    db.execute("""
        INSERT INTO counter (id, value) VALUES (1, 1)
        ON CONFLICT(id) DO UPDATE SET value = value + 1
    """)

    result = db.execute("SELECT value FROM counter WHERE id = 1")
    return {"count": result.fetchone()["value"]}
```

#### Pattern 2: Local Variables Only (Immutable)

```python
# python/safe_processing.py
async def process_data(input_data: list[dict]) -> dict:
    """Local variables only - safe for concurrent calls"""
    # All state is local to this function call
    results = []
    total = 0

    for item in input_data:
        processed = transform(item)  # Pure function
        results.append(processed)
        total += processed["value"]

    return {
        "results": results,
        "total": total,
        "count": len(results)
    }
    # When function returns, all state is discarded
```

#### Pattern 3: Async/Await (Concurrent, Not Parallel)

```python
# python/safe_async.py
import asyncio
import httpx

async def fetch_multiple_users(user_ids: list[int]) -> list[dict]:
    """Concurrent API calls - safe with async"""

    async def fetch_one(user_id: int) -> dict:
        # Each call has its own context - no shared state
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://api.example.com/users/{user_id}")
            return response.json()

    # Run concurrently, but each fetch_one is independent
    results = await asyncio.gather(*[fetch_one(uid) for uid in user_ids])
    return results
```

### Testing Concurrency Safety

```python
# tests/test_concurrency.py
import pytest
import asyncio
from python.my_module import concurrent_function

@pytest.mark.asyncio
async def test_concurrent_calls_no_race_condition():
    """Test that concurrent calls don't have race conditions"""

    # Run function 100 times concurrently
    tasks = [concurrent_function(i) for i in range(100)]
    results = await asyncio.gather(*tasks)

    # Verify all calls succeeded
    assert len(results) == 100

    # Verify no data corruption
    assert all(isinstance(r, dict) for r in results)

    # If function has a counter, verify correctness
    # (e.g., if each call increments, final count should be 100)

def test_parallel_execution_thread_safe():
    """Test with actual threading"""
    import threading

    results = []
    errors = []

    def worker(n):
        try:
            result = my_function(n)
            results.append(result)
        except Exception as e:
            errors.append(e)

    # Create 50 threads
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(50)]

    # Start all threads
    for t in threads:
        t.start()

    # Wait for completion
    for t in threads:
        t.join()

    # Verify
    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert len(results) == 50
```

## Complete Testing Checklist

### For SQL Tools:

- [ ] MXCP test cases in YAML
- [ ] Test with real seed data
- [ ] Verify result correctness (exact values)
- [ ] Test edge cases (empty results, NULL values)
- [ ] Test filters work correctly
- [ ] Test aggregations are mathematically correct
- [ ] Test with dbt test for data quality

### For Python Tools (No External Calls):

- [ ] MXCP test cases in YAML
- [ ] Python unit tests (pytest)
- [ ] Verify result correctness
- [ ] Test edge cases (empty input, NULL, invalid)
- [ ] Test error handling
- [ ] Test concurrency safety (if using shared state)

### For Python Tools (With External API Calls):

- [ ] MXCP test cases in YAML
- [ ] Python unit tests with mocking (pytest + httpx_mock)
- [ ] Mock all external API calls
- [ ] Test success path with mocked responses
- [ ] Test error cases (404, 500, timeout)
- [ ] Verify correct API parameters
- [ ] Test result correctness
- [ ] Test concurrency (multiple simultaneous calls)

### For Python Tools (With Database Operations):

- [ ] MXCP test cases in YAML
- [ ] Python unit tests
- [ ] Use test fixtures/seed data
- [ ] Verify query results correctness
- [ ] Test transactions (if applicable)
- [ ] Test concurrency (DuckDB is thread-safe)
- [ ] Clean up test data after tests

## Project Structure for Testing

```
project/
├── mxcp-site.yml
├── tools/
│   └── my_tool.yml              # Contains MXCP tests
├── python/
│   └── my_module.py             # Python code
├── tests/
│   ├── __init__.py
│   ├── test_my_module.py        # Python unit tests
│   ├── conftest.py              # pytest fixtures
│   └── fixtures/
│       └── test_data.json       # Test data
├── seeds/
│   ├── test_data.csv            # Test database seeds
│   └── schema.yml
└── requirements.txt             # Include: pytest, pytest-asyncio, pytest-httpx, pytest-cov
```

## Running Tests

```bash
# 1. MXCP tests (always run first)
mxcp validate  # Structure validation
mxcp test      # Integration tests

# 2. dbt tests (if using dbt)
dbt test

# 3. Python unit tests
pytest tests/ -v

# 4. With coverage report
pytest tests/ --cov=python --cov-report=html

# 5. Concurrency stress test (custom)
pytest tests/test_concurrency.py -v --count=100

# All together
mxcp validate && mxcp test && dbt test && pytest tests/ -v
```

## Summary

**Both types of tests are required**:

1. **MXCP tests** - Verify tools work end-to-end
2. **Python unit tests** - Verify logic, mocking, correctness, concurrency

**Key principles**:
- ✅ **Mock all external calls** - Use pytest-httpx, unittest.mock
- ✅ **Verify result correctness** - Don't just check structure
- ✅ **Use test databases** - SQL tools need real data
- ✅ **Test concurrency** - Tools run as servers
- ✅ **Avoid global mutable state** - Use stateless patterns or locks
- ✅ **Test edge cases** - Empty data, NULL, invalid input

**Before declaring a project done, BOTH test types must pass completely.**
