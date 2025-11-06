# LLM-Friendly Documentation Guide

**CRITICAL: Tools must be self-documenting for LLMs without any prior context.**

## Core Principle

**LLMs connecting to MXCP servers have ZERO context about your domain, data, or tools.**

They only see:
- Tool name
- Tool description
- Parameter names and types
- Parameter descriptions
- Return type structure

**The documentation YOU provide is the ONLY information they have.**

## Tool Description Requirements

### ❌ BAD Tool Description

```yaml
tool:
  name: get_data
  description: "Gets data"  # ❌ Useless - what data? how? when to use?
  parameters:
    - name: id
      type: string  # ❌ No description - what kind of ID?
  return:
    type: array  # ❌ Array of what?
```

**Why bad**: LLM has no idea when to use this, what ID means, what data is returned.

### ✅ GOOD Tool Description

```yaml
tool:
  name: get_customer_orders
  description: "Retrieve all orders for a specific customer by customer ID. Returns order history including order date, total amount, status, and items. Use this to answer questions about a customer's purchase history or order status."
  parameters:
    - name: customer_id
      type: string
      description: "Unique customer identifier (e.g., 'CUST_12345'). Found in customer records or from list_customers tool."
      required: true
      examples: ["CUST_12345", "CUST_98765"]
    - name: status
      type: string
      description: "Optional filter by order status. Valid values: 'pending', 'shipped', 'delivered', 'cancelled'. Omit to get all orders."
      required: false
      examples: ["pending", "shipped"]
  return:
    type: array
    items:
      type: object
      properties:
        order_id: { type: string, description: "Unique order identifier" }
        order_date: { type: string, description: "ISO 8601 date when order was placed" }
        total_amount: { type: number, description: "Total order value in USD" }
        status: { type: string, description: "Current order status" }
        items: { type: array, description: "List of items in the order" }
```

**Why good**:
- LLM knows WHEN to use it (customer purchase history, order status)
- LLM knows WHAT parameters mean and valid values
- LLM knows WHAT will be returned
- LLM can chain with other tools (mentions list_customers)

## Description Template

### Tool-Level Description

**Format**: `<What it does> <What it returns> <When to use it>`

```yaml
description: "Retrieve sales analytics by region and time period. Returns aggregated metrics including total sales, transaction count, and average order value. Use this to answer questions about sales performance, regional comparisons, or time-based trends."
```

**Must include**:
1. **What**: What data/operation
2. **Returns**: Summary of return data
3. **When**: Use cases / when LLM should call this

### Parameter Description

**Format**: `<What it is> <Valid values/format> <Optional context>`

```yaml
parameters:
  - name: region
    type: string
    description: "Geographic region code. Valid values: 'north', 'south', 'east', 'west'. Use 'all' for aggregated data across all regions."
    examples: ["north", "south", "all"]

  - name: start_date
    type: string
    format: date
    description: "Start date for analytics period in YYYY-MM-DD format. Defaults to 30 days ago if omitted."
    required: false
    examples: ["2024-01-01", "2024-06-15"]

  - name: limit
    type: integer
    description: "Maximum number of results to return. Defaults to 100. Set to -1 for all results (use cautiously for large datasets)."
    default: 100
    examples: [10, 50, 100]
```

**Must include**:
1. **What it is**: Clear explanation
2. **Valid values**: Enums, formats, ranges
3. **Defaults**: If parameter is optional
4. **Examples**: Concrete examples

### Return Type Description

**Include descriptions for ALL fields**:

```yaml
return:
  type: object
  properties:
    total_sales:
      type: number
      description: "Sum of all sales in USD for the period"
    transaction_count:
      type: integer
      description: "Number of individual transactions"
    avg_order_value:
      type: number
      description: "Average transaction amount (total_sales / transaction_count)"
    top_products:
      type: array
      description: "Top 5 products by revenue"
      items:
        type: object
        properties:
          product_id: { type: string, description: "Product identifier" }
          product_name: { type: string, description: "Human-readable product name" }
          revenue: { type: number, description: "Total revenue for this product in USD" }
```

## Combining Tools - Cross-References

**Help LLMs chain tools together** by mentioning related tools:

```yaml
tool:
  name: get_customer_details
  description: "Get detailed information for a specific customer. Use customer_id from list_customers tool or search_customers tool. Returns personal info, account status, and lifetime value."
  # ... parameters ...
```

```yaml
tool:
  name: list_customers
  description: "List all customers with optional filtering. Returns customer_id needed for get_customer_details and get_customer_orders tools."
  # ... parameters ...
```

**LLM workflow enabled**:
1. LLM sees: "I need customer details"
2. Reads: "Use customer_id from list_customers tool"
3. Calls: `list_customers` first
4. Gets: `customer_id`
5. Calls: `get_customer_details` with that ID

## Examples in Descriptions

**ALWAYS provide concrete examples**:

```yaml
parameters:
  - name: date_range
    type: string
    description: "Date range in format 'YYYY-MM-DD to YYYY-MM-DD' or use shortcuts: 'today', 'yesterday', 'last_7_days', 'last_30_days', 'last_month', 'this_year'"
    examples:
      - "2024-01-01 to 2024-12-31"
      - "last_7_days"
      - "this_year"
```

## Error Cases in Descriptions

**Document expected errors**:

```yaml
tool:
  name: get_order
  description: "Retrieve order by order ID. Returns order details if found. Returns error if order_id doesn't exist or user doesn't have permission to view this order."
  parameters:
    - name: order_id
      type: string
      description: "Order identifier. Format: ORD_XXXXXX (e.g., 'ORD_123456'). Returns error if order not found."
```

## Resource URIs

**Make URI templates clear**:

```yaml
resource:
  uri: "customer://profile/{customer_id}"
  description: "Access customer profile data. Replace {customer_id} with actual customer ID (e.g., 'CUST_12345'). Returns 404 if customer doesn't exist."
  parameters:
    - name: customer_id
      type: string
      description: "Customer identifier from list_customers or search_customers"
```

## Prompt Templates

**Explain template variables clearly**:

```yaml
prompt:
  name: analyze_customer
  description: "Generate customer analysis report. Provide customer_id to analyze spending patterns, order frequency, and recommendations."
  parameters:
    - name: customer_id
      type: string
      description: "Customer to analyze (from list_customers)"
    - name: analysis_type
      type: string
      description: "Type of analysis: 'spending' (purchase patterns), 'behavior' (order frequency), 'recommendations' (product suggestions)"
      examples: ["spending", "behavior", "recommendations"]
  messages:
    - role: system
      type: text
      prompt: "You are a customer analytics expert. Analyze data thoroughly and provide actionable insights."
    - role: user
      type: text
      prompt: "Analyze customer {{ customer_id }} focusing on {{ analysis_type }}. Include specific metrics and recommendations."
```

## Complete Example: Well-Documented Tool Set

```yaml
# tools/list_products.yml
mxcp: 1
tool:
  name: list_products
  description: "List all available products with optional category filtering. Returns product catalog with IDs, names, prices, and stock levels. Use this to browse products or find product_id for get_product_details tool."
  parameters:
    - name: category
      type: string
      description: "Filter by product category. Valid values: 'electronics', 'clothing', 'food', 'books', 'home'. Omit to see all categories."
      required: false
      examples: ["electronics", "clothing"]
    - name: in_stock_only
      type: boolean
      description: "If true, only return products currently in stock. Default: false (shows all products)."
      default: false
  return:
    type: array
    description: "Array of product objects sorted by name"
    items:
      type: object
      properties:
        product_id:
          type: string
          description: "Unique product identifier (use with get_product_details)"
        name:
          type: string
          description: "Product name"
        category:
          type: string
          description: "Product category"
        price:
          type: number
          description: "Current price in USD"
        stock:
          type: integer
          description: "Current stock level (0 = out of stock)"
  source:
    code: |
      SELECT
        product_id,
        name,
        category,
        price,
        stock
      FROM products
      WHERE ($category IS NULL OR category = $category)
        AND ($in_stock_only = false OR stock > 0)
      ORDER BY name
```

```yaml
# tools/get_product_details.yml
mxcp: 1
tool:
  name: get_product_details
  description: "Get detailed information for a specific product including full description, specifications, reviews, and related products. Use product_id from list_products tool."
  parameters:
    - name: product_id
      type: string
      description: "Product identifier from list_products (e.g., 'PROD_12345')"
      required: true
      examples: ["PROD_12345"]
  return:
    type: object
    description: "Complete product information"
    properties:
      product_id: { type: string, description: "Product identifier" }
      name: { type: string, description: "Product name" }
      description: { type: string, description: "Detailed product description" }
      price: { type: number, description: "Current price in USD" }
      stock: { type: integer, description: "Available quantity" }
      specifications: { type: object, description: "Product specs (varies by category)" }
      avg_rating: { type: number, description: "Average customer rating (0-5)" }
      review_count: { type: integer, description: "Number of customer reviews" }
      related_products: { type: array, description: "Product IDs of related items" }
  source:
    code: |
      SELECT * FROM product_details WHERE product_id = $product_id
```

## Documentation Quality Checklist

Before declaring a tool complete, verify:

### Tool Level:
- [ ] Description explains WHAT it does
- [ ] Description explains WHAT it returns
- [ ] Description explains WHEN to use it
- [ ] Cross-references to related tools (if applicable)
- [ ] Use cases are clear

### Parameter Level:
- [ ] Every parameter has a description
- [ ] Valid values/formats are documented
- [ ] Examples provided for complex parameters
- [ ] Required vs optional is clear
- [ ] Defaults documented (if optional)

### Return Type Level:
- [ ] Return type structure is documented
- [ ] Every field has a description
- [ ] Complex nested objects are explained
- [ ] Array item types are described

### Overall:
- [ ] An LLM reading this can use the tool WITHOUT human explanation
- [ ] An LLM knows WHEN to call this vs other tools
- [ ] An LLM knows HOW to get required parameters
- [ ] An LLM knows WHAT to expect in the response

## Common Documentation Mistakes

### ❌ MISTAKE 1: Vague Descriptions
```yaml
description: "Gets user info"  # ❌ Which user? What info? When?
```
✅ **FIX**:
```yaml
description: "Retrieve complete user profile including contact information, account status, and preferences for a specific user. Use user_id from list_users or search_users tools."
```

### ❌ MISTAKE 2: Missing Parameter Details
```yaml
parameters:
  - name: status
    type: string  # ❌ What are valid values?
```
✅ **FIX**:
```yaml
parameters:
  - name: status
    type: string
    description: "Order status filter. Valid values: 'pending', 'processing', 'shipped', 'delivered', 'cancelled'"
    examples: ["pending", "shipped"]
```

### ❌ MISTAKE 3: Undocumented Return Fields
```yaml
return:
  type: object
  properties:
    total: { type: number }  # ❌ Total what? In what units?
```
✅ **FIX**:
```yaml
return:
  type: object
  properties:
    total: { type: number, description: "Total order amount in USD including tax and shipping" }
```

### ❌ MISTAKE 4: No Cross-References
```yaml
tool:
  name: get_order_details
  parameters:
    - name: order_id
      type: string  # ❌ Where does LLM get this?
```
✅ **FIX**:
```yaml
tool:
  name: get_order_details
  description: "Get detailed order information. Use order_id from list_orders or search_orders tools."
  parameters:
    - name: order_id
      type: string
      description: "Order identifier (format: ORD_XXXXXX) from list_orders or search_orders"
```

### ❌ MISTAKE 5: Technical Jargon Without Explanation
```yaml
description: "Executes SOQL query on SF objects"  # ❌ LLM doesn't know SOQL or SF
```
✅ **FIX**:
```yaml
description: "Query Salesforce data using filters. Searches across accounts, contacts, and opportunities. Returns matching records with standard fields."
```

## Testing Documentation Quality

**Ask yourself**: "If I gave this to an LLM with ZERO context about my domain, could it use this tool correctly?"

**Test by asking**:
1. When should this tool be called?
2. What parameters are needed and where do I get them?
3. What will I get back?
4. How does this relate to other tools?

If you can't answer clearly from the YAML alone, **the documentation is insufficient.**

## Response Format Best Practices

**Design tool outputs to optimize LLM context usage.**

### Provide Detail Level Options

Allow LLMs to request different levels of detail based on their needs.

```yaml
tool:
  name: search_products
  parameters:
    - name: query
      type: string
      description: "Product search query"
    - name: detail_level
      type: string
      description: "Level of detail in response"
      enum: ["minimal", "standard", "full"]
      default: "standard"
      examples:
        - "minimal: Only ID, name, price (fastest, least context)"
        - "standard: Basic info + category + stock"
        - "full: All fields including descriptions and specifications"
```

**Implementation in SQL**:
```sql
SELECT
  CASE $detail_level
    WHEN 'minimal' THEN json_object('id', id, 'name', name, 'price', price)
    WHEN 'standard' THEN json_object('id', id, 'name', name, 'price', price, 'category', category, 'in_stock', stock > 0)
    ELSE json_object('id', id, 'name', name, 'price', price, 'category', category, 'stock', stock, 'description', description, 'specs', specs)
  END as product
FROM products
WHERE name LIKE '%' || $query || '%'
```

### Use Human-Readable Formats

**Return data in formats LLMs can easily understand and communicate to users.**

#### ✅ Good: Human-Readable
```yaml
return:
  type: object
  properties:
    customer_id: { type: string, description: "Customer ID (CUST_12345)" }
    customer_name: { type: string, description: "Display name" }
    last_order_date: { type: string, description: "Date in YYYY-MM-DD format" }
    total_spent: { type: number, description: "Total amount in USD" }
    status: { type: string, description: "Account status: active, inactive, suspended" }
```

**SQL implementation**:
```sql
SELECT
  customer_id,
  name as customer_name,
  DATE_FORMAT(last_order_date, '%Y-%m-%d') as last_order_date,  -- Not epoch timestamp
  ROUND(total_spent, 2) as total_spent,
  status
FROM customers
```

#### ❌ Bad: Opaque/Technical
```yaml
return:
  type: object
  properties:
    cust_id: { type: integer }              # Unclear name
    ts: { type: integer }                   # Epoch timestamp - not human readable
    amt: { type: number }                   # Unclear abbreviation
    stat_cd: { type: integer }              # Status code instead of name
```

### Include Display Names with IDs

When returning IDs, also return human-readable names.

```yaml
return:
  type: object
  properties:
    assigned_to_user_id: { type: string, description: "User ID" }
    assigned_to_name: { type: string, description: "User display name" }
    category_id: { type: string, description: "Category ID" }
    category_name: { type: string, description: "Category name" }
```

**Why**: LLM can understand relationships without additional tool calls.

### Limit Response Size

**Prevent overwhelming LLMs with too much data.**

```yaml
tool:
  name: list_transactions
  parameters:
    - name: limit
      type: integer
      description: "Maximum number of transactions to return (1-1000)"
      default: 100
      minimum: 1
      maximum: 1000
```

**Python implementation with truncation**:
```python
def list_transactions(limit: int = 100) -> dict:
    """List recent transactions with size limits"""

    if limit > 1000:
        return {
            "success": False,
            "error": f"Limit of {limit} exceeds maximum (1000). Use date filters to narrow results.",
            "error_code": "LIMIT_EXCEEDED",
            "suggestion": "Try adding 'start_date' and 'end_date' parameters"
        }

    results = db.execute(
        "SELECT * FROM transactions ORDER BY date DESC LIMIT $limit",
        {"limit": limit}
    )

    return {
        "success": True,
        "count": len(results),
        "limit": limit,
        "has_more": len(results) == limit,
        "transactions": results,
        "note": "Use pagination or filters if more results needed"
    }
```

### Provide Pagination Metadata

**Help LLMs understand when more data is available.**

```yaml
return:
  type: object
  properties:
    items: { type: array, description: "Results for this page" }
    total_count: { type: integer, description: "Total matching results" }
    returned_count: { type: integer, description: "Number returned in this response" }
    has_more: { type: boolean, description: "Whether more results are available" }
    next_offset: { type: integer, description: "Offset for next page" }
```

**SQL implementation**:
```sql
-- Get total count
WITH total AS (
  SELECT COUNT(*) as count FROM products WHERE category = $category
)
SELECT
  json_object(
    'items', (SELECT json_group_array(json_object('id', id, 'name', name))
              FROM products WHERE category = $category LIMIT $limit OFFSET $offset),
    'total_count', (SELECT count FROM total),
    'returned_count', MIN($limit, (SELECT count FROM total) - $offset),
    'has_more', (SELECT count FROM total) > ($offset + $limit),
    'next_offset', $offset + $limit
  ) as result
```

### Format for Readability

**Use clear field names and consistent structures.**

#### ✅ Good: Clear Structure
```yaml
return:
  type: object
  properties:
    summary:
      type: object
      description: "High-level summary"
      properties:
        total_orders: { type: integer }
        total_revenue: { type: number }
        average_order_value: { type: number }
    top_products:
      type: array
      description: "Top 5 selling products"
      items:
        type: object
        properties:
          product_name: { type: string }
          units_sold: { type: integer }
          revenue: { type: number }
```

#### ❌ Bad: Flat Unstructured
```yaml
return:
  type: object
  properties:
    total_orders: { type: integer }
    total_revenue: { type: number }
    product1_name: { type: string }
    product1_units: { type: integer }
    product2_name: { type: string }
    # ...repeated pattern
```

### Omit Verbose Metadata

**Don't return internal/technical metadata that doesn't help LLMs.**

```yaml
# ✅ GOOD: Essential information only
return:
  type: object
  properties:
    user_id: { type: string }
    name: { type: string }
    email: { type: string }
    profile_image: { type: string, description: "Profile image URL" }

# ❌ BAD: Too much metadata
return:
  type: object
  properties:
    user_id: { type: string }
    name: { type: string }
    email: { type: string }
    profile_image_small: { type: string }
    profile_image_medium: { type: string }
    profile_image_large: { type: string }
    profile_image_xlarge: { type: string }
    internal_db_id: { type: integer }
    created_timestamp_unix: { type: integer }
    modified_timestamp_unix: { type: integer }
    schema_version: { type: integer }
```

**Principle**: Include one best representation, not all variations.

## Summary

**Every tool must be self-documenting**:
- ✅ Clear, detailed descriptions
- ✅ Documented parameters with examples
- ✅ Documented return types
- ✅ Cross-references to related tools
- ✅ Valid values and formats
- ✅ Use cases explained

**Response format best practices**:
- ✅ Provide detail level options (minimal/standard/full)
- ✅ Use human-readable formats (dates, names, not codes)
- ✅ Include display names alongside IDs
- ✅ Limit response sizes with clear guidance
- ✅ Provide pagination metadata
- ✅ Structure data clearly
- ✅ Omit verbose internal metadata

**Remember**: The LLM has NO prior knowledge. Your descriptions are its ONLY guide.
