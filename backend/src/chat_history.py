"""
Chat history service for ReaConnect.

Think of this file like a notepad manager. Every time a user talks to the AI,
we write down what they said and what the AI replied. That way, the next time
they come back, the AI can read the notepad and remember the conversation.

We store everything in SQLite — a simple database that lives in a single file
on disk (like a spreadsheet saved as a file). No separate database server needed!
"""

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Where the database file lives on disk
# ---------------------------------------------------------------------------
# Path(__file__) is the location of THIS file (chat_history.py).
# .parent goes up one folder (to backend/src/).
# .parent again goes up another folder (to backend/).
# Then we put the database file inside a "db" subfolder.
DB_DIR = Path(__file__).parent.parent / "db"
DB_PATH = DB_DIR / "chat_history.db"


def _get_connection() -> sqlite3.Connection:
    """
    Open (or create) the SQLite database and return a connection to it.

    A "connection" is like opening a notebook — you need to open it before
    you can read or write anything. SQLite automatically creates the file
    if it doesn't exist yet.
    """
    # Make sure the db/ folder exists before trying to create the file inside it
    DB_DIR.mkdir(parents=True, exist_ok=True)

    # Connect to the database file. check_same_thread=False lets FastAPI's
    # async workers share the connection safely.
    connection = sqlite3.connect(str(DB_PATH), check_same_thread=False)

    # row_factory makes rows come back as dict-like objects instead of plain
    # tuples, so we can do row["role"] instead of row[0].
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database() -> None:
    """
    Create the database tables if they don't already exist.

    Think of this like drawing the columns on a blank spreadsheet before
    you start filling in rows. We call this once when the app starts up.

    Tables we create:
    - conversations: one row per chat session (like a new phone call)
    - messages: one row per message inside a conversation
    """
    connection = _get_connection()

    # cursor is like a pen — we use it to write SQL commands
    cursor = connection.cursor()

    # --- Table 1: conversations ---
    # Each conversation gets a unique ID (like a ticket number) and a timestamp.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id         TEXT PRIMARY KEY,   -- unique ID, e.g. "abc-123"
            created_at TEXT NOT NULL       -- when the conversation started
        )
    """)

    # --- Table 2: messages ---
    # Each message belongs to a conversation (via conversation_id).
    # role is either "user" (the human) or "assistant" (the AI).
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,  -- auto-numbered 1, 2, 3...
            conversation_id TEXT    NOT NULL,                   -- which conversation this belongs to
            role            TEXT    NOT NULL,                   -- "user" or "assistant"
            content         TEXT    NOT NULL,                   -- the actual message text
            created_at      TEXT    NOT NULL,                   -- when this message was sent
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        )
    """)

    # Save the changes and close the connection
    connection.commit()
    connection.close()


def create_conversation() -> str:
    """
    Start a brand-new conversation and return its unique ID.

    Think of this like opening a new page in the notepad and writing a
    page number at the top. We return that page number so the caller
    can reference it later.

    Returns:
        A unique conversation ID string (e.g. "3f2a1b4c-...")
    """
    # uuid4() generates a random unique ID — like a lottery ticket number
    conversation_id = str(uuid.uuid4())

    # Record the current time in UTC (a universal timezone so there's no confusion)
    now = datetime.now(timezone.utc).isoformat()

    connection = _get_connection()
    cursor = connection.cursor()

    # Insert a new row into the conversations table
    cursor.execute(
        "INSERT INTO conversations (id, created_at) VALUES (?, ?)",
        (conversation_id, now),
    )

    connection.commit()
    connection.close()

    return conversation_id


def save_message(conversation_id: str, role: str, content: str) -> None:
    """
    Save a single message to the database.

    Think of this like writing one line in the notepad:
    "User said: 'What homes are in Texas?'"
    or
    "AI said: 'Here are the listings...'"

    Args:
        conversation_id: Which conversation this message belongs to
        role:            "user" (the human) or "assistant" (the AI)
        content:         The actual text of the message
    """
    # Validate role — only "user" and "assistant" are allowed
    if role not in ("user", "assistant"):
        raise ValueError(f"role must be 'user' or 'assistant', got: '{role}'")

    now = datetime.now(timezone.utc).isoformat()

    connection = _get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO messages (conversation_id, role, content, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (conversation_id, role, content, now),
    )

    connection.commit()
    connection.close()


def get_history(conversation_id: str) -> list[dict]:
    """
    Fetch all messages for a conversation, in the order they were sent.

    Think of this like flipping back to a page in the notepad and reading
    everything written there from top to bottom.

    Args:
        conversation_id: The ID of the conversation to look up

    Returns:
        A list of dicts, each with "role" and "content" keys.
        Example:
        [
            {"role": "user",      "content": "What homes are in Texas?"},
            {"role": "assistant", "content": "Here are the listings..."},
        ]
    """
    connection = _get_connection()
    cursor = connection.cursor()

    # ORDER BY id ASC means oldest messages come first (chronological order)
    cursor.execute(
        """
        SELECT role, content
        FROM messages
        WHERE conversation_id = ?
        ORDER BY id ASC
        """,
        (conversation_id,),
    )

    # Convert each sqlite3.Row into a plain Python dict
    rows = [{"role": row["role"], "content": row["content"]} for row in cursor.fetchall()]

    connection.close()
    return rows


def conversation_exists(conversation_id: str) -> bool:
    """
    Check whether a conversation ID actually exists in the database.

    This is like checking whether a page number exists in the notepad
    before trying to read it — we don't want to crash if someone sends
    a made-up ID.

    Args:
        conversation_id: The ID to check

    Returns:
        True if it exists, False if it doesn't
    """
    connection = _get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT 1 FROM conversations WHERE id = ?",
        (conversation_id,),
    )

    exists = cursor.fetchone() is not None
    connection.close()
    return exists
