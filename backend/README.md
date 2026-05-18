# ReaConnect Backend — FastMCP Server

A **Model Context Protocol (MCP) server** for querying real estate listing data. Designed for AI assistants (Claude, etc.) to access, search, and analyze real estate data from weekly snapshots.

## Overview

The backend exposes three MCP tools:

1. **`list_available_weeks`** — Discover available time periods
2. **`get_data_schema`** — Understand data structure and columns for a week
3. **`query_listings`** — Query listings with filtering, sorting, and pagination

All tools are designed for **LLM consumption** with flexible, expressive query syntax.

## Data

- **Location**: `backend/data/`
- **Format**: Weekly CSV snapshots of real estate listings
- **Coverage**: June 2022 — February 2023 (36 weekly snapshots)
- **Geography**: USA
- **Source**: Real estate market data (nested JSON schema flattened to CSV)

Sample files:
- `USA_2022-06-26.csv` — Snapshot from June 26, 2022
- `USA_2023-02-26.csv` — Snapshot from Feb 26, 2023
- `USA_clean_unique.csv` — Cleaned/deduplicated dataset

### Key Columns (Real Estate Schema)

The CSV has a deeply nested schema. Key columns include:

- **Location**: `homeData.addressInfo.state`, `homeData.addressInfo.city`, `homeData.addressInfo.zip`
- **Pricing**: `homeData.priceInfo.amount.value`, `homeData.priceInfo.priceType`
- **Property**: `homeData.beds.value`, `homeData.baths.value`, `homeData.propertyType`, `homeData.yearBuilt.yearBuilt.value`
- **Condition**: `homeData.listingMetadata.searchStatus` (ACTIVE, PRE_ON_MARKET, etc.)
- **Features**: `homeData.sqftInfo.amount.value`, `homeData.hoaDues.amount.value`, `homeData.daysOnMarket.daysOnMarket.value`
- **Metadata**: `homeData.url`, `homeData.propertyId`, `homeData.listingMetadata.isNewConstruction`

Use `get_data_schema()` to see all columns for a specific week.

## Setup

### Prerequisites

- Python 3.14+
- `uv` package manager (fast Python package installer)

### Installation

```bash
cd backend

# Install dependencies using uv
uv sync

# Or with pip (if uv not available)
pip install -e .
```

This installs:
- `fastmcp` (≥3.3.1) — FastMCP server framework
- `mcp` (1.27.1) — Model Context Protocol library
- `pandas` — Data manipulation
- `pytest` — Testing

## Running the Server

### Start the MCP Server

```bash
cd backend
uv run src/server.py
```

The server will initialize and wait for MCP client connections. Output:

```
ReaConnect FastMCP Server
Data directory: /path/to/backend/data
Available weeks: 36

Starting MCP server...
```

### Use with Claude (via MCP Client)

Add to your `.cursor/settings.json` or VS Code MCP config:

```json
{
  "mcpServers": {
    "reaconnect": {
      "command": "uv",
      "args": ["run", "/path/to/reaconnect/backend/src/server.py"]
    }
  }
}
```

Then Claude can invoke the tools directly.

## Tool Reference

### 1. `list_available_weeks()`

**Purpose**: Discover what weeks of data are available.

**Arguments**: None

**Returns**:
```json
{
  "success": true,
  "weeks": ["2022-06-26", "2022-07-03", ...],
  "count": 36,
  "date_range": "2022-06-26 to 2023-02-26"
}
```

**Example Usage**:
```
Call: list_available_weeks()
→ Returns all 36 available weeks
```

---

### 2. `get_data_schema(week: str)`

**Purpose**: Get column names, data types, and sample data for a specific week.

**Arguments**:
- `week` (string, required): Week in format `YYYY-MM-DD` (e.g., `"2022-06-26"`)

**Returns**:
```json
{
  "success": true,
  "week": "2022-06-26",
  "row_count": 5432,
  "columns": [
    "homeData.addressInfo.state",
    "homeData.priceInfo.amount.value",
    "homeData.beds.value",
    ...
  ],
  "columns_info": {
    "homeData.priceInfo.amount.value": {
      "dtype": "float64",
      "non_null_count": 5421,
      "null_count": 11
    },
    ...
  },
  "sample_row": {
    "homeData.addressInfo.state": "AL",
    "homeData.priceInfo.amount.value": 345000.0,
    "homeData.beds.value": 3.0,
    ...
  }
}
```

**Example Usage**:
```
Call: get_data_schema(week="2022-06-26")
→ Understand what columns/fields are available for that week
```

---

### 3. `query_listings(week, filters, sort_by, limit)`

**Purpose**: Query listings with optional filtering, sorting, and pagination.

**Arguments**:
- `week` (string, required): Week in format `YYYY-MM-DD`
- `filters` (dict, optional): Filter conditions (see below)
- `sort_by` (list, optional): Sort specifications (see below)
- `limit` (int, optional): Max rows to return (default 100, max 10000)

**Filter Syntax**:

Filters support multiple syntaxes:

1. **Simple Equality**:
   ```json
   {
     "homeData.addressInfo.state": "AL"
   }
   ```

2. **Range (min/max)**:
   ```json
   {
     "homeData.priceInfo.amount.value": {
       "min": 300000,
       "max": 500000
     }
   }
   ```

3. **Explicit Equality**:
   ```json
   {
     "homeData.beds.value": {
       "eq": 3
     }
   }
   ```

4. **List Membership (in)**:
   ```json
   {
     "homeData.propertyType": {
       "in": ["SINGLE_FAMILY_RESIDENTIAL", "CONDO_COOP"]
     }
   }
   ```

5. **Combined**:
   ```json
   {
     "homeData.addressInfo.state": "AL",
     "homeData.priceInfo.amount.value": {
       "min": 200000,
       "max": 600000
     },
     "homeData.beds.value": {
       "min": 2
     }
   }
   ```

**Sort Specification**:

```json
{
  "sort_by": [
    {
      "column": "homeData.priceInfo.amount.value",
      "direction": "asc"
    },
    {
      "column": "homeData.beds.value",
      "direction": "desc"
    }
  ]
}
```

Directions: `"asc"` (ascending) or `"desc"` (descending)

**Returns**:
```json
{
  "success": true,
  "week": "2022-06-26",
  "data": [
    {
      "homeData.addressInfo.state": "AL",
      "homeData.addressInfo.city": "Montgomery",
      "homeData.priceInfo.amount.value": 325000.0,
      "homeData.beds.value": 3.0,
      ...
    },
    ...
  ],
  "total_matching": 127,
  "rows_returned": 50,
  "limit": 50,
  "columns": ["homeData.addressInfo.state", ...]
}
```

**Example Queries**:

1. **Find all active listings in Alabama**:
   ```json
   {
     "week": "2022-06-26",
     "filters": {
       "homeData.addressInfo.state": "AL",
       "homeData.listingMetadata.searchStatus": "ACTIVE"
     },
     "limit": 100
   }
   ```

2. **Find 3+ bedroom homes priced $300k–$600k, sorted by price ascending**:
   ```json
   {
     "week": "2022-06-26",
     "filters": {
       "homeData.beds.value": {
         "min": 3
       },
       "homeData.priceInfo.amount.value": {
         "min": 300000,
         "max": 600000
       }
     },
     "sort_by": [
       {
         "column": "homeData.priceInfo.amount.value",
         "direction": "asc"
       }
     ],
     "limit": 50
   }
   ```

3. **Find single-family or condo listings sorted by beds (descending)**:
   ```json
   {
     "week": "2023-02-26",
     "filters": {
       "homeData.propertyType": {
         "in": ["SINGLE_FAMILY_RESIDENTIAL", "CONDO_COOP"]
       }
     },
     "sort_by": [
       {
         "column": "homeData.beds.value",
         "direction": "desc"
       }
     ],
     "limit": 100
   }
   ```

---

## Testing

Run the test suite to verify all components:

```bash
cd backend

# Run all tests
uv run pytest __tests__/test.py -v

# Run specific test class
uv run pytest __tests__/test.py::TestDataLoader -v

# Run with coverage
uv run pytest __tests__/test.py --cov=src
```

### Test Coverage

- **DataLoader**: File discovery, CSV loading, caching, schema introspection
- **QueryEngine**: Filtering (equality, ranges, lists), sorting, response formatting
- **Integration**: Complete query workflows with multiple data weeks

---

## Architecture

```
backend/
├── src/
│   ├── __init__.py
│   ├── server.py           # FastMCP server entry point
│   ├── data_loader.py      # CSV loading and caching (DataLoader class)
│   └── query_engine.py     # Filtering, sorting, formatting (QueryEngine class)
├── data/
│   ├── USA_2022-06-26.csv  # Weekly snapshots
│   ├── USA_2022-07-03.csv
│   └── ...
├── __tests__/
│   └── test.py             # Comprehensive test suite
├── pyproject.toml          # Project config and dependencies
└── README.md               # This file
```

### Core Components

**`DataLoader`** (`src/data_loader.py`):
- Discovers available weeks from CSV filenames
- Loads CSVs on-demand with caching to save memory
- Returns schema info (columns, dtypes, samples)

**`QueryEngine`** (`src/query_engine.py`):
- Applies flexible filters (equality, ranges, list membership)
- Sorts by multiple columns
- Formats responses with metadata

**`FastMCP Server`** (`src/server.py`):
- Registers three tools with the MCP framework
- Handles tool invocation, error handling, and response formatting
- Integrates DataLoader and QueryEngine

---

## Performance Notes

- **On-demand loading**: CSVs are loaded only when queried, reducing startup time and memory
- **Caching**: Once loaded, weeks are cached in memory; subsequent queries reuse cached data
- **Pagination**: Limit results to 10,000 rows max to keep response sizes reasonable
- **Filter efficiency**: Filters are applied before sorting/formatting to minimize data processing

For large result sets, use `limit` and consider filtering to narrower criteria.

---

## Future Enhancements

1. **Multi-week queries**: Tool to compare data across multiple weeks (trends, changes)
2. **Column aliasing**: Shorter names (e.g., `price` → `homeData.priceInfo.amount.value`)
3. **Aggregations**: Statistics tool (avg price per state, count by type, etc.)
4. **Database backend**: Move from in-memory CSVs to SQLite/PostgreSQL for scalability
5. **Caching strategy**: Persist cache to disk; TTL-based invalidation
6. **Rate limiting**: Protect server from excessive queries
7. **Time series analysis**: Tools for trend detection, outlier analysis

---

## Troubleshooting

### Server fails to start

**Problem**: `ModuleNotFoundError: No module named 'fastmcp'`

**Solution**: Ensure dependencies are installed:
```bash
uv sync
```

### Query returns error: "Column not found"

**Problem**: Misspelled or wrong column name

**Solution**: Call `get_data_schema()` first to see available columns for that week

### Query returns empty results

**Problem**: Filters are too restrictive for that week

**Solution**: Try with fewer/broader filters, or inspect a sample with `get_data_schema()`

### Server is slow

**Problem**: Loading very large CSV or too many rows in response

**Solution**: 
- Use `limit` to paginate results
- Add more specific filters to reduce data
- Monitor memory usage

---

## Contributing

When adding new features:
1. Add tests first (TDD)
2. Update this README with new tool documentation
3. Ensure all tests pass: `uv run pytest __tests__/ -v`
4. Follow existing code style and error handling patterns

---

## License

(To be determined based on project policy)
