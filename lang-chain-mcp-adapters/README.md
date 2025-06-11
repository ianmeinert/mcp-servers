# LangChain MCP Adapters

A collection of adapters and example servers for integrating [LangChain](https://github.com/langchain-ai/langchain) with the Model Context Protocol (MCP). This project demonstrates how to connect LLM agents to external tools and APIs using MCP servers, including math, weather, and PII handling examples.

---

## Features

- **MCP Server Examples:** Math, Weather, and PII handling servers included, easily extensible.
- **LangChain Integration:** Use MCP tools as part of your LangChain agent workflows.
- **Multi-Server Support:** Connect to multiple MCP servers (stdio and SSE).
- **Gemini & OpenAI Support:** Easily switch between LLM providers.
- **PII Handling:** Secure handling of Personally Identifiable Information with session tracking, database management, and LangSmith integration.
- **Enhanced Security:** Improved PII processing with session management and comprehensive logging.

---

## Getting Started

### Prerequisites

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) (for fast dependency management and running scripts)
- LangSmith API key (for PII server tracking)

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/lang-chain-mcp-adapters.git
   cd lang-chain-mcp-adapters
   ```

2. **Install dependencies using uv:**

   ```bash
   uv add -r requirements.txt
   ```

3. **Set up environment variables:**
   - Copy `.env_sample` to `.env` and fill in your API keys and model names.

---

## Project Structure

```
.
├── main.py                # Example: Connects to math MCP server and runs a query
├── langchain_client.py    # Example: Multi-server client (math, weather, PII)
├── servers/
│   ├── math_server.py     # Math MCP server (add, multiply)
│   ├── weather_server.py  # Weather MCP server (example)
│   └── pii_server.py      # PII handling server (sanitization, restoration, and session tracking)
├── .env_sample            # Sample environment variables
├── pyproject.toml         # Project dependencies
└── README.md              # This file
```

---

## Usage

### Running the Math MCP Server

```bash
uv run servers/math_server.py
```

### Running the Weather MCP Server

```bash
uv run servers/weather_server.py
```

### Running the PII Handler Server

```bash
uv run servers/pii_server.py
```

The PII server provides enhanced functionality for secure PII handling:

1. `sanitize_input`: Masks PII in input text with session tracking
2. `restore_pii`: Restores original PII values in processed text using secure database management
3. **Session Management:** Tracks PII processing sessions for audit and security
4. **Database Management:** Secure storage and retrieval of PII data
5. **Comprehensive Logging:** Detailed logging of all PII operations

Example usage:

```python
# Input text with PII
text = "Contact me at john@example.com or 555-123-4567"

# Sanitize the input with session tracking
sanitized = sanitize_input(text)
# Result: "Contact me at [MASKED_EMAIL_15] or [MASKED_PHONE_12]"

# Process with LLM...

# Restore PII in the response using secure database lookup
restored = restore_pii(sanitized)
# Result: "Contact me at john@example.com or 555-123-4567"
```

### Running the LangChain Client

```bash
uv run langchain_client.py
```

### Example Output

```
Starting LangChain client...
Loading tools from math server...
Loaded 2 tools
Processing query...
Result: 4
```

---

## Adding New MCP Servers

To add a new MCP server, create a new file in the `servers/` directory. For example, a simple calculator server:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Calculator")

@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    return a - b

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

---

## Example MCP Servers from the Community

- **Mailtrap Email Sending:** Send transactional emails via API.
- **Neon:** Interact with serverless Postgres.
- **GitHub:** Manage GitHub issues.
- **Resend:** Send emails using Resend API.
- **Supabase:** Query Postgres databases via PostgREST.

Find more at [cursor.directory/mcp](https://cursor.directory/mcp).

---

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

---

## License

[MIT](LICENSE)
