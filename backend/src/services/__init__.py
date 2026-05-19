"""
Services package — the heavy-lifting layer that does the real work.

Think of services like the kitchen in a restaurant:
- The router (waiter) takes the order from the customer
- The service (chef) actually cooks the food
- The router brings the finished dish back to the customer

Services contain the core business logic:
- chat_history   → manages conversation storage in SQLite
- agent_service  → connects to AI agent and runs it
- data_loader    → loads CSV real estate data files
- query_engine   → filters and sorts listing data
"""

from services.agent_service import run_agent, stream_agent_events
from services import chat_history

__all__ = ["run_agent", "stream_agent_events", "chat_history"]
