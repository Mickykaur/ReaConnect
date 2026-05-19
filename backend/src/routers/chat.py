"""
Chat router — handles the /api/v1/chat and /api/v1/chat/stream endpoints.

This is the "front door" for all chat-related requests. When a user sends
a message, the request comes here first. The router's job is simple:
1. Validate the request (is the data shaped correctly?)
2. Resolve the conversation ID (new or existing?)
3. Hand off to the service layer (where the real work happens)
4. Return the result to the user

Think of this like a waiter in a restaurant:
- Takes the order (request)
- Checks the order makes sense (validation)
- Passes it to the kitchen (service)
- Brings the food back (response)
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from services import chat_history
from helpers import resolve_conversation_id
from models import ChatRequest, ChatResponse
from services import run_agent, stream_agent_events


# APIRouter is like a mini-app that handles a group of related URLs.
# We create it here and then "include" it in the main app later.
# prefix="/api/v1" means all URLs in this router start with /api/v1
# tags=["Chat"] groups these endpoints together in the API docs
router = APIRouter(prefix="/api/v1", tags=["Chat"])


# ---------------------------------------------------------------------------
# Non-streaming chat endpoint
# ---------------------------------------------------------------------------
@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a message to the ReaConnect AI assistant",
    description=(
        "Send a message and get an AI-powered reply. "
        "The AI has access to real estate listing tools and remembers "
        "your conversation history."
    ),
)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Handle a chat message and return the AI's reply (all at once, no streaming).

    Step-by-step walkthrough:
    1. Figure out which conversation this belongs to (new or existing)
    2. Load past messages from SQLite
    3. Run the agent (connects to MCP, builds agent, gets reply)
    4. Return the reply
    """
    # Step 1: Resolve the conversation ID
    conversation_id = resolve_conversation_id(request.conversation_id)

    # Step 2: Load past messages from SQLite
    history = chat_history.get_history(conversation_id)

    # Step 3: Run the agent and get the reply
    reply_text = await run_agent(conversation_id, request.message, history)

    # Step 4: Return the response
    return ChatResponse(
        reply=reply_text,
        conversation_id=conversation_id,
    )


# ---------------------------------------------------------------------------
# Streaming chat endpoint using Server-Sent Events (SSE)
# ---------------------------------------------------------------------------
@router.post(
    "/chat/stream",
    summary="Send a message and get a STREAMING response",
    description=(
        "Same as /api/v1/chat but streams responses using Server-Sent Events. "
        "You'll see tool calls and results in real-time as the agent works."
    ),
)
async def chat_stream(request: ChatRequest):
    """
    Handle a chat message and stream the AI's thought process + reply.

    Instead of waiting for the agent to finish and sending one big response,
    we send little updates as they happen (tool calls, results, text chunks).
    """
    # Step 1: Resolve conversation ID BEFORE streaming starts.
    # If this fails with a 404, FastAPI handles the error normally.
    conversation_id = resolve_conversation_id(request.conversation_id)

    # Step 2: Load past messages
    history = chat_history.get_history(conversation_id)

    # Step 3: Return a StreamingResponse that sends SSE events
    # "text/event-stream" tells the browser "this is an SSE stream"
    return StreamingResponse(
        stream_agent_events(conversation_id, request.message, history),
        media_type="text/event-stream",
        headers={
            # These headers make sure nothing between us and the browser
            # tries to buffer/cache the stream (which would defeat the purpose)
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # tells nginx not to buffer
        },
    )
