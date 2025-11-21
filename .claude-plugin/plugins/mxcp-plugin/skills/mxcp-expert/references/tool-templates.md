# Tool Templates

Copy these templates to avoid syntax errors when creating MXCP tools.

## Python Tool Template

**Use this template for Python-based tools** that require custom logic, API calls, or complex processing.

```yaml
mxcp: 1
tool:
  name: YOUR_TOOL_NAME
  description: |
    Clear description of what this tool does and when to use it.
    Explain the purpose and expected behavior.
  language: python
  parameters:
    # Required parameter (no default)
    - name: required_param
      type: string
      description: "What this parameter is for"

    # Optional parameter (with null default)
    - name: optional_param
      type: string
      description: "What this optional parameter is for"
      default: null

    # Optional parameter (with specific default)
    - name: limit
      type: integer
      description: "Maximum number of results"
      default: 100
  return:
    type: object
    description: "Description of what gets returned"
    properties:
      status: { type: string, description: "Operation status" }
      data: { type: array, description: "Result data" }
  source:
    file: ../python/your_module.py
  tests:
    - name: "basic_test"
      arguments:
        - key: required_param
          value: "test_value"
      result:
        status: "success"
```

**After copying this template:**
1. Replace `YOUR_TOOL_NAME` with the actual tool name
2. Update the `description` to explain what the tool does
3. Update the `parameters` section with actual parameters
4. Update the `return` type to match expected output
5. Update the `source.file` path to point to Python module
6. 🛑 **RUN `mxcp validate` IMMEDIATELY** 🛑

## SQL Tool Template

**Use this template for SQL-based tools** that query databases directly.

```yaml
mxcp: 1
tool:
  name: YOUR_TOOL_NAME
  description: |
    Clear description of what this SQL query does.
  parameters:
    - name: filter_value
      type: string
      description: "Filter criteria (optional)"
      default: null
  return:
    type: array
    items:
      type: object
      properties:
        id: { type: integer }
        name: { type: string }
  source:
    code: |
      SELECT
        id,
        name,
        other_column
      FROM your_table
      WHERE $filter_value IS NULL OR column = $filter_value
      ORDER BY id
      LIMIT 100
  tests:
    - name: "test_query"
      arguments: []
      # Add expected results if known
```

**After copying this template:**
1. Replace `YOUR_TOOL_NAME` with the actual tool name
2. Update the SQL query in `source.code` with actual table/columns
3. Update `parameters` section with query parameters
4. Update `return` types to match query output
5. 🛑 **RUN `mxcp validate` IMMEDIATELY** 🛑

## Resource Template

**Use this template for MCP resources** that provide static or dynamic data.

```yaml
mxcp: 1
resource:
  name: YOUR_RESOURCE_NAME
  uri: "resource://namespace/YOUR_RESOURCE_NAME"
  description: |
    Clear description of what this resource provides.
  mimeType: "application/json"
  source:
    code: |
      SELECT
        *
      FROM your_table
      LIMIT 100
```

## Prompt Template

**Use this template for MCP prompts** that provide LLM instructions.

```yaml
mxcp: 1
prompt:
  name: YOUR_PROMPT_NAME
  description: |
    Clear description of what this prompt helps with.
  arguments:
    - name: context_param
      description: "Context information for the prompt"
      required: true
  messages:
    - role: user
      content: |
        Use the following context to help answer questions:
        {{ context_param }}

        Please provide detailed and accurate responses.
```

## Validation Checklist

After creating any tool from a template:

- [ ] Tool name follows naming conventions (lowercase, underscores)
- [ ] Description is clear and LLM-friendly (explains what, when, why)
- [ ] All parameters have descriptions
- [ ] Return types are specified completely
- [ ] Tests are included in the tool definition
- [ ] `mxcp validate` passes without errors
- [ ] `mxcp test` passes for the tool
- [ ] Manual test with `mxcp run tool <name>` succeeds

## Common Template Mistakes

1. **Missing `tool:` wrapper** - Always include `tool:` as top-level key after `mxcp: 1`
2. **Using `type: python`** - Use `language: python` for Python tools, not `type:`
3. **Adding `required: true`** - Don't use `required:` field, use `default:` for optional params
4. **Empty return types** - Always specify complete return types
5. **No tests** - Always include at least one test case

## See Also

- **references/minimal-working-examples.md** - Complete working examples
- **references/endpoint-patterns.md** - Advanced tool patterns
- **SKILL.md** - Main skill guide with workflows
