# Claude Code Marketplace

Community-driven marketplace for Claude Code plugins.

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
/plugin marketplace add raw-labs/claude-code-marketplace
```

### Install MXCP Plugin

```bash
/plugin install mxcp-plugin@claude-code-marketplace
```

Or use interactive mode:
```bash
/plugin
```
Interactive mode lets you browse, install, and manage plugins and marketplaces.

**💡 Tip: When using interactive mode, press `SPACE` to select the plugin you want to install before confirming. The plugin won't install if you don't select it first!**

**⚠️ Important: Restart Claude Code after installing the plugin for changes to take effect.**

### Update

Update marketplace:
```bash
/plugin marketplace update claude-code-marketplace
```

Update plugin:
```bash
/plugin update mxcp-plugin
```

## Using MXCP Plugin

The `mxcp-plugin` plugin helps you build Model Context Protocol (MCP) servers for databases, APIs, and data files.

### Example Prompts

**Database Integration:**
```
Create an MXCP server for my PostgreSQL database at localhost:5432
```

**API Wrapper:**
```
Build an MXCP server that wraps the my API, you can find the api specification in the my-api.json file
```

**CSV/Excel Data:**
```
I have customer_data.csv in the current directory. Create an MXCP server 
to query and analyze this data
```

**Custom Data Pipeline:**
```
Create an MXCP server that:
1. Ingests sales.xlsx
2. Connects to my MySQL database
3. Provides tools to compare the data sources
```

**REST API to MCP:**
```
Build an MXCP server for the Stripe API with payment and subscription tools
```

## Claude Code Best Practices

### Be Specific

- **Point to files**: "Use data.csv in ./data/" instead of "use the CSV file"
- **Explain the goal**: "Create a REST API with authentication" not just "make an API"
- **Provide context**: Share schema, examples, or existing code patterns

### Give Guidance

- Ask Claude questions if unclear: "Should I use JWT or session auth?"
- Provide requirements upfront: "Python 3.11, FastAPI, PostgreSQL"
- Share constraints: "Keep response time under 100ms"

### Stay Engaged

- **Interrupt if off-track**: "Stop. That's not what I need. I want X instead"
- **Review changes**: Check diffs before accepting
- **Iterate**: "Good, now add error handling for timeout scenarios"

### Provide Examples

- Show desired output format
- Share similar code you like
- Reference documentation or patterns to follow

### Use Available Context

- Upload relevant files (schemas, configs, documentation)
- Mention related files in your codebase
- Point to specific functions or modules

## Resources

- [Claude Code Documentation](https://www.claude.com/product/claude-code)
- [Plugin Marketplace Docs](https://docs.claude.com/id/docs/claude-code/plugin-marketplaces)
