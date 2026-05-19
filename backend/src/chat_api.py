"""
ReaConnect Chat API — POST /api/v1/chat and /api/v1/chat/stream

This is the "front door" of our AI chat system. Here's the big picture:

1. A user sends a message like "What homes are under $400k in Texas?"
2. We look up their past messages from SQLite (so the AI remembers context)
3. We spin up a connection to our MCP server (the real estate data tools)
4. We create a LangGraph ReAct agent armed with those tools
5. The agent thinks, calls tools if needed, and writes a reply
6. We save both the user's message and the AI's reply to SQLite
7. We send the reply back to the user

The /api/v1/chat/stream endpoint does the SAME thing but sends updates
in real-time using Server-Sent Events (SSE). Think of SSE like a radio
broadcast — the backend keeps talking and the frontend keeps listening,
so the user can see tool calls happening live instead of staring at a spinner.
"""

import json
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

import chat_history


# ---------------------------------------------------------------------------
# Load environment variables from backend/.env
# ---------------------------------------------------------------------------
# dotenv reads the .env file and puts the values into the environment,
# so os.environ["OPENAI_API_KEY"] will work after this line.
# Path(__file__) is this file → .parent is backend/src/ → .parent is backend/
_ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH)


# ---------------------------------------------------------------------------
# MCP server configuration
# ---------------------------------------------------------------------------
# This tells the MCP client how to launch our server.py as a subprocess.
# "stdio" means the two processes talk to each other through standard input/output
# (like two people passing notes through a slot in a wall).
_SERVER_SCRIPT = str(Path(__file__).parent / "server.py")

MCP_SERVER_PARAMS = StdioServerParameters(
    command=sys.executable,    # use the SAME Python that's running this app (from the venv)
    args=[_SERVER_SCRIPT],     # with our server.py script
    env=None,                  # inherit the current environment (includes OPENAI_API_KEY)
)


# ---------------------------------------------------------------------------
# Shared constants — the system prompt for our AI agent
# ---------------------------------------------------------------------------
# We define this once so both /chat and /chat/stream use the exact same
# instructions. DRY = "Don't Repeat Yourself" — a coding best practice.
SYSTEM_PROMPT = (
    "You are a helpful real estate assistant for ReaConnect. "
    "You have access to tools that let you query real estate listing data. "
    "Always use the tools to look up actual data before answering questions "
    "about listings, prices, or availability. "
    "Be concise and helpful."
)


# ---------------------------------------------------------------------------
# FastAPI app lifecycle — runs setup code when the server starts
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Code inside the 'async with' block runs when the server starts up.
    Code after 'yield' runs when the server shuts down.

    Think of this like opening and closing a shop:
    - Before yield = opening the shop (set up tables, turn on lights)
    - After yield  = closing the shop (clean up)
    """
    # Create the SQLite tables if they don't exist yet
    chat_history.initialize_database()
    print("✅ Chat history database initialized")
    yield
    # Nothing special needed on shutdown for SQLite


# ---------------------------------------------------------------------------
# Create the FastAPI application
# ---------------------------------------------------------------------------
# FastAPI is the web framework — it handles incoming HTTP requests and
# routes them to the right function.
app = FastAPI(
    title="ReaConnect Chat API",
    description="AI-powered real estate chat using LangGraph + MCP tools",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Request and Response models (the shape of data coming in and going out)
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    """
    What the caller must send in the request body (as JSON).

    Think of this like a form the user fills out before talking to the AI.
    """
    # The user's message — required, cannot be empty
    message: str = Field(
        ...,
        min_length=1,
        description="The user's message to the AI assistant",
        examples=["What homes are available in Texas under $400k?"],
    )

    # Optional: if provided, we continue an existing conversation.
    # If omitted (None), we start a brand-new conversation.
    conversation_id: str | None = Field(
        default=None,
        description=(
            "ID of an existing conversation to continue. "
            "Leave empty to start a new conversation."
        ),
        examples=["3f2a1b4c-1234-5678-abcd-ef0123456789"],
    )


class ChatResponse(BaseModel):
    """
    What we send back to the caller (for the non-streaming endpoint).
    """
    # The AI's reply text
    reply: str = Field(description="The AI assistant's response")

    # Always returned so the caller can use it in the next request
    conversation_id: str = Field(
        description="The conversation ID — save this to continue the conversation later"
    )


# ---------------------------------------------------------------------------
# Helper: resolve conversation ID (used by both endpoints)
# ---------------------------------------------------------------------------
def _resolve_conversation_id(conversation_id: str | None) -> str:
    """
    Figure out which conversation this message belongs to.

    If no ID was given, start a new conversation (like opening a new page
    in a notepad). If an ID was given, make sure it exists in our database.

    Returns the valid conversation ID string.
    Raises HTTPException(404) if the given ID doesn't exist.
    """
    if conversation_id is None:
        # No ID provided → start a fresh conversation
        return chat_history.create_conversation()

    # ID provided → make sure it actually exists in our database
    if not chat_history.conversation_exists(conversation_id):
        raise HTTPException(
            status_code=404,
            detail=(
                f"Conversation '{conversation_id}' not found. "
                "Start a new conversation by omitting the conversation_id field."
            ),
        )
    return conversation_id


# ---------------------------------------------------------------------------
# Original (non-streaming) chat endpoint — kept for backwards compatibility
# ---------------------------------------------------------------------------

@app.post(
    "/api/v1/chat",
    response_model=ChatResponse,
    summary="Send a message to the ReaConnect AI assistant",
    description=(
        "Send a message and get an AI-powered reply. "
        "The AI has access to real estate listing tools and remembers your conversation history."
    ),
)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Handle a chat message and return the AI's reply (all at once, no streaming).

    Step-by-step walkthrough:
    1. Figure out which conversation this belongs to (new or existing)
    2. Load past messages from SQLite
    3. Connect to the MCP server (our real estate data tools)
    4. Build the LangGraph agent with those tools
    5. Run the agent with the full conversation history
    6. Save the new messages to SQLite
    7. Return the reply
    """

    # Step 1: Resolve the conversation ID
    conversation_id = _resolve_conversation_id(request.conversation_id)

    # Step 2: Load past messages from SQLite
    history = chat_history.get_history(conversation_id)

    # Steps 3-5: Connect to MCP, build agent, run it
    try:
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

                messages_for_agent = history + [
                    {"role": "user", "content": request.message}
                ]

                result = await agent.ainvoke({"messages": messages_for_agent})
                agent_messages = result["messages"]
                final_message = agent_messages[-1]
                reply_text = final_message.content

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(error)}",
        )

    # Step 6: Save both messages to SQLite
    chat_history.save_message(conversation_id, "user", request.message)
    chat_history.save_message(conversation_id, "assistant", reply_text)

    # Step 7: Return the response
    return ChatResponse(
        reply=reply_text,
        conversation_id=conversation_id,
    )


# ---------------------------------------------------------------------------
# NEW: Streaming chat endpoint using Server-Sent Events (SSE)
# ---------------------------------------------------------------------------
#
# SSE (Server-Sent Events) is a way for the server to send a STREAM of
# messages to the browser, one at a time. Think of it like a news ticker
# on TV — new headlines keep scrolling in as they happen.
#
# Each SSE message looks like this:
#   data: {"type": "tool_call", "name": "query_listings", ...}\n\n
#
# The "\n\n" (two newlines) is how the browser knows one message ended
# and the next is about to start. It's like pressing "Enter" twice
# between paragraphs.
#
# We send these event types:
#   - "conversation_id" → so the frontend knows which conversation this is
#   - "tool_call"       → the agent decided to call a tool (e.g. query_listings)
#   - "tool_result"     → the tool finished and returned data
#   - "text"            → a chunk of the AI's final text response
#   - "done"            → signals that the stream is complete
#   - "error"           → something went wrong
# ---------------------------------------------------------------------------

@app.post(
    "/api/v1/chat/stream",
    summary="Send a message and get a STREAMING response",
    description=(
        "Same as /api/v1/chat but streams responses using Server-Sent Events. "
        "You'll see tool calls and results in real-time as the agent works."
    ),
)
async def chat_stream(request: ChatRequest):
    """
    Handle a chat message and stream the AI's thought process + reply.

    Instead of waiting for the agent to finish everything and then sending
    one big response, we send little updates as they happen:
    - "I'm calling the query_listings tool..."
    - "The tool returned 15 results..."
    - "Here are the homes under $400k in Texas..."

    This uses LangGraph's astream_events() method, which is like putting
    a microphone on the agent so we can hear everything it does.
    """

    # Step 1: Resolve conversation ID (before we start streaming)
    # We do this BEFORE entering the generator because if it fails with
    # a 404 error, we want FastAPI to handle it normally (not inside the stream).
    conversation_id = _resolve_conversation_id(request.conversation_id)

    # Step 2: Load past messages
    history = chat_history.get_history(conversation_id)

    # Step 3: Define the generator function that produces SSE events
    # A "generator" is like a conveyor belt in a factory — it produces
    # items one at a time instead of making everything at once.
    async def event_generator():
        """
        This async generator yields SSE-formatted strings.
        Each yield sends one event to the frontend.
        """
        # We'll collect the final reply text as chunks come in
        final_reply_chunks = []

        try:
            # --- Send the conversation ID first ---
            # The frontend needs this to continue the conversation later
            yield _format_sse_event({
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
                        {"role": "user", "content": request.message}
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
                        # call a tool (like query_listings or list_available_weeks).
                        if kind == "on_tool_start":
                            # event["name"] = the tool's name (e.g. "query_listings")
                            # event["data"]["input"] = the arguments the agent passed
                            tool_name = event.get("name", "unknown_tool")
                            tool_input = event.get("data", {}).get("input", {})

                            yield _format_sse_event({
                                "type": "tool_call",
                                "name": tool_name,
                                "input": tool_input,
                            })

                        # ----- Tool call finished -----
                        # "on_tool_end" fires when the tool returns its result.
                        elif kind == "on_tool_end":
                            tool_name = event.get("name", "unknown_tool")
                            tool_output = event.get("data", {}).get("output", "")

                            # The tool output might be a LangChain ToolMessage object
                            # or a plain string. We need to handle both cases.
                            if hasattr(tool_output, "content"):
                                # It's a ToolMessage object — grab the .content
                                output_text = tool_output.content
                            else:
                                # It's already a string or dict
                                output_text = str(tool_output)

                            # Truncate very long tool outputs for the stream
                            # (the full data is still used by the agent internally)
                            display_output = _truncate_output(output_text, max_length=500)

                            yield _format_sse_event({
                                "type": "tool_result",
                                "name": tool_name,
                                "output": display_output,
                            })

                        # ----- AI text being generated (token by token) -----
                        # "on_chat_model_stream" fires for each chunk of text
                        # the AI produces. We only want the FINAL answer,
                        # not the intermediate "thinking" text.
                        elif kind == "on_chat_model_stream":
                            # We check the tags to make sure this is from the
                            # final response and not from an internal step.
                            chunk = event.get("data", {}).get("chunk", None)
                            if chunk and hasattr(chunk, "content") and chunk.content:
                                # Only stream text content (skip tool_use chunks)
                                if isinstance(chunk.content, str):
                                    final_reply_chunks.append(chunk.content)
                                    yield _format_sse_event({
                                        "type": "text",
                                        "content": chunk.content,
                                    })

            # --- After streaming is done, save to database ---
            final_reply = "".join(final_reply_chunks)

            # Save the user's message and the AI's complete reply
            chat_history.save_message(conversation_id, "user", request.message)
            if final_reply:
                chat_history.save_message(conversation_id, "assistant", final_reply)

            # --- Send the "done" signal ---
            yield _format_sse_event({
                "type": "done",
            })

        except Exception as error:
            # If anything goes wrong, send an error event
            logger.exception("Streaming error")
            yield _format_sse_event({
                "type": "error",
                "message": str(error),
            })

    # Step 4: Return a StreamingResponse with the SSE content type
    # "text/event-stream" tells the browser "this is an SSE stream"
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            # These headers make sure nothing between us and the browser
            # tries to buffer/cache the stream (which would defeat the purpose)
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # tells nginx not to buffer
        },
    )


# ---------------------------------------------------------------------------
# Helper functions for SSE formatting
# ---------------------------------------------------------------------------

def _format_sse_event(data: dict) -> str:
    """
    Format a dictionary as an SSE event string.

    SSE format requires each event to start with "data: " and end with
    two newlines. It's like writing a postcard — there's a specific format
    the postal service (browser) expects.

    Input:  {"type": "text", "content": "Hello"}
    Output: 'data: {"type": "text", "content": "Hello"}\n\n'
    """
    # json.dumps converts our Python dict to a JSON string
    json_string = json.dumps(data, default=str)
    return f"data: {json_string}\n\n"


def _truncate_output(text: str, max_length: int = 500) -> str:
    """
    Shorten very long tool outputs for display in the stream.

    The agent still sees the FULL output internally — we only shorten
    what we send to the frontend for display. It's like summarizing
    a long report: the researcher reads the whole thing, but tells
    you just the highlights.

    Args:
        text: The full tool output text
        max_length: Maximum characters to keep (default 500)

    Returns:
        The original text if short enough, or a truncated version
        with "... (truncated)" appended.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + "... (truncated)"


# ---------------------------------------------------------------------------
# Health check endpoint — useful for checking if the server is running
# ---------------------------------------------------------------------------

@app.get("/health", summary="Health check")
async def health_check() -> dict:
    """
    Simple endpoint to verify the API is running.
    Returns {"status": "ok"} if everything is fine.
    """
    return {"status": "ok", "service": "ReaConnect Chat API"}


# ---------------------------------------------------------------------------
# Run the server directly with: python chat_api.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    # uvicorn is the server that runs our FastAPI app.
    # Think of it like the engine that powers the car (FastAPI is the car).
    uvicorn.run(
        "chat_api:app",   # "filename:variable_name" of the FastAPI app
        host="0.0.0.0",   # listen on all network interfaces
        port=8000,        # port number (like a door number on a building)
        reload=True,      # auto-restart when you save changes (great for development)
    )
