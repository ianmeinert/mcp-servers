# MCP Servers Prototype

This repository contains a prototype implementation of Model Context Protocol (MCP) servers and adapters, demonstrating how to integrate LLM agents with external tools and APIs. The project consists of two main components:

1. **LangChain MCP Adapters**: A collection of adapters and example servers for integrating LangChain with MCP
2. **Shell Server**: A Python-based MCP server implementation

## Project Structure

```
.
├── lang-chain-mcp-adapters/    # LangChain integration with MCP
│   ├── servers/                # Example MCP servers (math, weather)
│   ├── langchain_client.py     # Multi-server client example
│   └── main.py                # Basic MCP server connection example
└── shellserver/               # Python MCP server implementation
    ├── server.py              # Main server implementation
    └── Dockerfile            # Container configuration
```

## Prerequisites

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) (recommended for dependency management)
- Docker (optional, for running the shell server in a container)

## Installation

### LangChain MCP Adapters

1. Navigate to the lang-chain-mcp-adapters directory:

   ```bash
   cd lang-chain-mcp-adapters
   ```

2. Install dependencies:

   ```bash
   uv add -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env_sample .env
   # Edit .env with your API keys and model names
   ```

### Shell Server

1. Navigate to the shellserver directory:

   ```bash
   cd shellserver
   ```

2. Install dependencies:
   ```bash
   uv add -r requirements.txt
   ```

## Usage

### Running the LangChain MCP Adapters

1. Start an MCP server (e.g., math server):

   ```bash
   cd lang-chain-mcp-adapters
   uv run servers/math_server.py
   ```

2. Run the LangChain client:
   ```bash
   uv run langchain_client.py
   ```

### Running the Shell Server

1. Start the server:

   ```bash
   cd shellserver
   uv run server.py
   ```

2. Or run with Docker:
   ```bash
   docker build -t mcp-shellserver .
   docker run -p 8000:8000 mcp-shellserver
   ```

## Features

- **Multiple Server Types**: Support for both stdio and SSE transport protocols
- **LangChain Integration**: Seamless integration with LangChain agents
- **Example Servers**: Math and weather server implementations included
- **Docker Support**: Containerized deployment option for the shell server
- **Extensible Architecture**: Easy to add new MCP servers and tools

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
