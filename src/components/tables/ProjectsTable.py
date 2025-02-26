# src/components/tables/ProjectsTable.py

import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional
from components.tables.DataTable import DataTable
from utils.formatters import Formatters
import logging

logger = logging.getLogger(__name__)

class ProjectsTable(DataTable):
    """Projects table component with specialized formatting and features"""
    
    def __init__(
        self,
        df: pd.DataFrame,
        key_prefix: str = "projects"
    ):
        """
        Initialize ProjectsTable
        
        Args:
            df: Projects DataFrame
            key_prefix: Prefix for component keys
        """
        # Define column formatters
        formatters = {
            'sum_price_agree': lambda x: Formatters.format_currency(x, 'THB'),
            'transaction_date': lambda x: Formatters.format_date(x, '%Y-%m-%d'),
            'price_build': lambda x: Formatters.format_currency(x, 'THB'),
            'project_duration': lambda x: f"{x} days"
        }
        
        super().__init__(df, formatters, key_prefix)
        
        # Default columns configuration
        self.default_columns = [
            'project_name',
            'winner',
            'dept_name',
            'sum_price_agree',
            'transaction_date'
        ]
        
        # Column labels mapping
        self.column_labels = {
            'project_name': 'Project Name',
            'winner': 'Company',
            'dept_name': 'Department',
            'sum_price_agree': 'Contract Value',
            'transaction_date': 'Date',
            'price_build': 'Budget',
            'project_duration': 'Duration',
            'purchase_method_name': 'Purchase Method'
        }
    
    def render(
        self,
        columns: Optional[List[str]] = None,
        page_size: int = 10,
        allow_column_config: bool = True,
        show_stats: bool = True
    ):
        """
        Render projects table with additional features
        
        Args:
            columns: List of columns to display
            page_size: Number of rows per page
            allow_column_config: Allow column configuration
            show_stats: Show table statistics
        """
        try:
            # Column selection
            display_columns = columns or self.default_columns
            if allow_column_config:
                display_columns = st.multiselect(
                    "Select Columns",
                    options=list(self.column_labels.keys()),
                    default=display_columns,
                    format_func=lambda x: self.column_labels.get(x, x),
                    key=f"{self.key_prefix}_columns"
                )
            
            # Show statistics
            if show_stats:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "Total Projects",
                        len(self.df),
                        help="Total number of projects displayed"
                    )
                with col2:
                    total_value = self.df['sum_price_agree'].sum()
                    st.metric(
                        "Total Value",
                        Formatters.format_currency(total_value, 'THB', precision=0),
                        help="Total value of displayed projects"
                    )
                with col3:
                    avg_value = self.df['sum_price_agree'].mean()
                    st.metric(
                        "Average Value",
                        Formatters.format_currency(avg_value, 'THB', precision=0),
                        help="Average project value"
                    )
            
            # Render table with formatting
            super().render(
                columns=display_columns,
                page_size=page_size,
                key=f"{self.key_prefix}_table"
            )
            
        except Exception as e:
            logger.error(f"Error rendering projects table: {e}")
            st.error("Error displaying projects table")