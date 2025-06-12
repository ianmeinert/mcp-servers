"""
Weather Server Module for MCP Integration.

This module provides weather information through an MCP (Model Control Protocol) server.
It implements a simple weather service that can be called remotely through the MCP interface.
Currently, it returns a mock response for demonstration purposes.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Weather")


@mcp.tool()
async def get_weather(location: str) -> str:
    """
    Get weather information for a specified location.

    Args:
        location (str): The location to get weather information for

    Returns:
        str: A string containing the weather information for the specified location

    Note:
        This is currently a mock implementation that always returns "sunny" weather.
    """
    print("This is a log from the SSE Server")
    return f"It's always sunny in {location}"


if __name__ == "__main__":
    mcp.run(transport="sse")
