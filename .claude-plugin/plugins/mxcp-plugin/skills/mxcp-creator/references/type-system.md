# Type System Reference

Complete reference for MXCP type validation.

## Basic Types

### String

```yaml
parameters:
  - name: text
    type: string
    description: "Text input"
    minLength: 1
    maxLength: 1000
    pattern: "^[a-zA-Z0-9]+$"
    examples: ["hello", "world123"]
```

### Number

```yaml
parameters:
  - name: price
    type: number
    description: "Price value"
    minimum: 0
    maximum: 1000000
    examples: [99.99, 149.50]
```

### Integer

```yaml
parameters:
  - name: count
    type: integer
    description: "Item count"
    minimum: 1
    maximum: 100
    examples: [5, 10, 25]
```

### Boolean

```yaml
parameters:
  - name: active
    type: boolean
    description: "Active status"
    default: true
    examples: [true, false]
```

### Null

```yaml
parameters:
  - name: optional_value
    type: "null"
    description: "Can be null"
```

## Complex Types

### Array

```yaml
parameters:
  - name: tags
    type: array
    items:
      type: string
    description: "List of tags"
    minItems: 1
    maxItems: 10
    examples: [["tag1", "tag2"]]
```

### Object

```yaml
return:
  type: object
  properties:
    id:
      type: string
      description: "User ID"
    name:
      type: string
      description: "User name"
    age:
      type: integer
      minimum: 0
  required: ["id", "name"]
```

### Nested Structures

```yaml
return:
  type: object
  properties:
    user:
      type: object
      properties:
        id: { type: string }
        profile:
          type: object
          properties:
            name: { type: string }
            email: { type: string, format: email }
    orders:
      type: array
      items:
        type: object
        properties:
          order_id: { type: string }
          amount: { type: number }
```

## Format Annotations

### String Formats

```yaml
parameters:
  - name: email
    type: string
    format: email
    examples: ["user@example.com"]
  
  - name: date
    type: string
    format: date
    examples: ["2024-01-15"]
  
  - name: datetime
    type: string
    format: date-time
    examples: ["2024-01-15T10:30:00Z"]
  
  - name: uri
    type: string
    format: uri
    examples: ["https://example.com"]
  
  - name: uuid
    type: string
    format: uuid
    examples: ["123e4567-e89b-12d3-a456-426614174000"]
```

## Enums

### String Enum

```yaml
parameters:
  - name: status
    type: string
    enum: ["active", "pending", "inactive"]
    description: "Account status"
```

### Number Enum

```yaml
parameters:
  - name: priority
    type: integer
    enum: [1, 2, 3, 4, 5]
    description: "Priority level (1-5)"
```

## Optional Parameters

```yaml
parameters:
  - name: required_param
    type: string
    description: "This is required"
  
  - name: optional_param
    type: string
    description: "This is optional"
    default: "default_value"
```

## Validation Rules

### String Constraints

```yaml
parameters:
  - name: username
    type: string
    minLength: 3
    maxLength: 20
    pattern: "^[a-zA-Z0-9_]+$"
    description: "3-20 chars, alphanumeric and underscore only"
```

### Number Constraints

```yaml
parameters:
  - name: price
    type: number
    minimum: 0.01
    maximum: 999999.99
    multipleOf: 0.01
    description: "Price with 2 decimal places"
```

### Array Constraints

```yaml
parameters:
  - name: items
    type: array
    items:
      type: string
    minItems: 1
    maxItems: 100
    uniqueItems: true
    description: "1-100 unique items"
```

## Return Type Examples

### Simple Return

```yaml
return:
  type: string
  description: "Success message"
```

### Object Return

```yaml
return:
  type: object
  properties:
    success: { type: boolean }
    message: { type: string }
    data:
      type: object
      properties:
        id: { type: string }
        value: { type: number }
```

### Array Return

```yaml
return:
  type: array
  items:
    type: object
    properties:
      id: { type: string }
      name: { type: string }
      created_at: { type: string, format: date-time }
```

## Sensitive Data Marking

```yaml
return:
  type: object
  properties:
    public_info: { type: string }
    ssn:
      type: string
      sensitive: true  # Marked as sensitive
    salary:
      type: number
      sensitive: true
```

## Union Types (anyOf)

```yaml
return:
  anyOf:
    - type: object
      properties:
        success: { type: boolean }
        data: { type: object }
    - type: object
      properties:
        error: { type: string }
        code: { type: integer }
```

## Validation in Practice

### Parameter Validation

MXCP validates parameters before execution:

```yaml
tool:
  name: create_user
  parameters:
    - name: email
      type: string
      format: email
    - name: age
      type: integer
      minimum: 18
    - name: role
      type: string
      enum: ["user", "admin"]
```

Invalid calls will be rejected:
```bash
# ✗ Invalid email format
mxcp run tool create_user --param email=invalid

# ✗ Age below minimum
mxcp run tool create_user --param age=15

# ✗ Invalid enum value
mxcp run tool create_user --param role=superadmin

# ✓ Valid
mxcp run tool create_user \
  --param email=user@example.com \
  --param age=25 \
  --param role=user
```

### Return Validation

MXCP validates returns match schema (can be disabled with `--skip-output-validation`):

```python
def get_user(user_id: str) -> dict:
    # Must return object matching return type
    return {
        "id": user_id,
        "name": "John Doe",
        "email": "john@example.com"
    }
```

## Best Practices

1. **Always define types** - Enables validation and documentation
2. **Use format annotations** - Provides additional validation
3. **Add examples** - Helps LLMs understand usage
4. **Set constraints** - Prevent invalid input
5. **Mark sensitive data** - Enables policy filtering
6. **Document types** - Add descriptions everywhere
7. **Use enums** - Constrain to valid values
8. **Test validation** - Include invalid inputs in tests
