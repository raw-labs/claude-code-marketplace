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

## Usage Example - Excel Files

The `mxcp-plugin` helps you build Model Context Protocol (MCP) servers. Here's a real workflow for turning Excel data into a queryable MXCP server.

### Step 1: Build Context About the Excel File

Before asking Claude to build anything, it needs to understand what's in your Excel file. You have two approaches:

**Describe it yourself** if you already know the structure - explain what sheets exist, what columns they have, and what the data represents.

**Ask Claude to read it** if you want Claude to figure it out:
```
Read the Excel file at ./data/report.xlsx and tell me what it contains.
```

**The problem with messy Excel files:** Many real-world Excel files are completely unstructured - merged cells scattered chaotically, inconsistent layouts, data in unexpected places. When Claude reads these programmatically, it struggles because the underlying libraries put values in the first cell of a merged range while the rest appear empty. The structure that's visually obvious to a human becomes a confusing mess of sparse data.

**The solution - use screenshots:** Since Claude is multimodal, you can provide a screenshot of the Excel file. This lets Claude see the visual layout the same way you do, making it much easier to understand files with complex formatting, merged cells, or unconventional structures.

### Step 2: Specify What You Want Built

Once Claude understands the data, tell it to create an MXCP server. The key steps are:

1. **Ingest the Excel data into DuckDB first** - this is essential before the server can query anything

2. **Choose an ingestion approach:**
   - **Python models**: Claude writes Python code that reads the Excel and loads it into DuckDB directly
   - **CSV + dbt seeds**: Claude first converts the Excel to CSV files, then uses dbt to seed them into DuckDB - this approach gives you dbt's transformation capabilities

3. **Provide example questions and answers** that you want the server to handle. These examples help Claude understand the analytical capabilities you need. Importantly, tell Claude to make the implementations generic - you don't just want it to answer your specific example questions, you want it to handle any question of that type.

Example prompt:
```
Create an MXCP server based on this Excel file. First ingest the data into
DuckDB using dbt seeds.

The server should answer questions like:
- What were total sales by region? (Answer: aggregated revenue grouped by region)
- Which products sell best? (Answer: products ranked by units sold)
- How do sales trend over time? (Answer: time series of sales metrics)

Make these generic so any similar analytical question works, not just these
exact queries.
```

### Step 3: Stay Engaged During Implementation

The plugin already instructs Claude to validate the server, write tests for both dbt and MXCP, and follow best practices. But the process is interactive - watch what Claude does and intervene when needed.

Claude will make assumptions about your data and requirements. Some will be wrong, especially things you didn't explicitly specify. When you see Claude heading in a direction you don't want, interrupt and correct it. This back-and-forth is normal and produces better results than trying to specify everything upfront.

Any additional context you provide during the process helps - the more Claude understands about your actual use case, the better the final server will be.

**Note:** These three steps can be combined into a single prompt. If you know your data well and have clear requirements, provide everything at once - the context about the Excel file, the MXCP server request with ingestion approach, and the example questions. Claude will work through it all in one go.

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
