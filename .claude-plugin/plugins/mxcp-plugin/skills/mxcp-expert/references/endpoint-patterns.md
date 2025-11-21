# Endpoint Patterns

Complete examples for creating MXCP endpoints (tools, resources, prompts).

## SQL Tool - Data Query

```yaml
# tools/sales_report.yml
mxcp: 1
tool:
  name: sales_report
  description: "Get sales data by region and date range"
  parameters:
    - name: region
      type: string
      examples: ["US-West"]
    - name: start_date
      type: string
      format: date
    - name: end_date
      type: string
      format: date
  return:
    type: object
    properties:
      total_sales: { type: number }
      count: { type: integer }
  source:
    code: |
      SELECT SUM(amount) as total_sales, COUNT(*) as count
      FROM sales
      WHERE region = $region 
        AND sale_date BETWEEN $start_date AND $end_date
```

## Python Tool - ML/API Integration

```yaml
# tools/analyze_sentiment.yml
mxcp: 1
tool:
  name: analyze_sentiment
  description: "Analyze sentiment using ML"
  language: python
  parameters:
    - name: texts
      type: array
      items: { type: string }
  return:
    type: array
    items:
      type: object
      properties:
        text: { type: string }
        sentiment: { type: string }
        confidence: { type: number }
  source:
    file: ../python/sentiment.py
```

```python
# python/sentiment.py
from mxcp.runtime import db, on_init
import asyncio

@on_init
def load_model():
    # Load model once at startup
    pass

async def analyze_sentiment(texts: list[str]) -> list[dict]:
    async def analyze_one(text: str) -> dict:
        sentiment = "positive" if "good" in text else "neutral"
        
        db.execute(
            "INSERT INTO logs (text, sentiment) VALUES ($1, $2)",
            {"text": text, "sentiment": sentiment}
        )
        
        return {"text": text, "sentiment": sentiment, "confidence": 0.85}
    
    return await asyncio.gather(*[analyze_one(t) for t in texts])
```

## Resource - Data Access

```yaml
# resources/customer_data.yml
mxcp: 1
resource:
  uri: "customer://data/{customer_id}"
  description: "Get customer profile"
  mime_type: "application/json"
  parameters:
    - name: customer_id
      type: string
  return:
    type: object
    properties:
      id: { type: string }
      name: { type: string }
      email: { type: string }
  source:
    code: |
      SELECT id, name, email FROM customers WHERE id = $customer_id
```

## Prompt Template

```yaml
# prompts/customer_analysis.yml
mxcp: 1
prompt:
  name: customer_analysis
  description: "Analyze customer behavior"
  parameters:
    - name: customer_id
      type: string
  messages:
    - role: system
      type: text
      prompt: "You are a customer analytics expert."
    - role: user
      type: text
      prompt: "Analyze customer {{ customer_id }} and provide insights."
```

## Combined SQL + Python

```yaml
# tools/customer_insights.yml
mxcp: 1
tool:
  name: customer_insights
  language: python
  source:
    file: ../python/insights.py
```

```python
# python/insights.py
from mxcp.runtime import db

def customer_insights(customer_id: str) -> dict:
    # SQL for aggregation
    stats = db.execute("""
        SELECT COUNT(*) as orders, SUM(amount) as total
        FROM orders WHERE customer_id = $id
    """, {"id": customer_id}).fetchone()
    
    # Python for analysis
    trend = calculate_trend(stats)
    
    return {**dict(stats), "trend": trend}
```

## With Policies

```yaml
tool:
  name: employee_data
  policies:
    input:
      - condition: "!('hr.read' in user.permissions)"
        action: deny
    output:
      - condition: "user.role != 'hr_manager'"
        action: filter_fields
        fields: ["salary", "ssn"]
```

## With Tests

```yaml
tool:
  name: calculate_total
  tests:
    - name: "basic_test"
      arguments:
        - key: amount
          value: 100
        - key: tax_rate
          value: 0.1
      result:
        total: 110
        tax: 10
```
