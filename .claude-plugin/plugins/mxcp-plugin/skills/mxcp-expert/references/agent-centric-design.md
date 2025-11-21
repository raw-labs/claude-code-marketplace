# Agent-Centric Design for MXCP Tools

**Designing MXCP tools that LLMs can effectively use with zero prior context.**

## Overview

When building MXCP servers, remember: **LLMs are your primary users**. Your tools must enable LLMs to accomplish real-world tasks effectively. This guide provides principles for designing tools that work well for AI agents.

## Core Principles

### 1. Build for Workflows, Not Just Data Access

**Don't simply expose database tables or API endpoints - design tools around complete workflows.**

#### ❌ Poor Design: Raw Data Access
```yaml
# tools/get_user.yml
tool:
  name: get_user
  description: "Get user by ID"
  parameters:
    - name: user_id
      type: integer
  source:
    code: SELECT * FROM users WHERE id = $user_id

# tools/get_orders.yml
tool:
  name: get_orders
  description: "Get orders by user"
  parameters:
    - name: user_id
      type: integer
  source:
    code: SELECT * FROM orders WHERE user_id = $user_id
```

**Problem**: LLM needs multiple tool calls to answer "What did user 123 buy?"

#### ✅ Good Design: Workflow-Oriented
```yaml
# tools/get_user_purchase_summary.yml
tool:
  name: get_user_purchase_summary
  description: "Get complete purchase history for a user including orders, products, and total spending. Use this to understand a user's buying behavior and preferences."
  parameters:
    - name: user_id
      type: integer
      description: "User identifier"
    - name: date_range
      type: string
      description: "Optional date range: 'last_30_days', 'last_year', or 'all_time'"
      default: "all_time"
  return:
    type: object
    properties:
      user_info: { type: object, description: "Basic user information" }
      order_count: { type: integer, description: "Total number of orders" }
      total_spent: { type: number, description: "Total amount spent in USD" }
      top_products: { type: array, description: "Most frequently purchased products" }
  source:
    code: |
      WITH user_orders AS (
        SELECT o.*, p.name as product_name, p.category
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        JOIN products p ON oi.product_id = p.id
        WHERE o.user_id = $user_id
          AND ($date_range = 'all_time'
               OR ($date_range = 'last_30_days' AND o.created_at > CURRENT_DATE - INTERVAL 30 DAY)
               OR ($date_range = 'last_year' AND o.created_at > CURRENT_DATE - INTERVAL 1 YEAR))
      )
      SELECT
        json_object(
          'user_info', (SELECT json_object('id', id, 'name', name) FROM users WHERE id = $user_id),
          'order_count', COUNT(DISTINCT id),
          'total_spent', SUM(total_amount),
          'top_products', (
            SELECT json_group_array(json_object('product', product_name, 'count', count))
            FROM (SELECT product_name, COUNT(*) as count FROM user_orders GROUP BY product_name ORDER BY count DESC LIMIT 5)
          )
        ) as result
      FROM user_orders
```

**Benefit**: Single tool call answers complete questions about user behavior.

### 2. Optimize for Limited Context

**LLMs have constrained context windows - make every token count.**

#### Design for Concise Responses

```yaml
tool:
  name: search_products
  parameters:
    - name: query
      type: string
      description: "Search query"
    - name: detail_level
      type: string
      description: "Response detail level"
      enum: ["minimal", "standard", "full"]
      default: "standard"
      examples:
        - "minimal: Only ID, name, price"
        - "standard: Basic info + category + stock"
        - "full: All fields including descriptions"
  source:
    code: |
      SELECT
        CASE $detail_level
          WHEN 'minimal' THEN json_object('id', id, 'name', name, 'price', price)
          WHEN 'standard' THEN json_object('id', id, 'name', name, 'price', price, 'category', category, 'stock', stock)
          ELSE json_object('id', id, 'name', name, 'price', price, 'category', category, 'stock', stock, 'description', description, 'specs', specs)
        END as product
      FROM products
      WHERE name LIKE '%' || $query || '%'
```

**Principle**: Default to high-signal information, provide options for more detail.

#### Use Human-Readable Identifiers

```yaml
# ✅ GOOD: Return names alongside IDs
return:
  type: object
  properties:
    customer_id: { type: string, description: "Customer ID (e.g., 'CUST_12345')" }
    customer_name: { type: string, description: "Customer display name" }
    assigned_to_id: { type: string, description: "Assigned user ID" }
    assigned_to_name: { type: string, description: "Assigned user name" }

# ❌ BAD: Only return opaque IDs
return:
  type: object
  properties:
    customer_id: { type: integer }
    assigned_to: { type: integer }
```

**Benefit**: LLM can understand relationships without additional lookups.

### 3. Design Actionable Error Messages

**Error messages should guide LLMs toward correct usage patterns.**

#### ✅ Good Error Messages (Python Tools)

```python
def search_large_dataset(query: str, limit: int = 100) -> dict:
    """Search with intelligent error guidance"""

    # Validate inputs
    if not query or len(query) < 3:
        return {
            "success": False,
            "error": "Query must be at least 3 characters. Provide a more specific search term to get better results.",
            "error_code": "QUERY_TOO_SHORT",
            "suggestion": "Try adding more keywords or using specific product names"
        }

    if limit > 1000:
        return {
            "success": False,
            "error": f"Limit of {limit} exceeds maximum allowed (1000). Use filters to narrow your search: add 'category' or 'price_range' parameters.",
            "error_code": "LIMIT_EXCEEDED",
            "max_limit": 1000,
            "suggestion": "Try using category='electronics' or price_range='0-100' to reduce results"
        }

    # Execute search
    results = db.execute(
        "SELECT * FROM products WHERE name LIKE $query LIMIT $limit",
        {"query": f"%{query}%", "limit": limit}
    )

    if not results:
        return {
            "success": False,
            "error": f"No products found matching '{query}'. Try broader terms or check spelling.",
            "error_code": "NO_RESULTS",
            "suggestion": "Use 'list_categories' tool to see available product categories"
        }

    return {
        "success": True,
        "count": len(results),
        "results": results
    }
```

**Principle**: Every error should suggest a specific next action.

### 4. Follow Natural Task Subdivisions

**Tool names should reflect how humans think about tasks, not just database structure.**

#### ✅ Good: Task-Oriented Naming
```
get_customer_purchase_history   # What users want to know
analyze_sales_by_region        # Natural analysis task
check_inventory_status         # Action-oriented
schedule_report_generation     # Complete workflow
```

#### ❌ Poor: Database-Oriented Naming
```
select_from_orders             # Database operation
join_users_and_purchases       # Technical operation
aggregate_by_column            # Generic operation
```

**Use consistent prefixes for discoverability**:
```yaml
# Customer operations
- get_customer_details
- get_customer_orders
- get_customer_analytics

# Product operations
- search_products
- get_product_details
- check_product_availability

# Analytics operations
- analyze_sales_trends
- analyze_customer_behavior
- analyze_inventory_turnover
```

### 5. Provide Comprehensive Documentation

**Every field must have a description that helps LLMs understand usage.**

See **references/llm-friendly-documentation.md** for complete documentation guidelines.

**Quick checklist**:
- [ ] Tool description explains WHAT, returns WHAT, WHEN to use
- [ ] Every parameter has description with examples
- [ ] Return type properties all have descriptions
- [ ] Cross-references to related tools
- [ ] Examples show realistic usage

## MXCP-Specific Best Practices

### Use SQL for Workflow Consolidation

**SQL is powerful for combining multiple data sources in one query:**

```yaml
tool:
  name: get_order_fulfillment_status
  description: "Get complete order fulfillment information including shipping, payments, and inventory status. Use this to answer questions about order status and estimated delivery."
  source:
    code: |
      SELECT
        o.id as order_id,
        o.status as order_status,
        u.name as customer_name,
        s.carrier,
        s.tracking_number,
        s.estimated_delivery,
        p.status as payment_status,
        json_group_array(
          json_object(
            'product', prod.name,
            'quantity', oi.quantity,
            'in_stock', prod.stock >= oi.quantity
          )
        ) as items
      FROM orders o
      JOIN users u ON o.user_id = u.id
      LEFT JOIN shipments s ON o.id = s.order_id
      LEFT JOIN payments p ON o.id = p.order_id
      JOIN order_items oi ON o.id = oi.order_id
      JOIN products prod ON oi.product_id = prod.id
      WHERE o.id = $order_id
      GROUP BY o.id
```

**Single tool call provides complete fulfillment picture.**

### Use Python for Complex Workflows

```python
async def analyze_customer_churn_risk(customer_id: str) -> dict:
    """
    Comprehensive churn risk analysis combining multiple data sources.

    Returns risk score, contributing factors, and recommended actions.
    Use this to identify customers who may leave and take preventive action.
    """
    # Get customer history
    orders = db.execute(
        "SELECT * FROM orders WHERE customer_id = $cid ORDER BY created_at DESC",
        {"cid": customer_id}
    )

    support_tickets = db.execute(
        "SELECT * FROM support_tickets WHERE customer_id = $cid",
        {"cid": customer_id}
    )

    # Calculate risk factors
    days_since_last_order = (datetime.now() - orders[0]["created_at"]).days if orders else 999
    unresolved_tickets = len([t for t in support_tickets if t["status"] != "resolved"])
    total_spent = sum(o["total_amount"] for o in orders)

    # Determine risk level
    risk_score = 0
    factors = []

    if days_since_last_order > 90:
        risk_score += 30
        factors.append("No purchases in 90+ days")

    if unresolved_tickets > 0:
        risk_score += 20 * unresolved_tickets
        factors.append(f"{unresolved_tickets} unresolved support tickets")

    if total_spent < 100:
        risk_score += 10
        factors.append("Low lifetime value")

    # Generate recommendations
    recommendations = []
    if days_since_last_order > 90:
        recommendations.append("Send re-engagement email with discount")
    if unresolved_tickets > 0:
        recommendations.append("Prioritize resolution of open support tickets")

    return {
        "success": True,
        "customer_id": customer_id,
        "risk_score": min(risk_score, 100),
        "risk_level": "high" if risk_score > 60 else "medium" if risk_score > 30 else "low",
        "contributing_factors": factors,
        "recommendations": recommendations,
        "days_since_last_order": days_since_last_order,
        "unresolved_tickets": unresolved_tickets
    }
```

### Leverage MXCP Policies for Context-Aware Tools

```yaml
tool:
  name: get_employee_compensation
  description: "Get employee compensation details. Returns salary and benefits information based on user permissions."
  parameters:
    - name: employee_id
      type: string
      description: "Employee identifier"
  return:
    type: object
    properties:
      employee_id: { type: string }
      name: { type: string }
      salary: { type: number, description: "Annual salary (admin only)" }
      benefits: { type: array, description: "Benefits package" }
  policies:
    output:
      - condition: "user.role != 'hr_manager' && user.role != 'admin'"
        action: filter_fields
        fields: ["salary"]
        reason: "Salary information restricted to HR managers and admins"
  source:
    code: |
      SELECT
        employee_id,
        name,
        salary,
        benefits
      FROM employees
      WHERE employee_id = $employee_id
```

**LLM can call same tool, MXCP automatically filters based on user context.**

## Testing Agent-Centric Design

### Create Realistic Evaluation Scenarios

See **references/mxcp-evaluation-guide.md** for complete evaluation guidelines.

**Quick validation**:
1. Can an LLM answer complex multi-step questions using your tools?
2. Do tool descriptions clearly indicate when to use each tool?
3. Do error messages guide the LLM toward correct usage?
4. Can common tasks be completed with minimal tool calls?

## Summary

**Agent-centric design principles for MXCP**:

1. ✅ **Build for workflows** - Consolidate related operations
2. ✅ **Optimize for context** - Provide detail level options, use readable identifiers
3. ✅ **Actionable errors** - Guide LLMs with specific suggestions
4. ✅ **Natural naming** - Task-oriented, not database-oriented
5. ✅ **Comprehensive docs** - Every parameter and field documented

**MXCP advantages**:
- SQL enables powerful workflow consolidation
- Python handles complex multi-step logic
- Policies provide automatic context-aware filtering
- Type system ensures clear contracts

**Remember**: Design for the LLM as your user, not the human. Humans configure tools, LLMs use them.
