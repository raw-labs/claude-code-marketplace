# MXCP Expert Claude Skill

A comprehensive Claude skill for working with MXCP (Enterprise MCP Framework) - enabling you to build production-ready MCP servers with SQL and Python endpoints, complete with security, audit trails, and policy enforcement.

## What's Included

This skill provides complete guidance for:

- **Creating MXCP projects** - Initialize and structure production-ready MCP servers
- **Endpoint development** - Build tools, resources, and prompts using SQL or Python
- **Enterprise features** - Implement authentication, policies, and audit logging
- **dbt integration** - Combine data transformation with MCP endpoints
- **Quality assurance** - Validate, test, lint, and evaluate your endpoints
- **Production deployment** - Monitor drift, track operations, and ensure security

## Installation

1. Download the `mxcp-expert.zip` file
2. In Claude Desktop, go to Settings → Developer → Custom Skills
3. Click "Add Skill" and upload the `mxcp-expert.zip` file
4. The skill will be automatically available when working on MXCP projects

## Skill Structure

```
mxcp-expert/
├── SKILL.md                                # Main skill file with quick reference
├── assets/                                 # Project templates and resources
│   ├── project-templates/                  # Pre-built MXCP projects
│   │   ├── google-calendar/                # OAuth integration examples
│   │   ├── jira/ jira-oauth/               # Jira integrations
│   │   ├── salesforce/ salesforce-oauth/   # Salesforce integrations
│   │   ├── confluence/                     # Confluence integration
│   │   ├── python-demo/                    # Python endpoint patterns
│   │   ├── covid_owid/                     # dbt data caching example
│   │   ├── keycloak/                       # SSO integration
│   │   └── ...                             # More templates
│   └── schemas/                            # JSON Schema definitions for YAML validation
│       ├── mxcp-site-schema-1.json         # mxcp-site.yml validation
│       ├── mxcp-config-schema-1.json       # config.yml validation
│       ├── tool-schema-1.json              # Tool definition validation
│       ├── resource-schema-1.json          # Resource definition validation
│       ├── prompt-schema-1.json            # Prompt definition validation
│       ├── eval-schema-1.json              # Evaluation suite validation
│       └── common-types-schema-1.json      # Common type definitions
├── scripts/                                # Utility scripts
│   └── validate_yaml.py                    # YAML validation script
└── references/                             # Detailed documentation (23 files)
    ├── tool-templates.md                   # Ready-to-use YAML templates for tools/resources/prompts
    ├── project-selection-guide.md          # Decision tree and template selection
    ├── dbt-core-guide.md                   # Essential dbt knowledge (seeds, models, Python models)
    ├── duckdb-essentials.md                # DuckDB features and SQL extensions
    ├── endpoint-patterns.md                # Complete endpoint examples
    ├── python-api.md                       # Python runtime API reference
    ├── policies.md                         # Policy enforcement guide
    ├── comprehensive-testing-guide.md      # Complete testing strategies
    ├── debugging-guide.md                  # Systematic debugging workflows
    ├── error-handling-guide.md             # Python error handling patterns
    ├── dbt-patterns.md                     # Advanced dbt integration patterns
    ├── database-connections.md             # PostgreSQL, MySQL, SQLite, SQL Server
    ├── excel-integration.md                # Excel file handling with pandas and dbt
    ├── claude-desktop.md                   # Claude Desktop setup guide
    ├── cli-reference.md                    # Complete CLI documentation
    ├── type-system.md                      # Type validation reference
    └── ...                                 # 8 more specialized guides
```

## When This Skill is Used

Claude will automatically use this skill when you:

- Ask to create or work with MXCP projects
- Define MCP tools, resources, or prompts
- Implement SQL queries or Python endpoints
- Configure authentication, policies, or audit logging
- Set up dbt integration
- Test, validate, or debug MXCP endpoints
- Deploy MXCP servers to production

## Quick Start Examples

### Example 1: CSV File to MCP Server

```
User: "I need to connect my chat to a CSV file with customer data"

Claude: [Uses mxcp-expert skill]
I'll help you create an MXCP server that queries your CSV file.

1. Initialize project:
   mkdir customer-mcp && cd customer-mcp
   mxcp init --bootstrap

2. Add your CSV as a dbt seed:
   cp customers.csv seeds/

3. Create schema definition (seeds/schema.yml):
   [Creates proper schema.yml with column types and tests]

4. Load data:
   dbt seed
   dbt test

5. Create query tool:
   [Creates tools/get_customers.yml with parameterized SQL]

6. Test and validate:
   mxcp validate && mxcp test
   mxcp serve

[Provides complete security-first implementation with validation]
```

### Example 2: API Integration

```
User: "Connect to Google Calendar API"

Claude: [Uses mxcp-expert skill]
I'll use the google-calendar project template for OAuth integration.

1. Copy template:
   cp -r assets/project-templates/google-calendar calendar-mcp
   cd calendar-mcp

2. Configure OAuth in project config.yml:
   [Creates config.yml with OAuth settings in project directory]

3. Test authentication:
   mxcp serve
   [Explains OAuth flow]

[Provides complete working OAuth integration]
```

### Example 3: Database Connection

```
User: "Connect to my PostgreSQL production database"

Claude: [Uses mxcp-expert skill]
I'll help you connect to your PostgreSQL database using DuckDB ATTACH.

1. Create project and config:
   mkdir postgres-mcp && cd postgres-mcp
   mxcp init --bootstrap

   Create config.yml with database credentials (uses environment variables)

2. Create SQL tool with ATTACH:
   [Creates tools/query_customers.yml with PostgreSQL ATTACH statement]

3. Set credentials and test:
   export DB_HOST="localhost" DB_USER="readonly_user" DB_PASSWORD="xxx"
   mxcp validate && mxcp run tool query_customers

4. Alternative: Cache data with dbt for fast queries
   [Shows dbt source + model pattern to materialize data]

[Provides both direct query and cached approaches with security best practices]
```

## Key Features Covered

### Endpoint Development
- SQL tools for data queries
- Python tools for complex logic
- Resources for data access
- Prompts with Jinja templates
- Combined SQL + Python patterns

### Enterprise Features
- OAuth authentication (GitHub, Google, Microsoft, etc.)
- Policy-based access control with CEL expressions
- Comprehensive audit logging (JSONL format)
- Field-level data filtering and masking
- User context testing

### Quality Assurance
- Structure validation with `mxcp validate`
- Functional testing with `mxcp test`
- Metadata quality checks with `mxcp lint`
- LLM behavior testing with `mxcp evals`

### dbt Integration
- Data transformation pipelines
- External data caching
- Incremental model patterns
- Data quality tests

### Production Operations
- Drift detection and monitoring
- Audit log querying and export
- Multi-environment profiles
- Secrets management (Vault, 1Password)
- OpenTelemetry observability

## Core Principles

This skill prioritizes:

1. **Security First** - Authentication, authorization, parameterized queries, input validation
2. **Robustness** - Error handling, type safety, data quality checks
3. **Validity** - Schema compliance, structure validation
4. **Testability** - Comprehensive test coverage
5. **Testing** - Always validate/test/lint before deployment

## Mandatory Workflow

**To ensure MXCP servers always work correctly, the agent follows:**

1. **Build incrementally** - One tool/component at a time
2. **Validate continuously** - `mxcp validate` after each change
3. **Test before proceeding** - `mxcp test` must pass before next step
4. **Verify manually** - Run actual tool with real data
5. **Definition of Done** - ALL validation checks must pass

The agent will NEVER declare a project complete unless all validation, tests, and manual verification succeed.

## Documentation Coverage

The skill includes comprehensive documentation based on official MXCP docs:

**CRITICAL - Start Here**:
- **build-and-validate-workflow.md** - MANDATORY workflow ensuring correctness
- **minimal-working-examples.md** - Guaranteed-to-work examples (copy, test, customize)

**Essential Guides** (for most projects):
- **project-selection-guide.md** - Decision trees, heuristics, when to use which approach
- **dbt-core-guide.md** - dbt seeds, models, schema.yml (critical for CSV/data projects)
- **duckdb-essentials.md** - DuckDB SQL features, CSV import, analytics
- **excel-integration.md** - Excel file handling and pandas integration
- **synthetic-data-patterns.md** - Generate test data with GENERATE_SERIES

**Detailed References**:
- **endpoint-patterns.md** - Complete tool/resource/prompt examples
- **python-api.md** - Python runtime API and library wrapping patterns
- **testing-guide.md** - Comprehensive testing strategies
- **policies.md** - Policy enforcement and security
- **type-system.md** - Type validation rules
- **cli-reference.md** - Complete CLI documentation
- **claude-desktop.md** - Claude Desktop integration
- **dbt-patterns.md** - Advanced dbt integration patterns

## About MXCP

MXCP is an enterprise-grade MCP (Model Context Protocol) framework that provides a structured methodology for building production AI applications:

1. **Data Quality First** - Start with dbt models and data contracts
2. **Service Design** - Define types, security policies, and API contracts
3. **Smart Implementation** - Choose SQL for data, Python for logic
4. **Quality Assurance** - Validate, test, lint, and evaluate
5. **Production Operations** - Monitor drift, track audits, ensure performance

## License

This skill compiles information from the MXCP project documentation.
MXCP is released under the Business Source License 1.1 (BSL).

For more information about MXCP:
- Website: https://mxcp.dev
- GitHub: https://github.com/raw-labs/mxcp
- Contact: mxcp@raw-labs.com

## Skill Version

Version: 1.0.0
Created: October 2025
Based on: MXCP documentation as of October 2025
