"""
MCP server configuration — tells the MCP client how to launch our tools server.

This is like writing down the instructions for how to start the tools server:
- WHAT program to run (Python)
- WHICH script to run (server.py)
- WHERE to find it (in the tools/ folder)

"stdio" means the two processes talk to each other through standard
input/output — like two people passing notes through a slot in a wall.
"""

import sys
from pathlib import Path

from mcp import StdioServerParameters


# Path(__file__) = this file (mcp_config.py)
# .parent       = helpers/ folder
# .parent       = src/ folder
# Then we point to server.py inside tools/
_SERVER_SCRIPT = str(Path(__file__).parent.parent / "tools" / "server.py")

# This object tells the MCP client exactly how to start the server process
MCP_SERVER_PARAMS = StdioServerParameters(
    command=sys.executable,    # use the SAME Python that's running this app (from the venv)
    args=[_SERVER_SCRIPT],     # run our tools/server.py script
    env=None,                  # inherit the current environment (includes OPENAI_API_KEY)
)
