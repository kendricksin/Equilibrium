# src/components/tables/ProjectsTable.py

import streamlit as st
import pandas as pd
from typing import Dict, Optional, Any
def ProjectsTable(
    df: pd.DataFrame,
    filters: Optional[Dict[str, Any]] = None,
    show_search: bool = True,
    key_prefix: str = ""
):
    """A component that displays project information in a table format."""
    # Create a copy of the DataFrame for filtering
    display_df = df.copy()
    display_df['sum_price_agree'] = df['sum_price_agree'] / 1e6

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
            
            # Sort using numerical values before formatting
            if sort_by == "Date (Newest)":
                display_df = display_df.sort_values('transaction_date', ascending=False)
            elif sort_by == "Date (Oldest)":
                display_df = display_df.sort_values('transaction_date', ascending=True)
            elif sort_by == "Value (Highest)":
                display_df = display_df.sort_values('sum_price_agree', ascending=False)
            elif sort_by == "Value (Lowest)":
                display_df = display_df.sort_values('sum_price_agree', ascending=True)
    
    # Keep original numerical values for sorting
    display_df['value_for_sort'] = display_df['sum_price_agree']
    
    # Format dates and values for display
    display_df['transaction_date'] = pd.to_datetime(display_df['transaction_date']).dt.strftime('%Y-%m-%d')
    
    # Display the table with numerical sorting
    st.dataframe(
        display_df[['transaction_date', 'project_name', 'winner', 'sum_price_agree', 'dept_name']],
        column_config={
            "transaction_date": st.column_config.DateColumn(
                "Date",
                width="small",
                format="YYYY-MM-DD"
            ),
            "project_name": st.column_config.TextColumn(
                "Project",
                width="large"
            ),
            "winner": st.column_config.TextColumn(
                "Company",
                width="medium"
            ),
            "sum_price_agree": st.column_config.NumberColumn(
                "Value",
                width="small",
                format="%.2f M฿"
            ),
            "dept_name": st.column_config.TextColumn(
                "Department",
                width="medium"
            )
        },
        hide_index=True,
        key=f"{key_prefix}projects_table"
    )
    
    st.markdown(f"Showing {len(display_df)} projects")