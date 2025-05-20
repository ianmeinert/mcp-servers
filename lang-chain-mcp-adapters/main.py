import asyncio
import os

from dotenv import load_dotenv

load_dotenv()
print(os.getenv("GOOGLE_API_KEY"))

async def main():
    print("Hello from lang-chain-mcp-adapters!")


if __name__ == "__main__":
    asyncio.run(main())
