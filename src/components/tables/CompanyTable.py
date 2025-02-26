# src/components/tables/CompanyTable.py

import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional, Set
from components.tables.DataTable import DataTable
from utils.formatters import Formatters
import logging

logger = logging.getLogger(__name__)

class CompanyTable(DataTable):
    """Company table component with selection and comparison features"""
    
    def __init__(
        self,
        df: pd.DataFrame,
        key_prefix: str = "companies",
        max_selections: int = 5
    ):
        """
        Initialize CompanyTable
        
        Args:
            df: Companies DataFrame
            key_prefix: Prefix for component keys
            max_selections: Maximum number of companies that can be selected
        """
        # Define column formatters
        formatters = {
            'total_value': lambda x: Formatters.format_currency(x, 'THB'),
            'avg_project_value': lambda x: Formatters.format_currency(x, 'THB'),
            'win_rate': lambda x: Formatters.format_percentage(x),
            'active_years': lambda x: f"{x} years",
            'project_count': lambda x: Formatters.format_number(x)
        }
        
        super().__init__(df, formatters, key_prefix)
        
        self.max_selections = max_selections
        self.default_columns = [
            'winner',
            'project_count',
            'total_value',
            'avg_project_value',
            'win_rate'
        ]
        
        # Column labels mapping
        self.column_labels = {
            'winner': 'Company Name',
            'project_count': 'Projects',
            'total_value': 'Total Value',
            'avg_project_value': 'Avg. Project Value',
            'win_rate': 'Win Rate',
            'active_years': 'Active Years',
            'departments': 'Departments'
        }
        
        # Initialize selection state
        if f"{key_prefix}_selected" not in st.session_state:
            st.session_state[f"{key_prefix}_selected"] = set()
    
    def render(
        self,
        columns: Optional[List[str]] = None,
        page_size: int = 10,
        allow_selection: bool = True,
        show_search: bool = True
    ) -> Set[str]:
        """
        Render company table with selection functionality
        
        Args:
            columns: List of columns to display
            page_size: Number of rows per page
            allow_selection: Allow company selection
            show_search: Show search box
            
        Returns:
            Set of selected company names
        """
        try:
            display_columns = columns or self.default_columns
            
            # Company search
            if show_search:
                search_term = st.text_input(
                    "🔍 Search Companies",
                    key=f"{self.key_prefix}_search"
                ).strip().lower()
                
                if search_term:
                    mask = self.df['winner'].str.lower().str.contains(search_term)
                    filtered_df = self.df[mask]
                else:
                    filtered_df = self.df
            else:
                filtered_df = self.df
            
            # Selection column
            if allow_selection:
                selection_col = 'select'
                filtered_df = filtered_df.copy()
                filtered_df[selection_col] = False
                
                # Get current selections
                selected = st.session_state[f"{self.key_prefix}_selected"]
                
                # Selection interface
                st.write(f"Selected: {len(selected)}/{self.max_selections}")
                
                for idx, row in filtered_df.iterrows():
                    company = row['winner']
                    is_selected = company in selected
                    
                    # Create unique key for each checkbox
                    key = f"{self.key_prefix}_select_{idx}"
                    
                    # Handle selection change
                    if st.checkbox(
                        company,
                        value=is_selected,
                        key=key,
                        disabled=not is_selected and len(selected) >= self.max_selections
                    ):
                        selected.add(company)
                    elif is_selected:
                        selected.remove(company)
                
                # Update session state
                st.session_state[f"{self.key_prefix}_selected"] = selected
                
                # Filter to show only selected companies if any are selected
                if selected:
                    filtered_df = filtered_df[filtered_df['winner'].isin(selected)]
            
            # Render table
            super().render(
                columns=display_columns,
                page_size=page_size,
                key=f"{self.key_prefix}_table"
            )
            
            return st.session_state[f"{self.key_prefix}_selected"]
            
        except Exception as e:
            logger.error(f"Error rendering company table: {e}")
            st.error("Error displaying company table")
            return set()
    
    def get_selected_companies(self) -> Set[str]:
        """Get currently selected companies"""
        return st.session_state.get(f"{self.key_prefix}_selected", set())
    
    def clear_selections(self):
        """Clear all company selections"""
        st.session_state[f"{self.key_prefix}_selected"] = set()