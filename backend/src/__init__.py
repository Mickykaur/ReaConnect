"""
ReaConnect backend server modules.

This package contains the backend API for ReaConnect, organized into:
- app.py       → Main FastAPI application (entry point)
- routers/     → URL endpoint handlers (chat, health)
- services/    → Core business logic (AI agent)
- models/      → Pydantic data models (request/response shapes)
- helpers/     → Business logic helpers (conversation resolution)
- utils/       → Reusable utility functions (SSE formatting)
- tools/       → MCP server configuration
- chat_history.py → SQLite conversation storage
- server.py    → MCP tools server (real estate data)
"""
