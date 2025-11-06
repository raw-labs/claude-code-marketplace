# Policy Enforcement Reference

Comprehensive guide to MXCP policy system.

## Policy Types

### Input Policies

Control access before execution:

```yaml
policies:
  input:
    - condition: "!('hr.read' in user.permissions)"
      action: deny
      reason: "Missing HR read permission"
    
    - condition: "user.role == 'guest'"
      action: deny
      reason: "Guests cannot access this endpoint"
```

### Output Policies

Filter or mask data in responses:

```yaml
policies:
  output:
    - condition: "user.role != 'admin'"
      action: filter_fields
      fields: ["salary", "ssn", "bank_account"]
      reason: "Sensitive data restricted"
    
    - condition: "user.department != 'finance'"
      action: mask_fields
      fields: ["revenue", "profit"]
      mask: "***"
```

## Policy Actions

### deny

Block execution completely:

```yaml
- condition: "!('data.read' in user.permissions)"
  action: deny
  reason: "Insufficient permissions"
```

### filter_fields

Remove fields from output:

```yaml
- condition: "user.role != 'hr_manager'"
  action: filter_fields
  fields: ["salary", "ssn"]
```

### mask_fields

Replace field values with mask:

```yaml
- condition: "user.clearance_level < 5"
  action: mask_fields
  fields: ["classified_info"]
  mask: "[REDACTED]"
```

### warn

Log warning but allow execution:

```yaml
- condition: "user.department != 'sales'"
  action: warn
  reason: "Cross-department access"
```

## CEL Expressions

Policy conditions use Common Expression Language (CEL):

### User Context Fields

```yaml
# Check role
condition: "user.role == 'admin'"

# Check permissions (array)
condition: "'hr.read' in user.permissions"

# Check department
condition: "user.department == 'engineering'"

# Check custom fields
condition: "user.clearance_level >= 3"
```

### Operators

```yaml
# Equality
condition: "user.role == 'admin'"

# Inequality
condition: "user.role != 'guest'"

# Logical AND
condition: "user.role == 'manager' && user.department == 'sales'"

# Logical OR
condition: "user.role == 'admin' || user.role == 'owner'"

# Negation
condition: "!(user.role == 'guest')"

# Array membership
condition: "'read:all' in user.permissions"

# Comparison
condition: "user.access_level >= 3"
```

## Real-World Examples

### HR Data Access

```yaml
tool:
  name: employee_data
  policies:
    input:
      # Only HR can access
      - condition: "user.department != 'hr'"
        action: deny
        reason: "HR department only"
    output:
      # Only managers see salaries
      - condition: "user.role != 'manager'"
        action: filter_fields
        fields: ["salary", "bonus"]
      # Only HR managers see SSN
      - condition: "!(user.role == 'hr_manager')"
        action: filter_fields
        fields: ["ssn"]
```

### Customer Data

```yaml
tool:
  name: customer_info
  policies:
    input:
      # Users can only see their own data
      - condition: "user.role != 'support' && $customer_id != user.customer_id"
        action: deny
        reason: "Can only access own data"
    output:
      # Mask payment info for non-finance
      - condition: "user.department != 'finance'"
        action: mask_fields
        fields: ["credit_card", "bank_account"]
        mask: "****"
```

### Financial Reports

```yaml
tool:
  name: financial_report
  policies:
    input:
      # Require finance permission
      - condition: "!('finance.read' in user.permissions)"
        action: deny
        reason: "Finance permission required"
      
      # Warn on external access
      - condition: "!user.internal_network"
        action: warn
        reason: "External access to financial data"
    
    output:
      # Directors see everything
      - condition: "user.role == 'director'"
        action: allow
      
      # Managers see summary only
      - condition: "user.role == 'manager'"
        action: filter_fields
        fields: ["detailed_transactions", "employee_costs"]
```

## Testing Policies

### In Tests

```yaml
tests:
  - name: "admin_full_access"
    user_context:
      role: admin
      permissions: ["read:all"]
    result_contains:
      salary: 75000
  
  - name: "user_filtered"
    user_context:
      role: user
    result_not_contains: ["salary", "ssn"]
```

### CLI Testing

```bash
# Test as admin
mxcp run tool employee_data \
  --param employee_id=123 \
  --user-context '{"role": "admin"}'

# Test as regular user
mxcp run tool employee_data \
  --param employee_id=123 \
  --user-context '{"role": "user"}'
```

## Best Practices

1. **Deny by Default**: Start restrictive, add exceptions
2. **Clear Reasons**: Always provide reason for debugging
3. **Test All Paths**: Test with different user contexts
4. **Layer Policies**: Use both input and output policies
5. **Document Permissions**: List required permissions in description
6. **Audit Policy Hits**: Enable audit logging to track policy decisions
