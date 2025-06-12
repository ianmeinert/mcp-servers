"""
Terminal Server Module for MCP Integration.

This module provides a terminal server implementation using the Model Control Protocol (MCP).
It allows for secure execution of terminal commands through an MCP interface.

Features:
- Secure command execution
- Error handling and reporting
- Asynchronous operation support
- MCP tool integration
"""

import asyncio
import subprocess

from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("Terminal Server")


@mcp.tool()
async def run_command(command: str) -> str:
    """Execute a terminal command and return its output.

    Args:
        command: The terminal command to execute

    Returns:
        str: The command output as a string

    Raises:
        subprocess.CalledProcessError: If the command execution fails
        Exception: For any unexpected errors during command execution
    """
    try:
        # Run the command and capture output
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error executing command: {e.stderr}"
    except (OSError, subprocess.SubprocessError) as e:
        return f"Command execution failed: {str(e)}"


if __name__ == "__main__":
    # This will run the server in stdio mode
    asyncio.run(mcp.run())
