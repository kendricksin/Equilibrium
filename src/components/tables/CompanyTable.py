# src/components/tables/CompanyTable.py

import streamlit as st
import pandas as pd
from typing import List, Optional, Callable

def CompanyTable(
    df: pd.DataFrame,
    selected_companies: Optional[List[str]] = None,
    on_selection_change: Optional[Callable[[List[str]], None]] = None,
    editable: bool = False,
    key_prefix: str = ""
):
    """
    A component that displays company information in a table format with selection capability.
    
    Args:
        df (pd.DataFrame): DataFrame containing company data
        selected_companies (Optional[List[str]]): List of currently selected company IDs
        on_selection_change (Optional[Callable]): Callback for selection changes
        editable (bool): Whether to allow selection/editing
        key_prefix (str): Prefix for component keys
    """
    # Calculate company metrics
    company_metrics = df.groupby('winner').agg({
        'project_name': 'count',
        'sum_price_agree': ['sum', 'mean'],
        'price_build': lambda x: ((df.loc[x.index, 'sum_price_agree'].sum() / x.sum()) - 1) * 100
    })

    # Flatten column names
    company_metrics.columns = [
        'Number of Projects',
        'Total Value',
        'Average Value',
        'Price Cut %'
    ]
    
    # Keep numerical values for sorting
    company_metrics['Total Value Numeric'] = company_metrics['Total Value']
    company_metrics['Average Value Numeric'] = company_metrics['Average Value']
    
    # Format values for display
    company_metrics['Total Value'] = company_metrics['Total Value'].apply(lambda x: f"{x/1e6:,.2f}M฿")
    company_metrics['Average Value'] = company_metrics['Average Value'].apply(lambda x: f"{x/1e6:,.2f}M฿")
    company_metrics['Price Cut %'] = company_metrics['Price Cut %'].apply(lambda x: f"{x:.2f}%")
    
    # Create display DataFrame
    display_df = company_metrics.reset_index()
    display_df = display_df.rename(columns={'winner': 'Company'})
    
    if editable:
        # Add selection column
        display_df.insert(0, 'Select', [
            company in (selected_companies or [])
            for company in company_metrics.index
        ])
        
        # Use data editor for editable mode
        edited_df = st.data_editor(
            display_df,
            column_config={
                "Select": st.column_config.CheckboxColumn(
                    "Select",
                    help="Select company for analysis",
                    default=False,
                ),
                "Company": st.column_config.TextColumn(
                    "Company",
                    help="Company name",
                ),
                "Number of Projects": st.column_config.NumberColumn(
                    "Projects",
                    help="Number of projects won"
                ),
                "Total Value": st.column_config.TextColumn(
                    "Total Value",
                    help="Total value of all projects"
                ),
                "Average Value": st.column_config.TextColumn(
                    "Avg Value",
                    help="Average project value"
                ),
                "Price Cut %": st.column_config.TextColumn(
                    "Price Cut",
                    help="Average price cut percentage"
                )
            },
            hide_index=True,
            key=f"{key_prefix}company_table_editor"
        )
        
        # Trigger selection change callback
        if on_selection_change and edited_df is not None:
            selected = edited_df[edited_df['Select']]['Company'].tolist()
            on_selection_change(selected)
    
    else:
        # Use regular dataframe for view mode
        st.dataframe(
            display_df,
            column_config={
                "Company": st.column_config.TextColumn(
                    "Company",
                    width="large"
                ),
                "Number of Projects": st.column_config.NumberColumn(
                    "Projects",
                    width="small"
                ),
                "Total Value": st.column_config.TextColumn(
                    "Total Value",
                    width="medium"
                ),
                "Average Value": st.column_config.TextColumn(
                    "Avg Value",
                    width="medium"
                ),
                "Price Cut %": st.column_config.TextColumn(
                    "Price Cut",
                    width="small"
                )
            },
            hide_index=True,
            key=f"{key_prefix}company_table_view"
        )