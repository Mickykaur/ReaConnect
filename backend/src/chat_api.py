"""
ReaConnect Chat API — POST /api/v1/chat

This is the "front door" of our AI chat system. Here's the big picture:

1. A user sends a message like "What homes are under $400k in Texas?"
2. We look up their past messages from SQLite (so the AI remembers context)
3. We spin up a connection to our MCP server (the real estate data tools)
4. We create a LangGraph ReAct agent armed with those tools
5. The agent thinks, calls tools if needed, and writes a reply
6. We save both the user's message and the AI's reply to SQLite
7. We send the reply back to the user

Think of the agent like a smart research assistant:
- You ask a question
- They look things up in the database (using the MCP tools)
- They write you a clear answer
- They remember what you talked about before
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

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
    command="python",          # run Python
    args=[_SERVER_SCRIPT],     # with our server.py script
    env=None,                  # inherit the current environment (includes OPENAI_API_KEY)
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
    What we send back to the caller.
    """
    # The AI's reply text
    reply: str = Field(description="The AI assistant's response")

    # Always returned so the caller can use it in the next request
    conversation_id: str = Field(
        description="The conversation ID — save this to continue the conversation later"
    )


# ---------------------------------------------------------------------------
# The main chat endpoint
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
    Handle a chat message and return the AI's reply.

    Step-by-step walkthrough:
    1. Figure out which conversation this belongs to (new or existing)
    2. Load past messages from SQLite
    3. Connect to the MCP server (our real estate data tools)
    4. Build the LangGraph agent with those tools
    5. Run the agent with the full conversation history
    6. Save the new messages to SQLite
    7. Return the reply
    """

    # ------------------------------------------------------------------
    # Step 1: Resolve the conversation ID
    # ------------------------------------------------------------------
    if request.conversation_id is None:
        # No ID provided → start a fresh conversation
        conversation_id = chat_history.create_conversation()
    else:
        # ID provided → make sure it actually exists in our database
        if not chat_history.conversation_exists(request.conversation_id):
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Conversation '{request.conversation_id}' not found. "
                    "Start a new conversation by omitting the conversation_id field."
                ),
            )
        conversation_id = request.conversation_id

    # ------------------------------------------------------------------
    # Step 2: Load past messages from SQLite
    # ------------------------------------------------------------------
    # history is a list like:
    # [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    history = chat_history.get_history(conversation_id)

    # ------------------------------------------------------------------
    # Step 3 & 4: Connect to MCP server and build the agent
    # ------------------------------------------------------------------
    # We use "async with" so the MCP connection is automatically closed
    # when we're done — like automatically hanging up the phone.
    try:
        async with stdio_client(MCP_SERVER_PARAMS) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:

                # Shake hands with the MCP server (required before using tools)
                await session.initialize()

                # Convert the MCP server's tools into LangChain-compatible tools
                # Think of this like translating a foreign language menu into English
                tools = await load_mcp_tools(session)

                # Create the LLM (Large Language Model) — the AI brain
                # ChatOpenAI reads OPENAI_API_KEY from the environment automatically
                llm = ChatOpenAI(
                    model="gpt-4.1",   # powerful and cost-effective model
                    temperature=0,     # 0 = deterministic (less random, more factual)
                )

                # Create the ReAct agent
                # "ReAct" stands for "Reason + Act" — the agent thinks step by step,
                # decides whether to call a tool, calls it, reads the result, and repeats
                # until it has a final answer.
                agent = create_react_agent(
                    model=llm,
                    tools=tools,
                    prompt=(
                        "You are a helpful real estate assistant for ReaConnect. "
                        "You have access to tools that let you query real estate listing data. "
                        "Always use the tools to look up actual data before answering questions "
                        "about listings, prices, or availability. "
                        "Be concise and helpful."
                    ),
                )

                # ----------------------------------------------------------
                # Step 5: Build the full message list and run the agent
                # ----------------------------------------------------------
                # We combine the past history with the new user message.
                # The agent sees the whole conversation so it has context.
                messages_for_agent = history + [
                    {"role": "user", "content": request.message}
                ]

                # ainvoke = "async invoke" — runs the agent without blocking
                # other requests while it's thinking
                result = await agent.ainvoke({"messages": messages_for_agent})

                # The agent returns a dict with a "messages" list.
                # The last message in that list is the AI's final reply.
                agent_messages = result["messages"]
                final_message = agent_messages[-1]

                # Extract the text content from the reply
                # (LangChain message objects have a .content attribute)
                reply_text = final_message.content

    except HTTPException:
        # Re-raise HTTP errors (like 404) without wrapping them
        raise
    except Exception as error:
        # Something went wrong with the MCP connection or the agent
        # We raise a 500 error (Internal Server Error) with a helpful message
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(error)}",
        )

    # ------------------------------------------------------------------
    # Step 6: Save both messages to SQLite
    # ------------------------------------------------------------------
    # Save the user's message first, then the AI's reply
    chat_history.save_message(conversation_id, "user", request.message)
    chat_history.save_message(conversation_id, "assistant", reply_text)

    # ------------------------------------------------------------------
    # Step 7: Return the response
    # ------------------------------------------------------------------
    return ChatResponse(
        reply=reply_text,
        conversation_id=conversation_id,
    )


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
