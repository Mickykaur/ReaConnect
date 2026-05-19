"""
SSE (Server-Sent Events) utility functions.

SSE is a way for the server to send a STREAM of messages to the browser,
one at a time. Think of it like a news ticker on TV — new headlines keep
scrolling in as they happen.

Each SSE message looks like this:
    data: {"type": "tool_call", "name": "query_listings", ...}\\n\\n

The "\\n\\n" (two newlines) is how the browser knows one message ended
and the next is about to start. It's like pressing "Enter" twice
between paragraphs.
"""

import json


def format_sse_event(data: dict) -> str:
    """
    Format a dictionary as an SSE event string.

    SSE format requires each event to start with "data: " and end with
    two newlines. It's like writing a postcard — there's a specific format
    the postal service (browser) expects.

    Args:
        data: A Python dictionary to send as JSON.

    Returns:
        A properly formatted SSE string.

    Example:
        Input:  {"type": "text", "content": "Hello"}
        Output: 'data: {"type": "text", "content": "Hello"}\\n\\n'
    """
    # json.dumps converts our Python dict to a JSON string.
    # default=str handles any objects that aren't normally JSON-serializable
    # (like dates) by converting them to strings.
    json_string = json.dumps(data, default=str)
    return f"data: {json_string}\n\n"


def truncate_output(text: str, max_length: int = 500) -> str:
    """
    Shorten very long tool outputs for display in the stream.

    The agent still sees the FULL output internally — we only shorten
    what we send to the frontend for display. It's like summarizing
    a long report: the researcher reads the whole thing, but tells
    you just the highlights.

    Args:
        text: The full tool output text.
        max_length: Maximum characters to keep (default 500).

    Returns:
        The original text if short enough, or a truncated version
        with "... (truncated)" appended.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + "... (truncated)"
