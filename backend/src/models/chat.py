"""
Chat models — the "forms" for chat requests and responses.

These Pydantic models define exactly what data the user must send us
and what data we send back. Pydantic automatically validates everything,
so if someone sends garbage data, they get a clear error message instead
of a crash.

Think of it like ordering at a restaurant:
- ChatRequest = your order form (what do you want?)
- ChatResponse = the receipt (what did you get?)
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """
    What the caller must send in the request body (as JSON).

    Think of this like a form the user fills out before talking to the AI.
    """

    # The user's message — required, cannot be empty
    message: str = Field(
        ...,                # ... means "this field is required"
        min_length=1,       # must be at least 1 character (no blank messages!)
        description="The user's message to the AI assistant",
        examples=["What homes are available in Texas under $400k?"],
    )

    # Optional: if provided, we continue an existing conversation.
    # If omitted (None), we start a brand-new conversation.
    conversation_id: str | None = Field(
        default=None,       # None means "not required"
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
