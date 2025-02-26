import streamlit as st
import pandas as pd
from typing import List, Optional, Callable

class DataTable:
    """Base table component with common functionality"""
    
    def __init__(
        self,
        df: pd.DataFrame,
        formatters: Dict[str, Callable] = None,
        key_prefix: str = ""
    ):
        self.df = df
        self.formatters = formatters or {}
        self.key_prefix = key_prefix
    
    def format_column(self, column: str, value: Any) -> str:
        """Format column value using registered formatter"""
        if column in self.formatters:
            return self.formatters[column](value)
        return str(value)
    
    def render(
        self,
        columns: List[str],
        page_size: int = 10,
        key: str = "table"
    ):
        """Render paginated table"""
        start_idx = st.session_state.get(f"{self.key_prefix}_{key}_start", 0)
        
        # Pagination controls
        total_pages = len(self.df) // page_size + 1
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            if st.button("Previous", key=f"{key}_prev"):
                start_idx = max(0, start_idx - page_size)
                
        with col3:
            if st.button("Next", key=f"{key}_next"):
                start_idx = min(len(self.df) - page_size, start_idx + page_size)
        
        # Display table
        end_idx = min(start_idx + page_size, len(self.df))
        st.dataframe(
            self.df.iloc[start_idx:end_idx][columns],
            use_container_width=True
        ) 