import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()
gemini_model = os.getenv("GOOGLE_MODEL")
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

# Get the current directory and construct the path to math_server.py
current_dir = Path(__file__).parent
math_server_path = current_dir / "servers" / "math_server.py"

stdio_server_params = StdioServerParameters(
    command="python",
    args=[str(math_server_path)],
)

async def main():
    try:
        async with stdio_client(stdio_server_params) as (read, write):
            async with ClientSession(read_stream=read, write_stream=write) as session:
                await session.initialize()
                print("Session initialized")
                tools = await load_mcp_tools(session)

                agent = create_react_agent(llm,tools)

                result = await agent.ainvoke({"messages": [HumanMessage(content="What is 54 + 2 * 3?")]})
                print(result["messages"][-1].content)
                
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
