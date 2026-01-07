# RAW Labs Marketplace for Claude

RAW Labs Marketplace for Claude plugins.

Community-driven marketplace, so feel free to use and contribute!

## Getting Started

### Install Claude Code

**macOS/Linux:**
```bash
curl -fsSL https://claude.ai/install.sh | bash
```

**Windows:**
```powershell
irm https://claude.ai/install.ps1 | iex
```

### Add This Marketplace

```bash
/plugin marketplace add raw-labs/raw-labs-claude-marketplace
```

## MXCP Plugin

The MXCP plugin helps you build Model Context Protocol (MCP) servers using the MXCP framework. It includes two skills:

| Skill | Description |
|-------|-------------|
| **mxcp-expert** | Expert guidance for building MXCP servers with SQL and Python endpoints |
| **document-to-mxcp** | Intelligent document ingestion (Excel, Word) into MXCP servers |

### Installation

```bash
/plugin install mxcp-plugin@raw-labs-claude-marketplace
```

Or use interactive mode:
```bash
/plugin
```

**Tip:** In interactive mode, press `SPACE` to select the plugin before confirming.

**Important:** Restart Claude Code after installing for changes to take effect.

### Usage: Document Ingestion

The `document-to-mxcp` skill automatically ingests Excel (.xlsx, .xls, .csv) and Word (.docx) files into MXCP servers. It analyzes content to determine whether data needs structured queries (DuckDB) or semantic search (RAG).

**Example prompt:**
```
Ingest the Excel file at ./data/sales_report.xlsx into an MXCP server.
I need to query total sales by region and search product descriptions.
```

Claude will:
1. Analyze the file structure and content types
2. Create dbt models for queryable data
3. Generate RAG content for text-heavy data
4. Build tools for the queries you need
5. Run tests to validate everything works

**For complex Excel files** with merged cells or unusual layouts, provide a screenshot - Claude can understand the visual structure better than parsing alone.

**For Word documents:**
```
Ingest the Word document at ./docs/annual_report.docx into an MXCP server.
```

### Usage: Building MXCP Servers

The `mxcp-expert` skill helps with general MXCP development:

```
Create an MXCP server that connects to my PostgreSQL database and
provides tools for querying customer orders.
```

The skill covers:
- SQL and Python endpoints
- Authentication (OAuth with GitHub, Google, etc.)
- Testing and validation
- Deployment options

## Best Practices

### Be Specific
- Point to files: "Use data.csv in ./data/" not "use the CSV file"
- Explain the goal: "Create a REST API with authentication"
- Provide context: Share schema, examples, or existing patterns

### Stay Engaged
- Interrupt if off-track: "Stop. That's not what I need."
- Review changes before accepting
- Iterate: "Good, now add error handling"

### Provide Examples
- Show desired output format
- Share similar code you like
- Reference documentation to follow

## Update

Update marketplace:
```bash
/plugin marketplace update raw-labs-claude-marketplace
```

Update plugin:
```bash
/plugin update mxcp-plugin@raw-labs-claude-marketplace
```

## Resources

- [RAW Labs](https://www.raw-labs.com/)
- [MXCP Quickstart](https://mxcp.dev/getting-started/quickstart/)
- [MXCP Documentation](https://mxcp.dev)
- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)
- [Plugin Marketplace Docs](https://docs.anthropic.com/en/docs/claude-code/plugins)
