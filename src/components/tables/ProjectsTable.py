import streamlit as st
import pandas as pd
from typing import Dict, Optional, Any
from datetime import datetime

def ProjectsTable(
    df: pd.DataFrame,
    filters: Optional[Dict[str, Any]] = None,
    show_search: bool = True,
    show_save_collection: bool = True,
    key_prefix: str = ""
):
    """
    A Streamlit-native projects table component with built-in search and filtering.
    
    Args:
        df (pd.DataFrame): DataFrame containing project data
        filters (Optional[Dict[str, Any]]): Optional filters to apply
        show_search (bool): Whether to show search and sort controls
        show_save_collection (bool): Whether to show save collection option
        key_prefix (str): Prefix for component keys
    """
    # Create a copy of the DataFrame for filtering
    display_df = df.copy()
    
    # Convert values to millions for display
    if 'sum_price_agree' in display_df.columns:
        display_df['sum_price_agree'] = df['sum_price_agree'] / 1e6
    if 'price_build' in display_df.columns:
        display_df['price_build'] = df['price_build'] / 1e6
    
    # Calculate price cut percentage
    if 'sum_price_agree' in df.columns and 'price_build' in df.columns:
        display_df['price_cut'] = ((df['sum_price_agree'] / df['price_build'] - 1) * 100).round(2)

    if show_search:
        # Create search and sort controls in columns
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_term = st.text_input(
                "🔍 Search projects",
                key=f"{key_prefix}project_search",
                placeholder="Search by project name or company"
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
            
            # Apply sorting
            if sort_by == "Date (Newest)":
                display_df = display_df.sort_values('transaction_date', ascending=False)
            elif sort_by == "Date (Oldest)":
                display_df = display_df.sort_values('transaction_date', ascending=True)
            elif sort_by == "Value (Highest)":
                display_df = display_df.sort_values('sum_price_agree', ascending=False)
            elif sort_by == "Value (Lowest)":
                display_df = display_df.sort_values('sum_price_agree', ascending=True)
            elif sort_by == "Price Cut (Highest)":
                display_df = display_df.sort_values('price_cut', ascending=False)
            elif sort_by == "Price Cut (Lowest)":
                display_df = display_df.sort_values('price_cut', ascending=True)
    
    # Format dates
    if 'transaction_date' in display_df.columns:
        display_df['transaction_date'] = pd.to_datetime(display_df['transaction_date']).dt.strftime('%Y-%m-%d')
    
    # Display the table using Streamlit's native dataframe
    st.dataframe(
        display_df[[
            'transaction_date',
            'project_id', 
            'project_name', 
            'winner', 
            'sum_price_agree', 
            'price_cut',
            'dept_name'
        ]],
        column_config={
            "transaction_date": st.column_config.DateColumn(
                "Date",
                width="small",
                format="YYYY-MM-DD"
            ),
            "project_id": st.column_config.TextColumn(
                "ID",
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
            "sum_price_agree": st.column_config.NumberColumn(
                "Final Value",
                width="small",
                format="%.2f M฿"
            ),
            "price_cut": st.column_config.NumberColumn(
                "Price Cut",
                width="small",
                format="%.2f%%",
                help="Percentage difference between budget and final value"
            ),
            "dept_name": st.column_config.TextColumn(
                "Department",
                width="medium"
            )
        },
        hide_index=True,
        key=f"{key_prefix}projects_table"
    )
    
    # Show record count
    st.markdown(f"Showing {len(display_df):,} projects")

    # Export functionality
    if st.button("📥 Export to CSV", key=f"{key_prefix}export_button"):
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"projects_export_{timestamp}.csv"
        
        # Convert to CSV
        csv = display_df.to_csv(index=False)
        
        # Create download button
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=filename,
            mime="text/csv",
            key=f"{key_prefix}download_csv"
        )