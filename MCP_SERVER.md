# MCP Server Setup for DREDGE

This repository includes a Model Context Protocol (MCP) server that runs on port 3001 in GitHub Codespaces.

## What is MCP?

Model Context Protocol (MCP) is an open-source protocol that allows AI applications to connect to external data sources, tools, and workflows. It provides a standardized way for AI agents to interact with your code and resources.

## Features

The DREDGE MCP server exposes the following tools:

- **get_version**: Get the DREDGE package version
- **hello_world**: A simple greeting tool that says hello
- **get_server_info**: Get information about the MCP server

## Using in GitHub Codespaces

### Automatic Startup

When you open this repository in GitHub Codespaces, the MCP server will automatically:

1. Install required dependencies
2. Start the MCP server on port 3001
3. Forward port 3001 so it's accessible

The port will be automatically forwarded and you'll receive a notification when it's ready.

### Manual Control

To manually start the MCP server:

```bash
python -m dredge.mcp_server
```

To stop the server, use `Ctrl+C`.

### Accessing the Server

Once running, the MCP server will be available at:
- Local: `http://localhost:3001`
- Codespaces: The forwarded URL provided by GitHub Codespaces

## Development

### Adding New Tools

To add new tools to the MCP server, edit `src/dredge/mcp_server.py` and add functions decorated with `@mcp.tool()`:

```python
@mcp.tool()
def my_new_tool(param: str) -> str:
    """
    Description of your tool.
    
    Args:
        param: Description of the parameter
    
    Returns:
        Description of the return value
    """
    return f"Result: {param}"
```

### Configuration

The MCP server configuration can be found in:
- `.devcontainer/devcontainer.json` - Codespaces configuration
- `src/dredge/mcp_server.py` - Server implementation

## Port Configuration

The MCP server listens on port **3001** by default. This is configured in:
- `src/dredge/mcp_server.py` (port=3001)
- `.devcontainer/devcontainer.json` (forwardPorts: [3001])

## Connecting AI Clients

To connect an AI client (like Claude Desktop, ChatGPT plugins, or other MCP-compatible tools) to this server:

1. Start the Codespace
2. Get the forwarded port URL for port 3001
3. Configure your AI client to connect to that URL

## Troubleshooting

### Server Not Starting

Check the logs:
```bash
python -m dredge.mcp_server
```

### Port Already in Use

If port 3001 is already in use, you can stop existing processes:
```bash
lsof -ti:3001 | xargs kill -9
```

### Dependencies Issues

Reinstall dependencies:
```bash
pip install -e .
```

## Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [GitHub Codespaces Port Forwarding](https://docs.github.com/en/codespaces/developing-in-codespaces/forwarding-ports-in-your-codespace)
