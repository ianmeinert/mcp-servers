# MCP Shell Server

A Model Context Protocol (MCP) server implementation that provides terminal command execution capabilities and file system access. This server allows LLM agents to interact with the local system through a secure and controlled interface.

## Features

- **Terminal Command Execution**: Run shell commands and capture their output
- **File System Access**: Read files from the desktop directory
- **Async Support**: Built with asyncio for efficient operation
- **Docker Support**: Containerized deployment option
- **FastMCP Integration**: Uses the FastMCP framework for MCP protocol implementation
- **uv Integration**: Fast dependency management and virtual environment handling
- **Enhanced Security**: Improved security with comprehensive logging and audit trails
- **PII Protection**: Secure handling of Personally Identifiable Information

## Prerequisites

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer and resolver
- Docker (optional, for containerized deployment)

## Installation

### Local Installation with uv

1. Install uv if you haven't already:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Navigate to the shellserver directory:

   ```bash
   cd shellserver
   ```

3. Create and activate virtual environment:

   ```bash
   uv venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

4. Install dependencies:

   ```bash
   uv sync
   ```

### Docker Installation

1. Build the Docker image:

   ```bash
   docker build -t mcp-shellserver .
   ```

## Environment Variables

The server can be configured using the following environment variables:

- `MCP_SERVER_PORT`: Port number for the server (default: 8000)
- `MCP_SERVER_HOST`: Host address to bind to (default: 0.0.0.0)
- `MCP_LOG_LEVEL`: Logging level (default: INFO)
- `MCP_ALLOWED_PATHS`: Comma-separated list of allowed file system paths
- `MCP_MAX_COMMAND_SIZE`: Maximum size of command input in bytes (default: 8192)

To set these variables, create a `.env` file in the shellserver directory:

```bash
cp .env_sample .env  # If .env_sample exists
# Edit .env with your desired configuration
```

## Usage

### Running with uv

1. Activate the virtual environment (if not already activated):

   ```bash
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Run the server:

   ```bash
   uv run server.py
   ```

### Running with Docker

Run the container:

```bash
docker run -p 8000:8000 mcp-shellserver
```

## Security Considerations

The server implements several security measures to ensure safe operation:

### Command Execution Security

- Command validation and sanitization
- Restricted command execution environment
- Command timeout limits
- Output size limits

### File System Security

- Path validation and sanitization
- Restricted file system access
- File type validation
- Access control lists

### Container Security

- Docker-based isolation
- Resource limits
- Network isolation
- Read-only filesystem where possible

### Logging and Monitoring

- Comprehensive operation logging
- Security event tracking
- Performance monitoring
- Error reporting

### Best Practices

- Regular security updates
- Dependency scanning
- Secure configuration
- Documentation of security features

## Project Structure

```text
shellserver/
├── server.py          # Main server implementation
├── Dockerfile         # Container configuration
├── requirements.txt   # Python dependencies
├── pyproject.toml     # Project metadata and dependencies
├── uv.lock           # uv dependency lock file
└── README.md         # This file
```

### Adding New Tools

To add a new tool to the server:

1. Import the FastMCP decorator:

   ```python
   from mcp.server.fastmcp import FastMCP
   ```

2. Create a new tool function with the `@mcp.tool()` decorator:

   ```python
   @mcp.tool()
   async def my_new_tool(param: str) -> str:
       """Tool description."""
       return result
   ```

3. Install any new dependencies:

   ```bash
   uv pip install new_dependency
   uv pip freeze > requirements.txt
   ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
