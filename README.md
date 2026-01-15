# DREDGE

DREDGE — small Python package scaffold with MCP server support.

## Install

Create a virtual environment and install:

python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e .

## MCP Server

DREDGE includes a Model Context Protocol (MCP) server that runs on port 3001. This allows AI agents to interact with DREDGE tools and resources.

For detailed information about the MCP server, see [MCP_SERVER.md](MCP_SERVER.md).

### Quick Start

Run the MCP server:

```bash
python -m dredge.mcp_server
```

The server will start on port 3001 and expose tools for AI agents.

## Test

Run tests with pytest:

pip install -U pytest
pytest

## Development

- Edit code in src/dredge
- Update version in pyproject.toml
- Tag releases with v<version> and push tags