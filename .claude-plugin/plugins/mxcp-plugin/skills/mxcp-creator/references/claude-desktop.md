# Claude Desktop Integration

Guide to connecting MXCP servers with Claude Desktop.

## Quick Setup

### 1. Initialize MXCP Project

```bash
mkdir my-mxcp-tools && cd my-mxcp-tools
mxcp init --bootstrap
```

The `--bootstrap` flag automatically creates `server_config.json` with the correct configuration for your environment.

### 2. Locate Claude Config

**macOS**:
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows**:
```
%APPDATA%\Claude\claude_desktop_config.json
```

**Linux**:
```
~/.config/Claude/claude_desktop_config.json
```

### 3. Add MXCP Server

Edit the Claude config file:

```json
{
  "mcpServers": {
    "my-tools": {
      "command": "mxcp",
      "args": ["serve", "--transport", "stdio"],
      "cwd": "/absolute/path/to/my-mxcp-tools"
    }
  }
}
```

**Important**: Use absolute paths for `cwd`.

### 4. Restart Claude Desktop

Close and reopen Claude Desktop. Your tools should now be available.

## Verifying Connection

### Check Tool Availability

Ask Claude:
- "What tools do you have available?"
- "List the MXCP tools you can use"

### Test a Tool

Ask Claude to use one of your tools:
- "Use the hello_world tool with name='Claude'"
- "Show me what the calculate_fibonacci tool does"

## Environment-Specific Configurations

### Virtual Environment

```json
{
  "mcpServers": {
    "my-tools": {
      "command": "/path/to/venv/bin/mxcp",
      "args": ["serve", "--transport", "stdio"],
      "cwd": "/path/to/project"
    }
  }
}
```

### Poetry Project

```json
{
  "mcpServers": {
    "my-tools": {
      "command": "poetry",
      "args": ["run", "mxcp", "serve", "--transport", "stdio"],
      "cwd": "/path/to/project"
    }
  }
}
```

### System-Wide Installation

```json
{
  "mcpServers": {
    "my-tools": {
      "command": "mxcp",
      "args": ["serve", "--transport", "stdio"],
      "cwd": "/path/to/project"
    }
  }
}
```

## Multiple MCP Servers

You can connect multiple MXCP projects:

```json
{
  "mcpServers": {
    "company-data": {
      "command": "mxcp",
      "args": ["serve", "--transport", "stdio"],
      "cwd": "/path/to/company-data-project"
    },
    "ml-tools": {
      "command": "mxcp",
      "args": ["serve", "--transport", "stdio"],
      "cwd": "/path/to/ml-tools-project"
    },
    "external-apis": {
      "command": "mxcp",
      "args": ["serve", "--transport", "stdio"],
      "cwd": "/path/to/external-apis-project"
    }
  }
}
```

## Using Profiles

Connect to different environments:

```json
{
  "mcpServers": {
    "company-dev": {
      "command": "mxcp",
      "args": ["serve", "--transport", "stdio", "--profile", "dev"],
      "cwd": "/path/to/project"
    },
    "company-prod": {
      "command": "mxcp",
      "args": ["serve", "--transport", "stdio", "--profile", "prod"],
      "cwd": "/path/to/project"
    }
  }
}
```

## Troubleshooting

### Tools Not Appearing

1. Check Claude config syntax:
   ```bash
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | jq
   ```

2. Verify MXCP installation:
   ```bash
   which mxcp
   mxcp --version
   ```

3. Test server manually:
   ```bash
   cd /path/to/project
   mxcp serve --transport stdio
   # Should wait for input
   # Press Ctrl+C to exit
   ```

4. Check project structure:
   ```bash
   ls -la /path/to/project
   # Should see mxcp-site.yml and tools/ directory
   ```

### Connection Errors

**Error: Command not found**
- Use absolute path to mxcp executable
- Check virtual environment activation

**Error: Permission denied**
- Ensure mxcp executable has execute permissions
- Check directory permissions

**Error: No tools available**
- Verify `tools/` directory exists
- Run `mxcp validate` to check endpoints
- Check `mxcp-site.yml` configuration

### Debug Mode

Enable debug logging:

```json
{
  "mcpServers": {
    "my-tools": {
      "command": "mxcp",
      "args": ["serve", "--transport", "stdio", "--debug"],
      "cwd": "/path/to/project"
    }
  }
}
```

Check Claude logs:
- macOS: `~/Library/Logs/Claude/`
- Windows: `%APPDATA%\Claude\logs\`
- Linux: `~/.config/Claude/logs/`

## Best Practices

1. **Use --bootstrap** - Creates correct config automatically
2. **Absolute Paths** - Always use absolute paths in config
3. **Test Locally** - Run `mxcp serve` manually before adding to Claude
4. **Multiple Projects** - Organize related tools in separate projects
5. **Profiles** - Use different profiles for dev/staging/prod
6. **Validation** - Run `mxcp validate` before deployment
7. **Version Control** - Keep `server_config.json` in .gitignore

## Example Workflow

```bash
# 1. Create project
mkdir my-tools && cd my-tools
mxcp init --bootstrap

# 2. Test locally
mxcp serve
# Ctrl+C to exit

# 3. Copy config path from server_config.json
cat server_config.json

# 4. Edit Claude config
vim ~/Library/Application\ Support/Claude/claude_desktop_config.json

# 5. Restart Claude Desktop

# 6. Test in Claude
# Ask: "What tools do you have?"
```

## Security Notes

- Never commit API keys in Claude config
- Use secrets management (Vault, 1Password)
- Set appropriate file permissions
- Use read-only mode for production: `--readonly`
- Enable audit logging for compliance
