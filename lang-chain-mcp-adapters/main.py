import asyncio
import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro")

stdio_server_params = StdioServerParameters(
    command="python",
    args=["C:\\Users\\marin\\Documents\\Computers\\DeveloperPortal\\mcp-servers\\lang-chain-mcp-adapters\\math.py"],
)

async def main():
    print("Hello from lang-chain-mcp-adapters!")


if __name__ == "__main__":
    asyncio.run(main())
