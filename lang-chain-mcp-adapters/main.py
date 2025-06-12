"""
Main module for the LangChain MCP Adapters integration.

This module demonstrates the integration of LangChain with MCP (Model Control Protocol)
to create an agent that can perform mathematical operations using a math server.
It uses Google's Gemini model for natural language processing and MCP tools for
mathematical computations.

Features:
- MCP server integration for mathematical operations
- Natural language processing with Google's Gemini model
- ReAct agent for mathematical problem solving
- Asynchronous operation support
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Load environment variables from .env file
load_dotenv()

# Initialize the Gemini model for natural language processing
gemini_model = os.getenv("GOOGLE_MODEL")
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

# Set up the path to the math server script
current_dir = Path(__file__).parent
math_server_path = current_dir / "servers" / "math_server.py"

# Configure the stdio server parameters for the math server
stdio_server_params = StdioServerParameters(
    command="python",
    args=[str(math_server_path)],
)


async def main():
    """
    Main async function that sets up and runs the MCP client session with LangChain integration.

    This function:
    1. Establishes a connection with the math server
    2. Initializes an MCP client session
    3. Loads MCP tools for mathematical operations
    4. Creates a ReAct agent using the Gemini model
    5. Processes a mathematical query using the agent

    The function includes error handling for session initialization and execution.

    Raises:
        Exception: If any error occurs during the session initialization or execution
    """
    try:
        # Create stdio client connection to the math server
        async with stdio_client(stdio_server_params) as (read, write):
            # Initialize MCP client session
            async with ClientSession(read_stream=read, write_stream=write) as session:
                await session.initialize()
                print("Session initialized")

                # Load MCP tools for mathematical operations
                tools = await MultiServerMCPClient.get_tools(session)

                # Create a ReAct agent with the Gemini model and MCP tools
                agent = create_react_agent(llm, tools)

                # Process a mathematical query using the agent
                result = await agent.ainvoke(
                    {"messages": [HumanMessage(content="What is 54 + 2 * 3?")]}
                )
                print(result["messages"][-1].content)

    except (ConnectionError, RuntimeError, ValueError) as e:
        print(f"Error occurred: {e}")


if __name__ == "__main__":
    # Run the main async function
    asyncio.run(main())
