"""
ReaConnect Chat API — Main Application Entry Point

This file is the "front door" of the entire backend. It:
1. Loads environment variables (like API keys)
2. Creates the FastAPI application
3. Registers all the routers (URL handlers)
4. Runs the server when executed directly

Think of this like the reception area of a building:
- It's where everyone enters first
- It directs people to the right department (router)
- It handles opening and closing the building (lifespan)

The actual work happens in the other packages:
- routers/  → handle incoming requests (the "front doors")
- services/ → do the heavy lifting (the "kitchen")
- models/   → define data shapes (the "forms")
- helpers/  → business logic helpers (the "receptionist")
- utils/    → small reusable tools (the "toolbox")
- tools/    → MCP tools server (the real estate data tools)
"""

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

from services import chat_history
from routers import chat, health


# ---------------------------------------------------------------------------
# Load environment variables from backend/.env
# ---------------------------------------------------------------------------
# dotenv reads the .env file and puts the values into the environment,
# so os.environ["OPENAI_API_KEY"] will work after this line.
# Path(__file__) is this file → .parent is backend/src/ → .parent is backend/
_ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH)


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
# Register routers — connect all the "departments" to the main building
# ---------------------------------------------------------------------------
# include_router() is like plugging in an extension cord — it connects
# all the URLs defined in that router to our main app.
app.include_router(chat.router)    # adds /api/v1/chat and /api/v1/chat/stream
app.include_router(health.router)  # adds /health


# ---------------------------------------------------------------------------
# Run the server directly with: python app.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    # uvicorn is the server that runs our FastAPI app.
    # Think of it like the engine that powers the car (FastAPI is the car).
    uvicorn.run(
        "app:app",        # "filename:variable_name" of the FastAPI app
        host="0.0.0.0",   # listen on all network interfaces
        port=8000,        # port number (like a door number on a building)
        reload=True,      # auto-restart when you save changes (great for development)
    )
