"""
Conversation helper — resolves and validates conversation IDs.

Before we can chat, we need to know WHICH conversation we're in.
This helper handles two cases:
1. No ID given → start a brand-new conversation (like opening a fresh notepad page)
2. ID given → check it exists in the database (don't let someone use a fake ID)
"""

from fastapi import HTTPException

from services import chat_history


def resolve_conversation_id(conversation_id: str | None) -> str:
    """
    Figure out which conversation this message belongs to.

    If no ID was given, start a new conversation (like opening a new page
    in a notepad). If an ID was given, make sure it exists in our database.

    Args:
        conversation_id: The ID from the request, or None for a new conversation.

    Returns:
        A valid conversation ID string.

    Raises:
        HTTPException(404): If the given ID doesn't exist in the database.
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
