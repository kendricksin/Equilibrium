# src/components/tables/ProjectsTable.py

import streamlit as st
import pandas as pd
from typing import Dict, Optional, Any, List

def ProjectsTable(
    df: pd.DataFrame,
    filters: Optional[Dict[str, Any]] = None,
    show_search: bool = True,
    key_prefix: str = ""
):
    """A component that displays project information in a table format.
    
    Args:
        df (pd.DataFrame): DataFrame containing project data
        filters (Optional[Dict[str, Any]]): Filter parameters (optional)
        show_search (bool): Whether to show search and sort options
        key_prefix (str): Prefix for component keys
    """
    # Create a copy of the DataFrame for filtering
    display_df = df.copy()
    
    # Convert values to millions
    display_df['sum_price_agree'] = df['sum_price_agree'] / 1e6
    if 'price_build' in df.columns:
        display_df['price_build'] = df['price_build'] / 1e6
    
    # Calculate price cut percentage if both columns exist
    if 'sum_price_agree' in df.columns and 'price_build' in df.columns:
        display_df['price_cut'] = ((df['sum_price_agree'] / df['price_build'] - 1) * 100).round(2)

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
                    "Value (Lowest)",
                    "Price Cut (Highest)",
                    "Price Cut (Lowest)"
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
            elif sort_by == "Price Cut (Highest)" and 'price_cut' in display_df.columns:
                display_df = display_df.sort_values('price_cut', ascending=False)
            elif sort_by == "Price Cut (Lowest)" and 'price_cut' in display_df.columns:
                display_df = display_df.sort_values('price_cut', ascending=True)
    
    # Keep original numerical values for sorting
    display_df['value_for_sort'] = display_df['sum_price_agree']
    
    # Format dates and values for display
    if 'transaction_date' in display_df.columns:
        display_df['transaction_date'] = pd.to_datetime(display_df['transaction_date']).dt.strftime('%Y-%m-%d')
    
    # Prepare columns for display
    display_columns = ['transaction_date', 'project_name', 'winner', 'sum_price_agree']
    
    # Add optional columns if they exist
    if 'price_build' in display_df.columns:
        display_columns.append('price_build')
    if 'price_cut' in display_df.columns:
        display_columns.append('price_cut')
    if 'dept_name' in display_df.columns:
        display_columns.append('dept_name')
    
    # Filter columns that actually exist in the dataframe
    display_columns = [col for col in display_columns if col in display_df.columns]
    
    # Column configurations
    column_config = {
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
            "Final Value",
            width="small",
            format="%.2f M฿"
        )
    }
    
    # Add configs for optional columns
    if 'price_build' in display_columns:
        column_config["price_build"] = st.column_config.NumberColumn(
            "Budget",
            width="small",
            format="%.2f M฿"
        )
    
    if 'price_cut' in display_columns:
        column_config["price_cut"] = st.column_config.NumberColumn(
            "Price Cut",
            width="small",
            format="%.2f%%",
            help="Percentage difference between budget and final value"
        )
    
    if 'dept_name' in display_columns:
        column_config["dept_name"] = st.column_config.TextColumn(
            "Department",
            width="medium"
        )
    
    # Display the table with numerical sorting
    st.dataframe(
        display_df[display_columns],
        column_config=column_config,
        hide_index=True,
        key=f"{key_prefix}projects_table"
    )
    
    st.markdown(f"Showing {len(display_df)} projects")