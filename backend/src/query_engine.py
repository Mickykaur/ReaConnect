"""Query filtering, sorting, and response formatting for listing data."""

from typing import Any, Optional
import pandas as pd


class QueryEngine:
    """Handles filtering, sorting, and formatting of listing queries."""
    
    def apply_filters(self, df: pd.DataFrame, filters: Optional[dict]) -> pd.DataFrame:
        """
        Apply filters to a DataFrame.
        
        Supports flexible filter syntax:
        - Simple equality: {"state": "AL"}
        - Comparison operators: {"price": {"min": 300000, "max": 500000}}
        - List membership: {"property_type": {"in": ["SINGLE_FAMILY_RESIDENTIAL", "CONDO_COOP"]}}
        - Explicit equality: {"beds": {"eq": 3}}
        
        Args:
            df: Input DataFrame
            filters: Dict of column -> filter condition. None or empty dict means no filtering.
        
        Returns:
            Filtered DataFrame
            
        Raises:
            ValueError: If column doesn't exist or filter syntax is invalid
        """
        if not filters:
            return df
        
        result_df = df.copy()
        
        for column, condition in filters.items():
            # Check column exists
            if column not in result_df.columns:
                raise ValueError(
                    f"Column '{column}' not found in data. Available columns: {list(result_df.columns)}"
                )
            
            # Handle different condition formats
            if isinstance(condition, dict):
                # Operator-based filtering
                if "min" in condition:
                    result_df = result_df[result_df[column] >= condition["min"]]
                if "max" in condition:
                    result_df = result_df[result_df[column] <= condition["max"]]
                if "eq" in condition:
                    result_df = result_df[result_df[column] == condition["eq"]]
                if "in" in condition:
                    result_df = result_df[result_df[column].isin(condition["in"])]
            else:
                # Simple equality
                result_df = result_df[result_df[column] == condition]
        
        return result_df
    
    def apply_sort(self, df: pd.DataFrame, sort_by: Optional[list]) -> pd.DataFrame:
        """
        Apply sorting to a DataFrame.
        
        Args:
            df: Input DataFrame
            sort_by: List of sort specs, each with "column" and "direction" (asc or desc).
                     Example: [{"column": "price", "direction": "asc"}]
                     None or empty list means no sorting.
        
        Returns:
            Sorted DataFrame
            
        Raises:
            ValueError: If column doesn't exist or direction is invalid
        """
        if not sort_by:
            return df
        
        result_df = df.copy()
        
        for sort_spec in sort_by:
            if not isinstance(sort_spec, dict) or "column" not in sort_spec:
                raise ValueError(
                    f"Invalid sort spec: {sort_spec}. Expected dict with 'column' and optional 'direction'."
                )
            
            column = sort_spec["column"]
            direction = sort_spec.get("direction", "asc").lower()
            
            if column not in result_df.columns:
                raise ValueError(
                    f"Column '{column}' not found in data. Available columns: {list(result_df.columns)}"
                )
            
            if direction not in ["asc", "desc"]:
                raise ValueError(f"Invalid sort direction: '{direction}'. Must be 'asc' or 'desc'.")
            
            result_df = result_df.sort_values(by=column, ascending=(direction == "asc"))
        
        return result_df
    
    def format_response(
        self,
        df: pd.DataFrame,
        limit: int = 100,
        columns: Optional[list[str]] = None,
    ) -> dict:
        """
        Format a DataFrame as a response dict with metadata.
        
        Args:
            df: Input DataFrame to format
            limit: Maximum number of rows to include. Default 100, max 10000.
            columns: Optional list of specific columns to include. If None, include all.
        
        Returns:
            Dict with keys: data (list of row dicts), total_matching, total_available, columns
        """
        # Enforce reasonable limits
        limit = min(max(1, limit), 10000)
        
        # Select columns if specified
        if columns:
            missing_cols = set(columns) - set(df.columns)
            if missing_cols:
                raise ValueError(
                    f"Columns not found: {missing_cols}. Available: {list(df.columns)}"
                )
            df = df[columns]
        
        # Convert to records with limit
        total_matching = len(df)
        data = df.head(limit).to_dict(orient="records")
        
        return {
            "data": data,
            "total_matching": total_matching,
            "rows_returned": len(data),
            "limit": limit,
            "columns": list(df.columns),
        }


def build_filter_dict(
    state: Optional[str] = None,
    city: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    beds_min: Optional[int] = None,
    beds_max: Optional[int] = None,
    baths_min: Optional[float] = None,
    baths_max: Optional[float] = None,
    property_types: Optional[list[str]] = None,
    status: Optional[str] = None,
    custom_filters: Optional[dict] = None,
) -> dict:
    """
    Helper to build a filter dict from common real estate query parameters.
    
    This is optional—LLMs can build filters directly, but this helper provides
    convenient aliases for common fields.
    
    Args:
        state: Filter by state abbreviation (e.g., "AL")
        city: Filter by city name
        price_min: Minimum listing price
        price_max: Maximum listing price
        beds_min: Minimum number of bedrooms
        beds_max: Maximum number of bedrooms
        baths_min: Minimum number of bathrooms
        baths_max: Maximum number of bathrooms
        property_types: List of property types (e.g., ["SINGLE_FAMILY_RESIDENTIAL", "CONDO_COOP"])
        status: Listing status (e.g., "ACTIVE", "PRE_ON_MARKET")
        custom_filters: Additional raw filters to merge
    
    Returns:
        Dict suitable for QueryEngine.apply_filters()
    """
    filters = {}
    
    if state:
        filters["homeData.addressInfo.state"] = state
    if city:
        filters["homeData.addressInfo.city"] = city
    
    if price_min is not None or price_max is not None:
        filters["homeData.priceInfo.amount.value"] = {}
        if price_min is not None:
            filters["homeData.priceInfo.amount.value"]["min"] = price_min
        if price_max is not None:
            filters["homeData.priceInfo.amount.value"]["max"] = price_max
    
    if beds_min is not None or beds_max is not None:
        filters["homeData.beds.value"] = {}
        if beds_min is not None:
            filters["homeData.beds.value"]["min"] = beds_min
        if beds_max is not None:
            filters["homeData.beds.value"]["max"] = beds_max
    
    if baths_min is not None or baths_max is not None:
        filters["homeData.baths.value"] = {}
        if baths_min is not None:
            filters["homeData.baths.value"]["min"] = baths_min
        if baths_max is not None:
            filters["homeData.baths.value"]["max"] = baths_max
    
    if property_types:
        filters["homeData.propertyType"] = {"in": property_types}
    
    if status:
        filters["homeData.listingMetadata.searchStatus"] = status
    
    if custom_filters:
        filters.update(custom_filters)
    
    return filters
