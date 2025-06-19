"""
Psychologist Server Module for MCP Integration (Conversational Flow).

This module implements a conversational MCP tool that guides the user through the three animal personality questions, tracks state, and provides a dynamic analysis using Gemini LLM when all answers are collected. Designed for seamless integration with LLM agents like Claude.

Features:
- Conversational, step-by-step question flow
- Stateless: client sends current state and latest answer
- Dynamic animal analysis using Gemini LLM
- JSON input/output for easy agent integration

Tool Interface:
Input:
    {
        "state": {"first": str|None, "second": str|None, "third": str|None},
        "answer": str|None
    }
Output:
    If not all answers collected:
        {"next_question": str, "state": {...}}
    If all answers collected:
        {"analysis": {...}, "summary": str, "state": {...}}
"""

import logging
import os
from typing import Any, Dict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from mcp.server.fastmcp import FastMCP

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("Psychologist")

# Initialize the LLM with a fallback model if environment variable is not set
model_name = os.getenv("GOOGLE_MODEL", "gemini-2.0-flash")
# Make sure the environment variable is set
api_key = os.getenv("GOOGLE_API_KEY")
llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key)

QUESTIONS = [
    "If you had to pick one animal that comes to mind first that you feel like is most like you or explains your personality, pick it.",
    "If that animal didn't exist, pick the very next animal that comes to mind.",
    "If that animal didn't exist either, pick the very next animal that resonates with you.",
]


async def async_analyze_animal(animal: str) -> str:
    prompt = (
        f"In one or two sentences, describe the personality traits, symbolism, "
        f"and psychological meaning commonly associated with a '{animal}'. "
        f"Focus on how this animal might represent a person's character or behavior."
    )
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    if hasattr(response, "content"):
        return response.content.strip()
    return str(response)


@mcp.tool()
async def animal_personality_conversation(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Conversational animal personality quiz tool for MCP/Claude integration.

    Args:
        input_data (Dict[str, Any]):
            {
                "state": {"first": str|None, "second": str|None, "third": str|None},
                "answer": str|None
            }
    Returns:
        Dict[str, Any]:
            If not all answers collected:
                {"next_question": str, "state": {...}}
            If all answers collected:
                {"analysis": {...}, "summary": str, "state": {...}}
    """
    state = input_data.get("state", {"first": None, "second": None, "third": None})
    answer = input_data.get("answer")

    # Update state with the latest answer
    if state["first"] is None and answer:
        state["first"] = answer
    elif state["second"] is None and answer:
        state["second"] = answer
    elif state["third"] is None and answer:
        state["third"] = answer

    # Determine next step
    if state["first"] is None:
        return {"next_question": QUESTIONS[0], "state": state}
    if state["second"] is None:
        return {"next_question": QUESTIONS[1], "state": state}
    if state["third"] is None:
        return {"next_question": QUESTIONS[2], "state": state}

    # All answers collected: generate analysis
    first, second, third = state["first"], state["second"], state["third"]
    external = await async_analyze_animal(first)
    internal = await async_analyze_animal(second)
    actual = await async_analyze_animal(third)

    analysis = {
        "external_perception": {
            "animal": first,
            "meaning": external,
            "description": "How you want others to perceive you.",
        },
        "internal_perception": {
            "animal": second,
            "meaning": internal,
            "description": "How you really perceive yourself.",
        },
        "actual_behavior": {
            "animal": third,
            "meaning": actual,
            "description": "How you actually show up in the world.",
        },
    }
    summary = (
        f"You want to be seen as a {first} (external), "
        f"feel like a {second} (internal), "
        f"and actually behave like a {third} (actual). "
        "See detailed analysis above."
    )
    return {"analysis": analysis, "summary": summary, "state": state}


if __name__ == "__main__":
    mcp.run(transport="stdio")
