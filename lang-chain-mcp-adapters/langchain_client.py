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

# Get the current directory and construct paths to server files
current_dir = Path(__file__).parent
math_server_path = current_dir / "servers" / "math_server.py"
pii_server_path = current_dir / "servers" / "pii_server.py"

# Initialize the LLM with a fallback model
model_name = os.getenv("GOOGLE_MODEL", "gemini-2.0-flash")
llm = ChatGoogleGenerativeAI(model=model_name)

client_params = {
    "pii": {
        "command": "python",
        "args": [str(pii_server_path)],
        "transport": "stdio",
    }
}

async def main():
    try:
        print("Starting LangChain client...")
        client = MultiServerMCPClient(client_params)
        tools = await client.get_tools()
        agent = create_react_agent(llm, tools)
        
        # Test email with PII
        email_content = """
Generate an order confirmation email using a fictitious product addressed to the following customer:

Name: John Doe 
Address: 123 Someplace Dr 
City: Somewhere, DC 12345 
Phone: (123) 456-7890 
Email: me@myemail.com 
Credit Card Number: 1234 5678 9012 3456
"""
        
        # Process the email with PII handling
        response = await agent.ainvoke({
            "messages": HumanMessage(content=f"Use the process_with_pii tool to generate an email with this customer information: {email_content}")
        })
        
        if response and "messages" in response and response["messages"]:
            print("\nGenerated email with PII handling:")
            print(response["messages"][-1].content)
        else:
            print("No response received from the agent")
            
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        import traceback
        print("Full error traceback:")
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())
