"""Quick verification script — run once to confirm everything works."""
import sys
from pathlib import Path

# Add src/ to the path so Python can find our modules
sys.path.insert(0, str(Path(__file__).parent))

# ── Test 1: chat_history ──────────────────────────────────────────────────
from services import chat_history

chat_history.initialize_database()
print("OK  chat_history.py imports and initializes database")
print("    DB file:", chat_history.DB_PATH)

conv_id = chat_history.create_conversation()
print("OK  create_conversation() ->", conv_id)

chat_history.save_message(conv_id, "user", "Hello, test message")
chat_history.save_message(conv_id, "assistant", "Hello back!")
print("OK  save_message() worked for both roles")

history = chat_history.get_history(conv_id)
assert len(history) == 2, f"Expected 2 messages, got {len(history)}"
assert history[0]["role"] == "user"
assert history[1]["role"] == "assistant"
print("OK  get_history() returned", history)

assert chat_history.conversation_exists(conv_id) is True
assert chat_history.conversation_exists("fake-id-000") is False
print("OK  conversation_exists() works correctly")

# ── Test 2: app syntax ───────────────────────────────────────────────────
import app
print("OK  app.py imports without errors")
print("    FastAPI app title:", app.app.title)

print()
print("All checks passed!")
