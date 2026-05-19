"""
Utils package — small, reusable helper tools.

Think of utils like the tools in a toolbox (screwdriver, wrench, etc.).
Each one does ONE simple job and can be used anywhere in the project.

- format_sse_event: Formats data for Server-Sent Events (real-time streaming)
- truncate_output: Shortens long text for display
"""

from utils.sse import format_sse_event, truncate_output

__all__ = ["format_sse_event", "truncate_output"]
