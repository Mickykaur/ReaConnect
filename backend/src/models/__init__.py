"""
Models package — defines the "shapes" of data flowing in and out of our API.

Think of models like forms:
- ChatRequest = the form the user fills out to send a message
- ChatResponse = the form we fill out to send a reply back

Pydantic models automatically check that the data is valid
(like a form that rejects blank fields).
"""

from models.chat import ChatRequest, ChatResponse

# This line lets other files do: from models import ChatRequest, ChatResponse
# instead of: from models.chat import ChatRequest, ChatResponse
__all__ = ["ChatRequest", "ChatResponse"]
