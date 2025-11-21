# Error Handling Guide

**Comprehensive error handling for MXCP servers: SQL errors (managed by MXCP) and Python errors (YOU must handle).**

## Two Types of Error Handling

### 1. SQL Errors (Managed by MXCP)

**MXCP automatically handles**:
- SQL syntax errors
- Type mismatches
- Parameter binding errors
- Database connection errors

**Your responsibility**:
- Write correct SQL
- Use proper parameter binding (`$param`)
- Match return types to actual data

### 2. Python Errors (YOU Must Handle)

**You MUST handle**:
- External API failures
- Invalid input
- Resource not found
- Business logic errors
- Async/await errors

**Return structured error objects, don't raise exceptions to MXCP.**

## Python Error Handling Pattern

### ❌ WRONG: Let Exceptions Bubble Up

```python
# python/api_wrapper.py
async def fetch_user(user_id: int) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/users/{user_id}")
        response.raise_for_status()  # ❌ Will crash if 404/500!
        return response.json()
```

**Problem**: When API returns 404, exception crashes the tool. LLM gets unhelpful error.

### ✅ CORRECT: Return Structured Errors

```python
# python/api_wrapper.py
import httpx

async def fetch_user(user_id: int) -> dict:
    """
    Fetch user from external API.

    Returns:
        Success: {"success": true, "user": {...}}
        Error: {"success": false, "error": "User not found", "error_code": "NOT_FOUND"}
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://api.example.com/users/{user_id}"
            )

            if response.status_code == 404:
                return {
                    "success": False,
                    "error": f"User with ID {user_id} not found",
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

            response.raise_for_status()  # Other HTTP errors

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

    except httpx.HTTPError as e:
        return {
            "success": False,
            "error": f"HTTP error occurred: {str(e)}",
            "error_code": "HTTP_ERROR"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "error_code": "UNKNOWN_ERROR"
        }
```

**Why good**:
- ✅ LLM gets clear error message
- ✅ LLM knows what went wrong (error_code)
- ✅ LLM can take action (retry, try different ID, etc.)
- ✅ Tool never crashes

## Error Response Structure

### Standard Error Format

```python
{
    "success": False,
    "error": "Human-readable error message for LLM",
    "error_code": "MACHINE_READABLE_CODE",
    "details": {  # Optional: additional context
        "attempted_value": user_id,
        "valid_range": "1-1000"
    }
}
```

### Standard Success Format

```python
{
    "success": True,
    "data": {
        # Actual response data
    }
}
```

## Common Error Scenarios

### 1. Input Validation Errors

```python
def process_order(order_id: str, quantity: int) -> dict:
    """Process an order with validation"""

    # Validate order_id format
    if not order_id.startswith("ORD_"):
        return {
            "success": False,
            "error": f"Invalid order ID format. Expected format: 'ORD_XXXXX', got: '{order_id}'",
            "error_code": "INVALID_FORMAT",
            "expected_format": "ORD_XXXXX",
            "provided": order_id
        }

    # Validate quantity range
    if quantity <= 0:
        return {
            "success": False,
            "error": f"Quantity must be positive. Got: {quantity}",
            "error_code": "INVALID_QUANTITY",
            "provided": quantity,
            "valid_range": "1 or greater"
        }

    if quantity > 1000:
        return {
            "success": False,
            "error": f"Quantity {quantity} exceeds maximum allowed (1000). Please split into multiple orders.",
            "error_code": "QUANTITY_EXCEEDED",
            "provided": quantity,
            "maximum": 1000
        }

    # Process order...
    return {"success": True, "order_id": order_id, "quantity": quantity}
```

### 2. Resource Not Found Errors

```python
from mxcp.runtime import db

def get_customer(customer_id: str) -> dict:
    """Get customer by ID with proper error handling"""

    try:
        result = db.execute(
            "SELECT * FROM customers WHERE customer_id = $1",
            {"customer_id": customer_id}
        )

        customer = result.fetchone()

        if customer is None:
            return {
                "success": False,
                "error": f"Customer '{customer_id}' not found in database. Use list_customers to see available customers.",
                "error_code": "CUSTOMER_NOT_FOUND",
                "customer_id": customer_id,
                "suggestion": "Call list_customers tool to see all available customer IDs"
            }

        return {
            "success": True,
            "customer": dict(customer)
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Database error while fetching customer: {str(e)}",
            "error_code": "DATABASE_ERROR"
        }
```

### 3. External API Errors

```python
import httpx

async def create_customer_in_stripe(email: str, name: str) -> dict:
    """Create Stripe customer with comprehensive error handling"""

    try:
        import stripe
        from mxcp.runtime import get_secret

        # Get API key
        secret = get_secret("stripe")
        if not secret:
            return {
                "success": False,
                "error": "Stripe API key not configured. Please set up 'stripe' secret in config.yml",
                "error_code": "MISSING_CREDENTIALS",
                "required_secret": "stripe"
            }

        stripe.api_key = secret.get("api_key")

        # Create customer
        customer = stripe.Customer.create(
            email=email,
            name=name
        )

        return {
            "success": True,
            "customer_id": customer.id,
            "email": customer.email
        }

    except stripe.error.InvalidRequestError as e:
        return {
            "success": False,
            "error": f"Invalid request to Stripe: {str(e)}",
            "error_code": "INVALID_REQUEST",
            "details": str(e)
        }

    except stripe.error.AuthenticationError:
        return {
            "success": False,
            "error": "Stripe API key is invalid or expired. Please update credentials.",
            "error_code": "AUTHENTICATION_FAILED"
        }

    except stripe.error.RateLimitError:
        return {
            "success": False,
            "error": "Stripe rate limit exceeded. Please try again in a few seconds.",
            "error_code": "RATE_LIMIT",
            "suggestion": "Wait 5-10 seconds and retry"
        }

    except stripe.error.StripeError as e:
        return {
            "success": False,
            "error": f"Stripe error: {str(e)}",
            "error_code": "STRIPE_ERROR"
        }

    except ImportError:
        return {
            "success": False,
            "error": "Stripe library not installed. Run: pip install stripe",
            "error_code": "MISSING_DEPENDENCY",
            "fix": "pip install stripe>=5.0.0"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "error_code": "UNKNOWN_ERROR"
        }
```

### 4. Business Logic Errors

```python
def transfer_funds(from_account: str, to_account: str, amount: float) -> dict:
    """Transfer funds with business logic validation"""

    # Check amount
    if amount <= 0:
        return {
            "success": False,
            "error": f"Transfer amount must be positive. Got: ${amount}",
            "error_code": "INVALID_AMOUNT"
        }

    # Check account exists and get balance
    from_balance = db.execute(
        "SELECT balance FROM accounts WHERE account_id = $1",
        {"account_id": from_account}
    ).fetchone()

    if from_balance is None:
        return {
            "success": False,
            "error": f"Source account '{from_account}' not found",
            "error_code": "ACCOUNT_NOT_FOUND",
            "account_id": from_account
        }

    # Check sufficient funds
    if from_balance["balance"] < amount:
        return {
            "success": False,
            "error": f"Insufficient funds. Available: ${from_balance['balance']:.2f}, Requested: ${amount:.2f}",
            "error_code": "INSUFFICIENT_FUNDS",
            "available": from_balance["balance"],
            "requested": amount,
            "shortfall": amount - from_balance["balance"]
        }

    # Perform transfer...
    return {
        "success": True,
        "transfer_id": "TXN_12345",
        "from_account": from_account,
        "to_account": to_account,
        "amount": amount
    }
```

### 5. Async/Await Errors

```python
import asyncio

async def fetch_multiple_users(user_ids: list[int]) -> dict:
    """Fetch multiple users concurrently with error handling"""

    async def fetch_one(user_id: int) -> dict:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"https://api.example.com/users/{user_id}")

                if response.status_code == 404:
                    return {
                        "user_id": user_id,
                        "success": False,
                        "error": f"User {user_id} not found"
                    }

                response.raise_for_status()
                return {
                    "user_id": user_id,
                    "success": True,
                    "user": response.json()
                }

        except asyncio.TimeoutError:
            return {
                "user_id": user_id,
                "success": False,
                "error": f"Timeout fetching user {user_id}"
            }

        except Exception as e:
            return {
                "user_id": user_id,
                "success": False,
                "error": str(e)
            }

    # Fetch all concurrently
    results = await asyncio.gather(*[fetch_one(uid) for uid in user_ids])

    # Separate successes and failures
    successes = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]

    return {
        "success": len(failures) == 0,
        "total_requested": len(user_ids),
        "successful": len(successes),
        "failed": len(failures),
        "users": [r["user"] for r in successes],
        "errors": [{"user_id": r["user_id"], "error": r["error"]} for r in failures]
    }
```

## Error Messages for LLMs

### Principles for Good Error Messages

1. **Be Specific**: Tell exactly what went wrong
2. **Be Actionable**: Suggest what to do next
3. **Provide Context**: Include relevant values/IDs
4. **Use Plain Language**: Avoid technical jargon

### ❌ BAD Error Messages

```python
return {"error": "Error"}  # ❌ Useless
return {"error": "Invalid input"}  # ❌ Which input? Why invalid?
return {"error": "DB error"}  # ❌ What kind of error?
return {"error": str(e)}  # ❌ Raw exception message (often cryptic)
```

### ✅ GOOD Error Messages

```python
return {
    "error": "Customer ID 'CUST_999' not found. Use list_customers to see available IDs."
}

return {
    "error": "Date format invalid. Expected 'YYYY-MM-DD' (e.g., '2024-01-15'), got: '01/15/2024'"
}

return {
    "error": "Quantity 5000 exceeds maximum allowed (1000). Split into multiple orders or contact support."
}

return {
    "error": "API rate limit exceeded. Please wait 30 seconds and try again."
}
```

## SQL Error Handling (MXCP Managed)

### You Don't Handle These (MXCP Does)

MXCP automatically handles and returns errors for:
- Invalid SQL syntax
- Missing tables/columns
- Type mismatches
- Parameter binding errors

**Your job**: Write correct SQL and let MXCP handle errors.

### Prevent SQL Errors

#### 1. Validate Schema

```yaml
# Always define return types to match SQL output
tool:
  name: get_stats
  return:
    type: object
    properties:
      total: { type: number }  # Matches SQL: SUM(amount)
      count: { type: integer }  # Matches SQL: COUNT(*)
  source:
    code: |
      SELECT
        SUM(amount) as total,
        COUNT(*) as count
      FROM orders
```

#### 2. Handle NULL Values

```sql
-- BAD: Might return NULL which breaks type system
SELECT amount FROM orders WHERE id = $order_id

-- GOOD: Handle potential NULL
SELECT COALESCE(amount, 0) as amount
FROM orders
WHERE id = $order_id

-- GOOD: Use IFNULL/COALESCE for aggregations
SELECT
  COALESCE(SUM(amount), 0) as total,
  COALESCE(AVG(amount), 0) as average
FROM orders
WHERE status = $status
```

#### 3. Handle Empty Results

```sql
-- If no results, return empty array (not NULL)
SELECT * FROM customers WHERE city = $city
-- Returns: [] if no customers (MXCP handles this)

-- For aggregations, always return a row
SELECT
  COUNT(*) as count,
  COALESCE(SUM(amount), 0) as total
FROM orders
WHERE status = $status
-- Always returns one row, even if no matching orders
```

## Error Codes Convention

**Use consistent error codes across your tools**:

```python
# Standard error codes
ERROR_CODES = {
    # Input validation
    "INVALID_FORMAT": "Input format is incorrect",
    "INVALID_RANGE": "Value outside valid range",
    "MISSING_REQUIRED": "Required parameter missing",

    # Resource errors
    "NOT_FOUND": "Resource not found",
    "ALREADY_EXISTS": "Resource already exists",
    "DELETED": "Resource has been deleted",

    # Permission errors
    "UNAUTHORIZED": "User not authenticated",
    "FORBIDDEN": "User lacks permission",

    # External service errors
    "API_ERROR": "External API error",
    "TIMEOUT": "Request timed out",
    "RATE_LIMIT": "Rate limit exceeded",

    # System errors
    "DATABASE_ERROR": "Database operation failed",
    "CONFIGURATION_ERROR": "Missing or invalid configuration",
    "DEPENDENCY_ERROR": "Required library not installed",

    # Business logic errors
    "INSUFFICIENT_FUNDS": "Not enough balance",
    "INVALID_STATE": "Operation not allowed in current state",
    "QUOTA_EXCEEDED": "Usage quota exceeded",

    # Unknown
    "UNKNOWN_ERROR": "Unexpected error occurred"
}
```

## Testing Error Handling

### Unit Tests for Error Cases

```python
# tests/test_error_handling.py
import pytest
from python.my_module import fetch_user

@pytest.mark.asyncio
async def test_fetch_user_not_found(httpx_mock):
    """Test 404 error handling"""
    httpx_mock.add_response(
        url="https://api.example.com/users/999",
        status_code=404
    )

    result = await fetch_user(999)

    assert result["success"] is False
    assert result["error_code"] == "NOT_FOUND"
    assert "999" in result["error"]  # Error mentions the ID

@pytest.mark.asyncio
async def test_fetch_user_timeout(httpx_mock):
    """Test timeout handling"""
    httpx_mock.add_exception(httpx.TimeoutException("Timeout"))

    result = await fetch_user(123)

    assert result["success"] is False
    assert result["error_code"] == "TIMEOUT"
    assert "timeout" in result["error"].lower()

def test_invalid_input():
    """Test input validation"""
    result = process_order("INVALID", quantity=5)

    assert result["success"] is False
    assert result["error_code"] == "INVALID_FORMAT"
    assert "ORD_" in result["error"]  # Mentions expected format
```

## Error Handling Checklist

Before declaring Python tool complete:

- [ ] All external API calls wrapped in try/except
- [ ] All exceptions return structured error objects
- [ ] Error messages are clear and actionable
- [ ] Error codes are consistent
- [ ] Input validation with helpful error messages
- [ ] NULL/None values handled gracefully
- [ ] Timeout handling for network calls
- [ ] Missing dependencies handled (ImportError)
- [ ] Database errors caught and explained
- [ ] Success/failure clearly indicated in response
- [ ] Unit tests for error scenarios
- [ ] Error messages help LLM understand what to do next

## Summary

**SQL Tools (MXCP Handles)**:
- Write correct SQL
- Handle NULL values with COALESCE
- Match return types to SQL output

**Python Tools (YOU Handle)**:
- ✅ Wrap ALL external calls in try/except
- ✅ Return structured error objects (`{"success": False, "error": "...", "error_code": "..."}`)
- ✅ Validate inputs with clear error messages
- ✅ Be specific and actionable in error messages
- ✅ Use consistent error codes
- ✅ Test error scenarios
- ✅ NEVER let exceptions bubble up to MXCP

**Golden Rule**: Errors should help the LLM understand what went wrong and what to do next.
