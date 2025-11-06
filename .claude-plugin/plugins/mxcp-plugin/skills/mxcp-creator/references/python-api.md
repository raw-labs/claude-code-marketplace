# Python Runtime API Reference

Complete reference for MXCP Python endpoints, including wrapping external libraries and packages.

## Database Access

```python
from mxcp.runtime import db

# Execute query
results = db.execute(
    "SELECT * FROM users WHERE id = $id",
    {"id": user_id}
)

# Get first result
first = results[0] if results else None

# Iterate results
for row in results:
    print(row["name"])
```

**Important**: Always access through `db.execute()`, never cache `db.connection`.

## Configuration & Secrets

```python
from mxcp.runtime import config

# Get secret (returns dict with parameters)
secret = config.get_secret("api_key")
api_key = secret["value"] if secret else None

# For complex secrets (like HTTP with headers)
http_secret = config.get_secret("api_service")
if http_secret:
    token = http_secret.get("BEARER_TOKEN")
    headers = http_secret.get("EXTRA_HTTP_HEADERS", {})

# Get settings
project_name = config.get_setting("project")
debug_mode = config.get_setting("debug", default=False)

# Access full configs
user_config = config.user_config
site_config = config.site_config
```

## Lifecycle Hooks

```python
from mxcp.runtime import on_init, on_shutdown
import httpx

client = None

@on_init
def setup():
    """Initialize resources at startup"""
    global client
    client = httpx.Client()
    print("Client initialized")

@on_shutdown
def cleanup():
    """Clean up resources at shutdown"""
    global client
    if client:
        client.close()
```

**IMPORTANT: Lifecycle hooks are for Python resources ONLY**

- ✅ **USE FOR**: HTTP clients, external API connections, ML model loading, cache clients
- ❌ **DON'T USE FOR**: Database management, DuckDB connections, dbt operations

The DuckDB connection is managed automatically by MXCP. These hooks are for managing Python-specific resources that need initialization at server startup and cleanup at shutdown.

## Async Functions

```python
import asyncio
import aiohttp

async def fetch_data(urls: list[str]) -> list[dict]:
    """Fetch from multiple URLs concurrently"""
    
    async def fetch_one(url: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()
    
    results = await asyncio.gather(*[fetch_one(url) for url in urls])
    return results
```

## Return Types

Match your function return to the endpoint's return type:

```python
# Array return
def list_items() -> list:
    return [{"id": 1}, {"id": 2}]

# Object return
def get_stats() -> dict:
    return {"total": 100, "active": 75}

# Scalar return
def count_items() -> int:
    return 42
```

## Shared Modules

Organize code in subdirectories:

```python
# python/utils/validators.py
def validate_email(email: str) -> bool:
    import re
    return bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email))

# python/main_tool.py
from utils.validators import validate_email

def process_user(email: str) -> dict:
    if not validate_email(email):
        return {"error": "Invalid email"}
    return {"status": "ok"}
```

## Error Handling

```python
def safe_divide(a: float, b: float) -> dict:
    if b == 0:
        return {"error": "Division by zero"}
    return {"result": a / b}
```

## External API Integration Pattern

```python
import httpx
from mxcp.runtime import config, db

async def call_external_api(param: str) -> dict:
    # Get API key
    api_key = config.get_secret("external_api")["value"]
    
    # Check cache
    cached = db.execute(
        "SELECT data FROM cache WHERE key = $key AND ts > datetime('now', '-1 hour')",
        {"key": param}
    ).fetchone()
    
    if cached:
        return cached["data"]
    
    # Make API call
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.example.com/data",
            params={"q": param, "key": api_key}
        )
        data = response.json()
    
    # Cache result
    db.execute(
        "INSERT OR REPLACE INTO cache (key, data, ts) VALUES ($1, $2, CURRENT_TIMESTAMP)",
        {"key": param, "data": data}
    )
    
    return data
```

## Database Reload (Advanced)

Use `reload_duckdb` only when external tools need exclusive database access:

```python
from mxcp.runtime import reload_duckdb

def rebuild_database():
    """Trigger database rebuild"""
    
    def rebuild():
        # Run with exclusive database access
        import subprocess
        subprocess.run(["dbt", "run"], check=True)
    
    reload_duckdb(
        payload_func=rebuild,
        description="Rebuilding with dbt"
    )
    
    return {"status": "Reload scheduled"}
```

**Note**: Normally you don't need this. Use `db.execute()` for direct operations.

## Wrapping External Libraries

### Pattern 1: Simple Library Wrapper

**Use case**: Expose existing Python library as MCP tool

```python
# python/library_wrapper.py
"""Wrapper for an existing library like requests, pandas, etc."""

import requests
from mxcp.runtime import get_secret

def fetch_url(url: str, method: str = "GET", headers: dict = None) -> dict:
    """Wrap requests library as MCP tool"""
    try:
        # Get auth if needed
        secret = get_secret("api_token")
        if secret and headers is None:
            headers = {"Authorization": f"Bearer {secret['token']}"}

        response = requests.request(method, url, headers=headers, timeout=30)
        response.raise_for_status()

        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        }
    except requests.RequestException as e:
        return {"error": str(e), "status": "failed"}
```

```yaml
# tools/http_request.yml
mxcp: 1
tool:
  name: http_request
  description: "Make HTTP requests using requests library"
  language: python
  parameters:
    - name: url
      type: string
    - name: method
      type: string
      default: "GET"
  return:
    type: object
  source:
    file: ../python/library_wrapper.py
```

### Pattern 2: Data Science Library Wrapper (pandas, numpy)

```python
# python/data_analysis.py
"""Wrap pandas for data analysis"""

import pandas as pd
import numpy as np
from mxcp.runtime import db

def analyze_dataframe(table_name: str) -> dict:
    """Analyze a table using pandas"""
    # Read from DuckDB into pandas
    df = db.execute(f"SELECT * FROM {table_name}").df()

    # Pandas analysis
    analysis = {
        "shape": df.shape,
        "columns": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "summary_stats": df.describe().to_dict(),
        "memory_usage": df.memory_usage(deep=True).sum()
    }

    # Numeric column correlations
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 1:
        analysis["correlations"] = df[numeric_cols].corr().to_dict()

    return analysis

def pandas_query(table_name: str, operation: str) -> dict:
    """Execute pandas operations on DuckDB table"""
    df = db.execute(f"SELECT * FROM {table_name}").df()

    # Support common pandas operations
    if operation == "describe":
        result = df.describe().to_dict()
    elif operation == "head":
        result = df.head(10).to_dict('records')
    elif operation == "value_counts":
        # For first categorical column
        cat_col = df.select_dtypes(include=['object']).columns[0]
        result = df[cat_col].value_counts().to_dict()
    else:
        return {"error": f"Unknown operation: {operation}"}

    return {"operation": operation, "result": result}
```

### Pattern 3: ML Library Wrapper (scikit-learn)

```python
# python/ml_wrapper.py
"""Wrap scikit-learn for ML tasks"""

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from mxcp.runtime import db, on_init
import pickle
import os

# Global model store
models = {}

@on_init
def load_models():
    """Load saved models on startup"""
    global models
    model_dir = "models"
    if os.path.exists(model_dir):
        for file in os.listdir(model_dir):
            if file.endswith('.pkl'):
                model_name = file[:-4]
                with open(os.path.join(model_dir, file), 'rb') as f:
                    models[model_name] = pickle.load(f)

def train_classifier(
    table_name: str,
    target_column: str,
    feature_columns: list[str],
    model_name: str = "default"
) -> dict:
    """Train a classifier on DuckDB table"""
    # Load data
    df = db.execute(f"SELECT * FROM {table_name}").df()

    X = df[feature_columns]
    y = df[target_column]

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)

    # Save model
    global models
    models[model_name] = model
    os.makedirs("models", exist_ok=True)
    with open(f"models/{model_name}.pkl", 'wb') as f:
        pickle.dump(model, f)

    return {
        "model_name": model_name,
        "train_accuracy": train_score,
        "test_accuracy": test_score,
        "feature_importance": dict(zip(feature_columns, model.feature_importances_))
    }

def predict(model_name: str, features: dict) -> dict:
    """Make prediction with trained model"""
    if model_name not in models:
        return {"error": f"Model '{model_name}' not found"}

    model = models[model_name]

    # Convert features to DataFrame with correct order
    import pandas as pd
    feature_df = pd.DataFrame([features])

    prediction = model.predict(feature_df)[0]
    probabilities = model.predict_proba(feature_df)[0] if hasattr(model, 'predict_proba') else None

    return {
        "prediction": prediction,
        "probabilities": probabilities.tolist() if probabilities is not None else None
    }
```

### Pattern 4: API Client Library Wrapper

```python
# python/api_client_wrapper.py
"""Wrap an API client library (e.g., stripe, twilio, sendgrid)"""

import stripe
from mxcp.runtime import get_secret, on_init

@on_init
def initialize_stripe():
    """Configure Stripe on startup"""
    secret = get_secret("stripe")
    if secret:
        stripe.api_key = secret["api_key"]

def create_customer(email: str, name: str) -> dict:
    """Wrap Stripe customer creation"""
    try:
        customer = stripe.Customer.create(
            email=email,
            name=name
        )
        return {
            "customer_id": customer.id,
            "email": customer.email,
            "name": customer.name,
            "created": customer.created
        }
    except stripe.error.StripeError as e:
        return {"error": str(e), "type": e.__class__.__name__}

def list_charges(customer_id: str = None, limit: int = 10) -> dict:
    """Wrap Stripe charges listing"""
    try:
        charges = stripe.Charge.list(
            customer=customer_id,
            limit=limit
        )
        return {
            "charges": [
                {
                    "id": charge.id,
                    "amount": charge.amount,
                    "currency": charge.currency,
                    "status": charge.status,
                    "created": charge.created
                }
                for charge in charges.data
            ]
        }
    except stripe.error.StripeError as e:
        return {"error": str(e)}
```

### Pattern 5: Async Library Wrapper

```python
# python/async_library_wrapper.py
"""Wrap async libraries like httpx, aiohttp"""

import httpx
import asyncio
from mxcp.runtime import get_secret

async def batch_fetch(urls: list[str]) -> list[dict]:
    """Fetch multiple URLs concurrently"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        async def fetch_one(url: str) -> dict:
            try:
                response = await client.get(url)
                return {
                    "url": url,
                    "status": response.status_code,
                    "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                }
            except Exception as e:
                return {"url": url, "error": str(e)}

        results = await asyncio.gather(*[fetch_one(url) for url in urls])
        return results

async def graphql_query(endpoint: str, query: str, variables: dict = None) -> dict:
    """Wrap GraphQL library/client"""
    secret = get_secret("graphql_api")
    headers = {"Authorization": f"Bearer {secret['token']}"} if secret else {}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            endpoint,
            json={"query": query, "variables": variables or {}},
            headers=headers
        )
        return response.json()
```

### Pattern 6: Complex Library with State Management

```python
# python/stateful_library_wrapper.py
"""Wrap libraries that maintain state (e.g., database connections, cache clients)"""

from redis import Redis
from mxcp.runtime import get_secret, on_init, on_shutdown

redis_client = None

@on_init
def connect_redis():
    """Initialize Redis connection on startup"""
    global redis_client
    secret = get_secret("redis")
    if secret:
        redis_client = Redis(
            host=secret["host"],
            port=secret.get("port", 6379),
            password=secret.get("password"),
            decode_responses=True
        )

@on_shutdown
def disconnect_redis():
    """Clean up Redis connection"""
    global redis_client
    if redis_client:
        redis_client.close()

def cache_set(key: str, value: str, ttl: int = 3600) -> dict:
    """Set value in Redis cache"""
    if not redis_client:
        return {"error": "Redis not configured"}

    try:
        redis_client.setex(key, ttl, value)
        return {"status": "success", "key": key, "ttl": ttl}
    except Exception as e:
        return {"error": str(e)}

def cache_get(key: str) -> dict:
    """Get value from Redis cache"""
    if not redis_client:
        return {"error": "Redis not configured"}

    try:
        value = redis_client.get(key)
        return {"key": key, "value": value, "found": value is not None}
    except Exception as e:
        return {"error": str(e)}
```

## Dependency Management

### requirements.txt

Always include dependencies for wrapped libraries:

```txt
# requirements.txt

# HTTP clients
requests>=2.31.0
httpx>=0.24.0
aiohttp>=3.8.0

# Data processing
pandas>=2.0.0
numpy>=1.24.0
openpyxl>=3.1.0  # For Excel support

# ML libraries
scikit-learn>=1.3.0

# API clients
stripe>=5.4.0
twilio>=8.0.0
sendgrid>=6.10.0

# Database/Cache
redis>=4.5.0
psycopg2-binary>=2.9.0  # For PostgreSQL

# Other common libraries
pillow>=10.0.0  # Image processing
beautifulsoup4>=4.12.0  # HTML parsing
lxml>=4.9.0  # XML parsing
```

### Installing Dependencies

```bash
# In project directory
pip install -r requirements.txt

# Or install specific library
pip install pandas requests
```

## Error Handling for Library Wrappers

**Always handle library-specific exceptions**:

```python
def safe_library_call(param: str) -> dict:
    """Template for safe library wrapping"""
    try:
        # Import library (can fail if not installed)
        import some_library

        # Use library
        result = some_library.do_something(param)

        return {"success": True, "result": result}

    except ImportError as e:
        return {
            "error": "Library not installed",
            "message": str(e),
            "fix": "Run: pip install some_library"
        }
    except some_library.SpecificError as e:
        return {
            "error": "Library-specific error",
            "message": str(e),
            "type": e.__class__.__name__
        }
    except Exception as e:
        return {
            "error": "Unexpected error",
            "message": str(e),
            "type": e.__class__.__name__
        }
```

## Database Reload (Advanced)

**Important**: In most cases, you DON'T need this feature. Use `db.execute()` directly for database operations.

The `reload_duckdb()` function allows Python endpoints to trigger a safe reload of the DuckDB database. This is **only** needed when external processes require exclusive access to the database file.

### When to Use

Use `reload_duckdb()` ONLY when:
- External tools need exclusive database access (e.g., running `dbt` as a subprocess)
- You're replacing the entire database file
- External processes cannot operate within the same Python process

### When NOT to Use

- ❌ Regular database operations (use `db.execute()` instead)
- ❌ Running dbt (use dbt Python API directly in the same process)
- ❌ Loading data from APIs/files (use `db.execute()` to insert data)

DuckDB's concurrency model allows the MXCP process to own the connection while multiple threads operate safely. Only use `reload_duckdb()` if you absolutely must have an external process update the database file.

### API

```python
from mxcp.runtime import reload_duckdb

def update_data_endpoint() -> dict:
    """Endpoint that triggers a data refresh"""

    def rebuild_database():
        """
        This function runs with all connections closed.
        You have exclusive access to the DuckDB file.
        """
        # Example: Run external tool
        import subprocess
        subprocess.run(["dbt", "run", "--target", "prod"], check=True)

        # Or: Replace with pre-built database
        import shutil
        shutil.copy("/staging/analytics.duckdb", "/app/data/analytics.duckdb")

        # Or: Load fresh data
        import pandas as pd
        import duckdb
        df = pd.read_parquet("s3://bucket/latest-data.parquet")
        conn = duckdb.connect("/app/data/analytics.duckdb")
        conn.execute("CREATE OR REPLACE TABLE sales AS SELECT * FROM df")
        conn.close()

    # Schedule the reload (happens asynchronously)
    reload_duckdb(
        payload_func=rebuild_database,
        description="Updating analytics data"
    )

    # Return immediately - reload happens in background
    return {
        "status": "scheduled",
        "message": "Data refresh will complete in background"
    }
```

### How It Works

When you call `reload_duckdb()`:

1. **Queues the reload** - Function returns immediately to client
2. **Drains active requests** - Existing requests complete normally
3. **Shuts down runtime** - Closes Python hooks and DuckDB connections
4. **Runs your payload** - With all connections closed and exclusive access
5. **Restarts runtime** - Fresh configuration and connections
6. **Processes waiting requests** - With the updated data

### Real-World Example

```python
from mxcp.runtime import reload_duckdb, db
from datetime import datetime
import requests

def scheduled_update(source: str = "api") -> dict:
    """Endpoint called by cron to update data"""

    def rebuild_from_api():
        # Fetch data from external API
        response = requests.get("https://api.example.com/analytics/export")
        data = response.json()

        # Write to DuckDB (exclusive access guaranteed)
        import duckdb
        conn = duckdb.connect("/app/data/analytics.duckdb")

        # Clear old data
        conn.execute("DROP TABLE IF EXISTS daily_metrics")

        # Load new data
        conn.execute("""
            CREATE TABLE daily_metrics AS
            SELECT * FROM read_json_auto(?)
        """, [data])

        # Update metadata
        conn.execute("""
            INSERT INTO update_log (timestamp, source, record_count)
            VALUES (?, ?, ?)
        """, [datetime.now(), source, len(data)])

        conn.close()

    reload_duckdb(
        payload_func=rebuild_from_api,
        description=f"Scheduled update from {source}"
    )

    return {
        "status": "scheduled",
        "source": source,
        "timestamp": datetime.now().isoformat()
    }
```

### Best Practices

1. **Avoid when possible** - Prefer direct `db.execute()` operations
2. **Return immediately** - Don't wait for reload in your endpoint
3. **Handle errors in payload** - Wrap payload logic in try/except
4. **Keep payload fast** - Long-running payloads block new requests
5. **Document behavior** - Let users know data refresh is asynchronous

## Plugin System

MXCP supports a plugin system for extending DuckDB with custom Python functions.

### Accessing Plugins

```python
from mxcp.runtime import plugins

# Get a specific plugin
my_plugin = plugins.get("my_custom_plugin")
if my_plugin:
    result = my_plugin.some_method()

# List available plugins
available_plugins = plugins.list()
print(f"Available plugins: {available_plugins}")
```

### Example Usage

```python
def use_custom_function(data: str) -> dict:
    """Use a custom DuckDB function from a plugin"""

    # Get the plugin
    text_plugin = plugins.get("text_processing")
    if not text_plugin:
        return {"error": "text_processing plugin not available"}

    # Use plugin functionality
    result = text_plugin.normalize_text(data)

    return {"normalized": result}
```

### Plugin Definition

Plugins are defined in `plugins/` directory:

```python
# plugins/my_plugin.py
def custom_transform(value: str) -> str:
    """Custom transformation logic"""
    return value.upper()

# Register with DuckDB if needed
def register_functions(conn):
    """Register custom functions with DuckDB"""
    conn.create_function("custom_upper", custom_transform)
```

See official MXCP documentation for complete plugin development guide.

## Best Practices for Library Wrapping

1. **Initialize once**: Use `@on_init` for expensive setup (connections, model loading)
2. **Clean up**: Use `@on_shutdown` to release resources (HTTP clients, NOT database)
3. **Handle errors**: Catch library-specific exceptions, return error dicts
4. **Document dependencies**: List in requirements.txt with versions
5. **Type hints**: Add for better IDE support and documentation
6. **Async when appropriate**: Use async for I/O-bound library operations
7. **State management**: Use global variables + lifecycle hooks for stateful clients
8. **Version pin**: Pin library versions to avoid breaking changes
9. **Timeout handling**: Add timeouts for network operations
10. **Return simple types**: Convert library-specific objects to dicts/lists

## General Best Practices

1. **Database Access**: Always use `db.execute()`, never cache connections
2. **Error Handling**: Return error dicts instead of raising exceptions
3. **Type Hints**: Use for better IDE support
4. **Logging**: Use standard Python logging
5. **Resource Management**: Use context managers
6. **Async**: Use for I/O-bound operations
