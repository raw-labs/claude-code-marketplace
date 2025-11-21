# CLI Reference

Quick reference for MXCP command-line interface.

## Core Commands

### mxcp init

Initialize new MXCP project.

```bash
mxcp init                    # Current directory
mxcp init my-project         # New directory
mxcp init --bootstrap        # With examples
mxcp init --project=myapp --profile=dev
```

### mxcp serve

Start MCP server.

```bash
mxcp serve                   # Use config defaults
mxcp serve --transport stdio # For Claude Desktop
mxcp serve --transport http --port 8080
mxcp serve --profile production
mxcp serve --sql-tools true  # Enable SQL query tools
mxcp serve --readonly        # Read-only database
mxcp serve --stateless       # For serverless deployment
mxcp serve --debug           # Debug mode
```

### mxcp list

List available endpoints.

```bash
mxcp list                    # All endpoints
mxcp list --json-output      # JSON format
mxcp list --profile prod     # Specific profile
```

### mxcp run

Execute endpoint.

```bash
# Tools
mxcp run tool my_tool --param name=value

# Resources
mxcp run resource my_resource --param id=123

# Prompts
mxcp run prompt my_prompt --param text="hello"

# Complex parameters from JSON file
mxcp run tool analyze --param data=@input.json

# With user context
mxcp run tool secure_data --user-context '{"role": "admin"}'

# Read-only mode
mxcp run tool query_data --readonly
```

## Quality Commands

### mxcp validate

Check structure and types.

```bash
mxcp validate                # All endpoints
mxcp validate my_tool        # Specific endpoint
mxcp validate --json-output  # JSON format
mxcp validate --readonly     # Read-only database
```

### mxcp test

Run endpoint tests.

```bash
mxcp test                    # All tests
mxcp test tool my_tool       # Specific endpoint
mxcp test --user-context '{"role": "admin"}'
mxcp test --user-context @user.json
mxcp test --json-output
mxcp test --readonly
```

### mxcp lint

Check metadata quality.

```bash
mxcp lint                    # All endpoints
mxcp lint --severity warning # Warnings only
mxcp lint --severity info    # All issues
mxcp lint --json-output
```

### mxcp evals

Test LLM behavior.

```bash
mxcp evals                   # All eval suites
mxcp evals safety_checks     # Specific suite
mxcp evals --model gpt-4o    # Override model
mxcp evals --user-context '{"role": "user"}'
mxcp evals --json-output
```

## Data Commands

### mxcp query

Execute SQL directly.

```bash
mxcp query "SELECT * FROM users"
mxcp query "SELECT * FROM sales WHERE region = $region" --param region=US
mxcp query --file query.sql
mxcp query --file query.sql --param date=@dates.json
mxcp query "SELECT COUNT(*) FROM data" --json-output
mxcp query "SELECT * FROM users" --readonly
```

### mxcp dbt

Run dbt commands.

```bash
mxcp dbt run                 # Run all models
mxcp dbt run --select model
mxcp dbt test                # Run tests
mxcp dbt docs generate       # Generate docs
mxcp dbt-config             # Generate dbt config
mxcp dbt-config --dry-run   # Preview config
```

### mxcp drift-snapshot

Create baseline snapshot.

```bash
mxcp drift-snapshot          # Default profile
mxcp drift-snapshot --profile prod
mxcp drift-snapshot --force  # Overwrite existing
mxcp drift-snapshot --dry-run
```

### mxcp drift-check

Check for changes.

```bash
mxcp drift-check             # Use default baseline
mxcp drift-check --baseline path/to/snapshot.json
mxcp drift-check --profile prod
mxcp drift-check --json-output
mxcp drift-check --readonly
```

## Monitoring Commands

### mxcp log

Query audit logs.

```bash
# Basic queries
mxcp log                     # Recent logs
mxcp log --since 1h          # Last hour
mxcp log --since 2d          # Last 2 days

# Filtering
mxcp log --tool my_tool      # Specific tool
mxcp log --resource my_resource
mxcp log --prompt my_prompt
mxcp log --type tool         # By type
mxcp log --status error      # Errors only
mxcp log --status success    # Successes only
mxcp log --policy deny       # Denied by policy

# Output
mxcp log --limit 50          # Limit results
mxcp log --json              # JSON format
mxcp log --export-csv audit.csv
mxcp log --export-duckdb audit.db

# Combined filters
mxcp log --since 1d --tool my_tool --status error
```

### mxcp log-cleanup

Apply retention policies.

```bash
mxcp log-cleanup             # Apply retention
mxcp log-cleanup --dry-run   # Preview deletions
mxcp log-cleanup --profile prod
mxcp log-cleanup --json
```

## Common Options

Available for most commands:

```bash
--profile PROFILE            # Use specific profile
--json-output                # Output as JSON
--debug                      # Debug logging
--readonly                   # Read-only database access
```

## Environment Variables

```bash
# Config location (use project-local config)
export MXCP_CONFIG=./config.yml
# Or for global config (user manually copies)
# export MXCP_CONFIG=~/.mxcp/config.yml

# Default profile
export MXCP_PROFILE=production

# Debug mode
export MXCP_DEBUG=1

# Read-only mode
export MXCP_READONLY=1

# Override database path
export MXCP_DUCKDB_PATH=/path/to/custom.duckdb

# Disable analytics
export MXCP_DISABLE_ANALYTICS=1
```

## Time Formats

For `--since` option:

```bash
10s   # 10 seconds
5m    # 5 minutes
2h    # 2 hours
1d    # 1 day
3w    # 3 weeks
```

## Exit Codes

- `0` - Success
- `1` - Error or validation failure
- `2` - Invalid arguments

## Configuration Options

### Project Structure Enforcement

**CRITICAL**: MXCP enforces organized directory structure. Files in wrong locations are **ignored**.

Required structure:
- Tools: `tools/*.yml`
- Resources: `resources/*.yml`
- Prompts: `prompts/*.yml`
- Python: `python/*.py`
- SQL: `sql/*.sql`

Use `mxcp init --bootstrap` to create proper structure.

### Profile Configuration (mxcp-site.yml)

```yaml
mxcp: 1
project: my-project

# Generic SQL tools for database exploration (optional)
sql_tools:
  enabled: true

profiles:
  default:
    database:
      path: data.duckdb

  production:
    # Authentication
    auth:
      provider: github
      # OAuth config in project config.yml

    # Audit logging
    audit:
      enabled: true
      path: audit/logs.jsonl
      retention_days: 90

    # OpenTelemetry observability
    telemetry:
      enabled: true
      endpoint: "http://otel-collector:4318"

    # Policy enforcement
    policies:
      strict_mode: true

    # Database
    database:
      path: /app/data/production.duckdb
```

### Configuration Details

**Telemetry (OpenTelemetry)**:
```yaml
profiles:
  production:
    telemetry:
      enabled: true
      endpoint: "http://localhost:4318"  # OTLP endpoint
      # Optional: service name
      service_name: "my-mxcp-server"
```

Provides:
- Distributed tracing for requests
- Performance metrics
- Integration with Jaeger, Grafana, etc.

**Stateless Mode** (`--stateless` flag):
- For Claude.ai and serverless deployments
- Disables state that persists across requests
- Use for horizontal scaling

**SQL Tools**:

Generic SQL tools provide built-in database exploration capabilities for LLMs:
- **`list_tables`** - View all available tables
- **`get_table_schema`** - Examine table structure and columns
- **`execute_sql_query`** - Run custom SQL queries

Enable via config file (recommended):
```yaml
# mxcp-site.yml
sql_tools:
  enabled: true
```

Or via command-line flag:
```bash
mxcp serve --sql-tools true   # Enable
mxcp serve --sql-tools false  # Disable (default)
```

**Use cases:**
- Natural language data exploration
- Ad-hoc analysis and discovery
- Prototyping query patterns
- Working with dbt-transformed data

**Security:** Generic SQL tools allow arbitrary SQL execution. Use read-only database connections and consider policy-based restrictions for production deployments.

**Example:** See `assets/project-templates/covid_owid/` for complete implementation.

## Common Workflows

### Development

```bash
# Initialize with proper directory structure
mxcp init --bootstrap

# Validate structure
mxcp validate

# Test functionality
mxcp test

# Check documentation
mxcp lint

# Run locally with debug
mxcp serve --debug
```

### Deployment

```bash
# Create snapshot
mxcp drift-snapshot --profile prod

# Run tests
mxcp test --profile prod

# Run evals
mxcp evals --profile prod

# Deploy
mxcp serve --profile prod
```

### Monitoring

```bash
# Check drift
mxcp drift-check --profile prod

# View recent errors
mxcp log --since 1h --status error

# Export audit trail
mxcp log --since 7d --export-duckdb audit.db

# Clean old logs
mxcp log-cleanup
```

## Tips

1. **Use --debug** for troubleshooting
2. **Test locally** before deployment
3. **Use profiles** for different environments
4. **Export logs** for analysis
5. **Run drift checks** in CI/CD
6. **Validate before committing**
7. **Use --readonly** for query tools
