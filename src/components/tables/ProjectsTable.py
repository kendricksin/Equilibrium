# src/components/tables/ProjectsTable.py

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any

def ProjectsTable(
    df: pd.DataFrame,
    filters: Optional[Dict[str, Any]] = None,
    show_search: bool = True,
    key_prefix: str = ""
):
    """
    A component that displays project information in a table format.
    
    Args:
        df (pd.DataFrame): DataFrame containing project data
        filters (Optional[Dict[str, Any]]): Additional filters to apply
        show_search (bool): Whether to show search/filter controls
        key_prefix (str): Prefix for component keys
    """
    # Create a copy of the DataFrame for filtering
    display_df = df.copy()
    
    if show_search:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_term = st.text_input(
                "🔍 Search projects",
                key=f"{key_prefix}project_search"
            ).lower()
            
            if search_term:
                display_df = display_df[
                    display_df['project_name'].str.lower().str.contains(search_term) |
                    display_df['winner'].str.lower().str.contains(search_term)
                ]
        
        with col2:
            sort_by = st.selectbox(
                "Sort by",
                options=[
                    "Date (Newest)",
                    "Date (Oldest)",
                    "Value (Highest)",
                    "Value (Lowest)"
                ],
                key=f"{key_prefix}project_sort"
            )
            
            if sort_by == "Date (Newest)":
                display_df = display_df.sort_values('transaction_date', ascending=False)
            elif sort_by == "Date (Oldest)":
                display_df = display_df.sort_values('transaction_date', ascending=True)
            elif sort_by == "Value (Highest)":
                display_df = display_df.sort_values('sum_price_agree', ascending=False)
            elif sort_by == "Value (Lowest)":
                display_df = display_df.sort_values('sum_price_agree', ascending=True)
    
    # Format dates and values
    display_df['transaction_date'] = pd.to_datetime(display_df['transaction_date']).dt.strftime('%Y-%m-%d')
    display_df['sum_price_agree'] = display_df['sum_price_agree'].apply(lambda x: f"{x/1e6:,.2f}M฿")
    
    # Display the table
    st.dataframe(
        display_df[['transaction_date', 'project_name', 'winner', 'sum_price_agree', 'dept_name']],
        column_config={
            "transaction_date": st.column_config.TextColumn(
                "Date",
                width="small"
            ),
            "project_name": st.column_config.TextColumn(
                "Project",
                width="large"
            ),
            "winner": st.column_config.TextColumn(
                "Company",
                width="medium"
            ),
            "sum_price_agree": st.column_config.TextColumn(
                "Value",
                width="small"
            ),
            "dept_name": st.column_config.TextColumn(
                "Department",
                width="medium"
            )
        },
        hide_index=True,
        key=f"{key_prefix}projects_table"
    )
    
    # Show summary
    st.markdown(f"Showing {len(display_df)} projects")