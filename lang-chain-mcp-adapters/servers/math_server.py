"""
Math Server Module for MCP Integration.

This module provides basic mathematical operations through an MCP (Model Control Protocol) server.
It implements simple arithmetic functions that can be called remotely through the MCP interface.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Math")


@mcp.tool()
def add(a: int, b: int) -> int:
    """
    Add two integers together.

    Args:
        a (int): First number to add
        b (int): Second number to add

    Returns:
        int: The sum of a and b
    """
    return a + b


@mcp.tool()
def multiply(a: int, b: int) -> int:
    """
    Multiply two integers together.

    Args:
        a (int): First number to multiply
        b (int): Second number to multiply

    Returns:
        int: The product of a and b
    """
    return a * b


if __name__ == "__main__":
    mcp.run(transport="stdio")
