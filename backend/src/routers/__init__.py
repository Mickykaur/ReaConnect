"""
Routers package — the "front doors" of our API.

Think of routers like the entrance doors to different departments in a store:
- /api/v1/chat       → the chat department (talk to the AI)
- /api/v1/chat/stream → the chat department with live updates
- /health            → the information desk (is the store open?)

Each router file handles one group of related URLs.
The main app (app.py) includes all routers so they work together.
"""
