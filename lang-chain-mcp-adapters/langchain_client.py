import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent

load_dotenv()

# Get the current directory and construct the path to math_server.py
current_dir = Path(__file__).parent
math_server_path = current_dir / "servers" / "math_server.py"

# Initialize the LLM with a fallback model
model_name = os.getenv("GOOGLE_MODEL", "gemini-2.0-flash")
llm = ChatGoogleGenerativeAI(model=model_name)

client_params = {
        "math": {
            "command": "python",
            # Make sure to update to the full absolute path to your math_server.py file
            "args": [str(math_server_path)],
            "transport": "stdio",
        },
        "weather": {
            # make sure you start your weather server on port 8000
            "url": "http://localhost:8000/sse",
            "transport": "sse",
        }
    }


async def main():
    try:
        print("Starting LangChain client...")
        client = MultiServerMCPClient(client_params)
        tools = await client.get_tools()
        agent = create_react_agent(llm, tools)
        math_response = await agent.ainvoke({"messages": HumanMessage(content="what's (3 + 5) x 12?")})
        weather_response = await agent.ainvoke({"messages": HumanMessage(content="what is the weather in nyc?")})
        print(math_response["messages"][-1].content)
        print(weather_response["messages"][-1].content)
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
