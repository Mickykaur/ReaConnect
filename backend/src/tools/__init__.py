"""
Tools package — contains the MCP tools server.

The MCP server (server.py) runs as a separate subprocess. It provides
the real estate data tools that our AI agent can use:
- list_available_weeks: See what time periods have data
- get_data_schema: Understand what columns/fields exist
- query_listings: Search and filter real estate listings

Note: The MCP server configuration (how to LAUNCH the server) lives in
helpers/mcp_config.py, since it's a config helper, not a tool itself.
"""
