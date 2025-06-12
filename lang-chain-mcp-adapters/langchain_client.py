"""
LangChain MCP Client Module for Multi-Server Integration.

This module demonstrates the integration of LangChain with multiple MCP (Model Control Protocol)
servers, specifically focusing on PII (Personally Identifiable Information) handling.
It uses Google's Gemini model for natural language processing and MCP tools for
processing sensitive information in a secure manner.

Features:
- Multi-server MCP client integration
- PII handling and processing
- Natural language processing with Google's Gemini model
- Secure processing of sensitive information
"""

import asyncio
import os
from pathlib import Path
import traceback

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

# Load environment variables from .env file
load_dotenv()

# Set up paths to server scripts
current_dir = Path(__file__).parent
math_server_path = current_dir / "servers" / "math_server.py"
pii_server_path = current_dir / "servers" / "pii_server.py"

# Initialize the LLM with a fallback model if environment variable is not set
model_name = os.getenv("GOOGLE_MODEL", "gemini-2.0-flash")
llm = ChatGoogleGenerativeAI(model=model_name)

# Configure client parameters for the PII server
client_params = {
    "pii": {
        "command": "python",
        "args": [str(pii_server_path)],
        "transport": "stdio",
    }
}


async def main():
    """
    Main async function that sets up and runs the multi-server MCP client with LangChain
    integration.

    This function:
    1. Initializes a MultiServerMCPClient with PII handling capabilities
    2. Creates a ReAct agent using the Gemini model
    3. Processes a sample email containing PII using the agent
    4. Handles and displays the processed response

    The function includes error handling with detailed traceback for debugging purposes.

    Raises:
        Exception: If any error occurs during client initialization or execution
    """
    try:
        print("Starting LangChain client...")
        # Initialize multi-server MCP client
        client = MultiServerMCPClient(client_params)
        tools = await client.get_tools()

        # Create a ReAct agent with the Gemini model and MCP tools
        agent = create_react_agent(llm, tools)

        # Sample email content containing PII for testing
        email_content = """
Generate an order confirmation email using a fictitious product addressed to the following customer:

Name: John Doe 
Address: 123 Someplace Dr 
City: Somewhere, DC 12345 
Phone: (123) 456-7890 
Email: me@myemail.com 
Credit Card Number: 1234 5678 9012 3456
"""

        # Process the email content using the PII handling tool
        response = await agent.ainvoke(
            {
                "messages": HumanMessage(
                    content=(
                        "Use the process_with_pii tool to generate an email with this "
                        f"customer information: {email_content}"
                    )
                )
            }
        )

        # Display the processed response if available
        if response and "messages" in response and response["messages"]:
            print("\nGenerated email with PII handling:")
            print(response["messages"][-1].content)
        else:
            print("No response received from the agent")

    except (ConnectionError, RuntimeError, ValueError) as e:
        # Enhanced error handling with full traceback
        print(f"Error occurred: {str(e)}")

        print("Full error traceback:")
        print(traceback.format_exc())


if __name__ == "__main__":
    # Run the main async function
    asyncio.run(main())
