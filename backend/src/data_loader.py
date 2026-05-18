"""CSV data loading and caching for real estate listings."""

import os
import re
from pathlib import Path
from typing import Optional
import pandas as pd


class DataLoader:
    """Manages loading and caching of weekly CSV files."""
    
    def __init__(self, data_dir: str):
        """
        Initialize DataLoader with path to data directory.
        
        Args:
            data_dir: Path to directory containing CSV files (e.g., "backend/data")
        """
        self.data_dir = Path(data_dir)
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {data_dir}")
        
        self._cache: dict[str, pd.DataFrame] = {}
        self._available_weeks: Optional[list[str]] = None
    
    def get_available_weeks(self) -> list[str]:
        """
        Get list of available week strings from CSV filenames.
        
        Returns:
            Sorted list of week strings in format "YYYY-MM-DD" (e.g., ["2022-06-26", "2022-07-03", ...])
        """
        if self._available_weeks is not None:
            return self._available_weeks
        
        weeks = []
        # Match filenames like "USA_2022-06-26.csv"
        pattern = r"USA_(\d{4}-\d{2}-\d{2})\.csv$"
        
        for file in self.data_dir.iterdir():
            if file.is_file():
                match = re.match(pattern, file.name)
                if match:
                    week = match.group(1)
                    weeks.append(week)
        
        # Sort chronologically
        weeks.sort()
        self._available_weeks = weeks
        return weeks
    
    def load_csv_for_week(self, week: str) -> pd.DataFrame:
        """
        Load CSV for a given week, with caching.
        
        Args:
            week: Week string in format "YYYY-MM-DD" (e.g., "2022-06-26")
        
        Returns:
            DataFrame containing listings for that week
            
        Raises:
            ValueError: If week doesn't exist in available weeks
            FileNotFoundError: If CSV file cannot be read
        """
        # Check if week exists
        available = self.get_available_weeks()
        if week not in available:
            raise ValueError(
                f"Week '{week}' not found. Available weeks: {available[0]} to {available[-1]} "
                f"({len(available)} total)"
            )
        
        # Return from cache if already loaded
        if week in self._cache:
            return self._cache[week].copy()
        
        # Load from file
        filepath = self.data_dir / f"USA_{week}.csv"
        try:
            df = pd.read_csv(filepath, index_col=0)
            self._cache[week] = df
            return df.copy()
        except FileNotFoundError:
            raise FileNotFoundError(f"CSV file not found: {filepath}")
        except Exception as e:
            raise RuntimeError(f"Error loading CSV {filepath}: {e}")
    
    def get_schema_for_week(self, week: str) -> dict:
        """
        Get schema information (columns, dtypes, sample) for a week.
        
        Args:
            week: Week string in format "YYYY-MM-DD"
        
        Returns:
            Dict with keys: columns, dtypes, row_count, sample_row
            
        Raises:
            ValueError: If week doesn't exist
        """
        df = self.load_csv_for_week(week)
        
        # Get column info with types
        columns_info = {}
        for col in df.columns:
            dtype_str = str(df[col].dtype)
            columns_info[col] = {
                "dtype": dtype_str,
                "non_null_count": int(df[col].notna().sum()),
                "null_count": int(df[col].isna().sum()),
            }
        
        # Get a sample row (first non-null-heavy row)
        sample_row = df.iloc[0].to_dict() if len(df) > 0 else {}
        
        return {
            "week": week,
            "columns": list(df.columns),
            "columns_info": columns_info,
            "row_count": len(df),
            "sample_row": sample_row,
        }
