import asyncio
import os
import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("Terminal Server")

# Get the desktop path
DESKTOP_PATH = str(Path.home() / "Desktop")

@mcp.resource("readme://desktop")
async def get_readme() -> str:
    """Get the contents of README.md from the desktop directory.
    
    Returns:
        The contents of the README.md file as a string
    """
    try:
        readme_path = os.path.join(DESKTOP_PATH, "README.md")
        if os.path.exists(readme_path):
            with open(readme_path, 'r', encoding='utf-8') as f:
                return f.read()
        return "README.md not found on desktop"
    except Exception as e:
        return f"Error reading README.md: {str(e)}"

@mcp.tool()
async def run_command(command: str) -> str:
    """Execute a terminal command and return its output.
    
    Args:
        command: The terminal command to execute
        
    Returns:
        The command output as a string
    """
    try:
        # Run the command and capture output
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error executing command: {e.stderr}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

if __name__ == "__main__":
    # This will run the server in stdio mode
    asyncio.run(mcp.run())
