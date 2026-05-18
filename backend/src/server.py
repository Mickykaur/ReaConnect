"""FastMCP server for ReaConnect real estate data."""

import os
from pathlib import Path
import json

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from data_loader import DataLoader
from query_engine import QueryEngine, build_filter_dict


# Initialize FastMCP server
mcp = FastMCP("reaconnect-listings", "1.0.0")

# Initialize data and query components
# Determine data directory relative to this script
DATA_DIR = Path(__file__).parent.parent / "data"
loader = DataLoader(str(DATA_DIR))
engine = QueryEngine()


# ============================================================================
# Tool Input Models (Pydantic)
# ============================================================================

class GetDataSchemaInput(BaseModel):
    """Input for get_data_schema tool."""
    week: str = Field(..., description="Week in format YYYY-MM-DD (e.g., '2022-06-26')")


class QueryListingsFilterDict(BaseModel):
    """Flexible filter specification."""
    class Config:
        extra = "allow"  # Allow any fields for custom filters


class QueryListingsSortSpec(BaseModel):
    """Sort specification."""
    column: str = Field(..., description="Column name to sort by")
    direction: str = Field(
        default="asc",
        description="Sort direction: 'asc' or 'desc'"
    )


class QueryListingsInput(BaseModel):
    """Input for query_listings tool."""
    week: str = Field(..., description="Week in format YYYY-MM-DD (e.g., '2022-06-26')")
    filters: dict = Field(
        default_factory=dict,
        description=(
            "Filter conditions as a dict. Examples: "
            "{'homeData.addressInfo.state': 'AL'}, "
            "{'homeData.priceInfo.amount.value': {'min': 300000, 'max': 500000}}, "
            "{'homeData.beds.value': {'eq': 3}}, "
            "{'homeData.propertyType': {'in': ['SINGLE_FAMILY_RESIDENTIAL', 'CONDO_COOP']}}"
        )
    )
    sort_by: list = Field(
        default_factory=list,
        description=(
            "Sort specifications. Example: "
            "[{'column': 'homeData.priceInfo.amount.value', 'direction': 'asc'}]"
        )
    )
    limit: int = Field(
        default=100,
        description="Maximum rows to return (1-10000, default 100)"
    )


# ============================================================================
# Tools
# ============================================================================

@mcp.tool()
def list_available_weeks() -> dict:
    """
    List all available weeks in the dataset.
    
    Returns a dict with available weeks and count. Use this to discover what time
    periods are available before querying.
    """
    try:
        weeks = loader.get_available_weeks()
        return {
            "success": True,
            "weeks": weeks,
            "count": len(weeks),
            "date_range": f"{weeks[0]} to {weeks[-1]}" if weeks else "No data",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_data_schema(input: GetDataSchemaInput) -> dict:
    """
    Get schema information (columns, data types, sample) for a specific week.
    
    Use this to understand what fields are available before querying.
    """
    try:
        schema = loader.get_schema_for_week(input.week)
        
        # Simplify the response for LLM consumption
        return {
            "success": True,
            "week": input.week,
            "row_count": schema["row_count"],
            "columns": schema["columns"],
            "columns_info": schema["columns_info"],
            "sample_row": schema["sample_row"],
        }
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {e}"}


@mcp.tool()
def query_listings(input: QueryListingsInput) -> dict:
    """
    Query real estate listings for a specific week with optional filtering and sorting.
    
    This is the main tool for querying the dataset. You can:
    - Filter by various criteria (state, city, price, beds, baths, property type, status)
    - Sort results by any column
    - Limit results for pagination
    
    Filter examples:
    - Simple equality: {"homeData.addressInfo.state": "AL"}
    - Price range: {"homeData.priceInfo.amount.value": {"min": 300000, "max": 500000}}
    - Multiple beds: {"homeData.beds.value": {"min": 3}}
    - Property types: {"homeData.propertyType": {"in": ["SINGLE_FAMILY_RESIDENTIAL", "CONDO_COOP"]}}
    - Status: {"homeData.listingMetadata.searchStatus": "ACTIVE"}
    
    Sort examples:
    - [{"column": "homeData.priceInfo.amount.value", "direction": "asc"}]
    - [{"column": "homeData.beds.value", "direction": "desc"}, {"column": "homeData.priceInfo.amount.value", "direction": "asc"}]
    """
    try:
        # Load data for the week
        df = loader.load_csv_for_week(input.week)
        
        # Apply filters
        if input.filters:
            df = engine.apply_filters(df, input.filters)
        
        # Apply sorting
        if input.sort_by:
            df = engine.apply_sort(df, input.sort_by)
        
        # Format response
        response = engine.format_response(df, limit=input.limit)
        response["success"] = True
        response["week"] = input.week
        
        return response
    
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {e}"}


# ============================================================================
# Main entry point
# ============================================================================

if __name__ == "__main__":
    import asyncio
    
    print(f"ReaConnect FastMCP Server")
    print(f"Data directory: {DATA_DIR}")
    print(f"Available weeks: {len(loader.get_available_weeks())}")
    print()
    
    # Start the server
    print("Starting MCP server...")
    mcp.run()
