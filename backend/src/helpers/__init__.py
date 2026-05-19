"""
Helpers package — business logic helpers that sit between routers and services.

Think of helpers like a receptionist at a hotel:
- They check your reservation (does this conversation ID exist?)
- They create a new room key if you're a new guest (new conversation)
- They handle problems early (404 if the conversation doesn't exist)
- They know how to connect to the MCP tools server (mcp_config)

Helpers are different from utils:
- Utils = generic tools anyone could use (formatting, truncating)
- Helpers = specific to OUR app's business rules (conversation logic, MCP config)
"""

from helpers.conversation import resolve_conversation_id
from helpers.mcp_config import MCP_SERVER_PARAMS

__all__ = ["resolve_conversation_id", "MCP_SERVER_PARAMS"]
