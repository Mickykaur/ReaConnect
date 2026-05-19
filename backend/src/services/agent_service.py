"""
Agent service — connects to MCP tools and runs the AI agent.

This is the "brain" of the backend. It:
1. Opens a connection to the MCP server (our real estate data tools)
2. Builds a LangGraph ReAct agent (an AI that can think + use tools)
3. Runs the agent with the user's message and conversation history
4. Returns the agent's reply (or streams it in real-time)

Think of this like hiring a research assistant:
- You give them your question and all your past notes (history)
- They have access to reference books (MCP tools)
- They read the books, think, and write you an answer
"""

import logging
from collections.abc import AsyncGenerator

from fastapi import HTTPException
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from mcp import ClientSession
from mcp.client.stdio import stdio_client

from services.chat_history import save_message
from helpers.mcp_config import MCP_SERVER_PARAMS
from utils import format_sse_event, truncate_output

# Logger lets us record what's happening (like a security camera for code).
# If something goes wrong, we can check the logs to see what happened.
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared constants — the system prompt for our AI agent
# ---------------------------------------------------------------------------
# We define this once so both run_agent and stream_agent_events use the
# exact same instructions. DRY = "Don't Repeat Yourself" — a coding
# best practice that means: write it once, use it everywhere.
SYSTEM_PROMPT = (
    "You are a helpful real estate assistant for ReaConnect. "
    "You have access to tools that let you query real estate listing data. "
    "Always use the tools to look up actual data before answering questions "
    "about listings, prices, or availability. "
    "Be concise and helpful."
)


async def run_agent(conversation_id: str, user_message: str, history: list[dict]) -> str:
    """
    Run the AI agent and return its complete reply (no streaming).

    This is the simpler version — we wait for the agent to finish everything,
    then return the full answer. Like ordering food for delivery: you wait,
    and then the complete meal arrives all at once.

    Args:
        conversation_id: Which conversation this belongs to.
        user_message: The user's new message.
        history: List of past messages (so the AI has context).

    Returns:
        The AI agent's reply text.

    Raises:
        HTTPException(500): If the agent encounters an error.
    """
    try:
        # Connect to the MCP server (our real estate data tools)
        # "async with" automatically closes the connection when we're done
        async with stdio_client(MCP_SERVER_PARAMS) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize the MCP session (like shaking hands to start)
                await session.initialize()

                # Load the available tools from the MCP server
                tools = await load_mcp_tools(session)

                # Create the AI model (GPT-4.1, temperature=0 for consistent answers)
                llm = ChatOpenAI(model="gpt-4.1", temperature=0)

                # Build the ReAct agent (an AI that can Reason + Act using tools)
                agent = create_react_agent(
                    model=llm,
                    tools=tools,
                    prompt=SYSTEM_PROMPT,
                )

                # Combine past history with the new user message
                messages_for_agent = history + [
                    {"role": "user", "content": user_message}
                ]

                # Run the agent and get the result
                result = await agent.ainvoke({"messages": messages_for_agent})

                # The last message in the result is the agent's final answer
                agent_messages = result["messages"]
                final_message = agent_messages[-1]
                reply_text = final_message.content

    except HTTPException:
        # Re-raise HTTP exceptions as-is (they already have status codes)
        raise
    except Exception as error:
        # Wrap unexpected errors in a 500 HTTP error
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(error)}",
        )

    # Save both messages to the database
    save_message(conversation_id, "user", user_message)
    save_message(conversation_id, "assistant", reply_text)

    return reply_text


async def stream_agent_events(
    conversation_id: str,
    user_message: str,
    history: list[dict],
) -> AsyncGenerator[str, None]:
    """
    Run the AI agent and STREAM its thought process + reply as SSE events.

    Instead of waiting for the agent to finish everything and then sending
    one big response, we send little updates as they happen:
    - "I'm calling the query_listings tool..."
    - "The tool returned 15 results..."
    - "Here are the homes under $400k in Texas..."

    This is an async generator — think of it like a conveyor belt in a
    factory. It produces items (SSE events) one at a time instead of
    making everything at once.

    Args:
        conversation_id: Which conversation this belongs to.
        user_message: The user's new message.
        history: List of past messages (so the AI has context).

    Yields:
        SSE-formatted strings, one event at a time.
    """
    # We'll collect the final reply text as chunks come in
    final_reply_chunks = []

    try:
        # --- Send the conversation ID first ---
        # The frontend needs this to continue the conversation later
        yield format_sse_event({
            "type": "conversation_id",
            "conversation_id": conversation_id,
        })

        # --- Connect to MCP server and build the agent ---
        async with stdio_client(MCP_SERVER_PARAMS) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)

                llm = ChatOpenAI(model="gpt-4.1", temperature=0)
                agent = create_react_agent(
                    model=llm,
                    tools=tools,
                    prompt=SYSTEM_PROMPT,
                )

                # Build the full message list (history + new message)
                messages_for_agent = history + [
                    {"role": "user", "content": user_message}
                ]

                # --- Stream events from the agent ---
                # astream_events() is the magic method that lets us
                # "listen in" on everything the agent does.
                # version="v2" is the latest event format from LangGraph.
                async for event in agent.astream_events(
                    {"messages": messages_for_agent},
                    version="v2",
                ):
                    # Each event has a "kind" that tells us what happened.
                    # We check the kind and send the right SSE event.
                    kind = event.get("event", "")

                    # ----- Tool call started -----
                    # "on_tool_start" fires when the agent decides to
                    # call a tool (like query_listings).
                    if kind == "on_tool_start":
                        tool_name = event.get("name", "unknown_tool")
                        tool_input = event.get("data", {}).get("input", {})

                        yield format_sse_event({
                            "type": "tool_call",
                            "name": tool_name,
                            "input": tool_input,
                        })

                    # ----- Tool call finished -----
                    # "on_tool_end" fires when the tool returns its result.
                    elif kind == "on_tool_end":
                        tool_name = event.get("name", "unknown_tool")
                        tool_output = event.get("data", {}).get("output", "")

                        # The tool output might be a LangChain ToolMessage
                        # object or a plain string. We handle both cases.
                        if hasattr(tool_output, "content"):
                            output_text = tool_output.content
                        else:
                            output_text = str(tool_output)

                        # Truncate very long outputs for display
                        display_output = truncate_output(output_text, max_length=500)

                        yield format_sse_event({
                            "type": "tool_result",
                            "name": tool_name,
                            "output": display_output,
                        })

                    # ----- AI text being generated (token by token) -----
                    # "on_chat_model_stream" fires for each chunk of text
                    # the AI produces.
                    elif kind == "on_chat_model_stream":
                        chunk = event.get("data", {}).get("chunk", None)
                        if chunk and hasattr(chunk, "content") and chunk.content:
                            # Only stream text content (skip tool_use chunks)
                            if isinstance(chunk.content, str):
                                final_reply_chunks.append(chunk.content)
                                yield format_sse_event({
                                    "type": "text",
                                    "content": chunk.content,
                                })

        # --- After streaming is done, save to database ---
        final_reply = "".join(final_reply_chunks)

        # Save the user's message and the AI's complete reply
        save_message(conversation_id, "user", user_message)
        if final_reply:
            save_message(conversation_id, "assistant", final_reply)

        # --- Send the "done" signal ---
        yield format_sse_event({"type": "done"})

    except Exception as error:
        # If anything goes wrong, send an error event
        logger.exception("Streaming error")
        yield format_sse_event({
            "type": "error",
            "message": str(error),
        })
