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
    """A component that displays company information in a table format with selection capability."""
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
        'Price Cut'
    ]
    
    # Convert values to millions
    company_metrics['Total Value'] = company_metrics['Total Value'] / 1e6
    company_metrics['Average Value'] = company_metrics['Average Value'] / 1e6
    
    # Create display DataFrame
    display_df = company_metrics.reset_index()
    display_df = display_df.rename(columns={'winner': 'Company'})
    
    if editable:
        # Add selection column
        display_df.insert(0, 'Select', [
            company in (selected_companies or [])
            for company in display_df['Company']
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
                    help="Number of projects won",
                    format="%d"
                ),
                "Total Value": st.column_config.NumberColumn(
                    "Total Value (M฿)",
                    help="Total value of all projects in millions",
                    format="%.2f"
                ),
                "Average Value": st.column_config.NumberColumn(
                    "Avg Value (M฿)",
                    help="Average project value in millions",
                    format="%.2f"
                ),
                "Price Cut": st.column_config.NumberColumn(
                    "Price Cut (%)",
                    help="Average price cut percentage",
                    format="%.2f"
                )
            },
            hide_index=True,
            key=f"{key_prefix}company_table_editor"
        )
        
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
                    width="small",
                    format="%d"
                ),
                "Total Value": st.column_config.NumberColumn(
                    "Total Value (M฿)",
                    width="medium",
                    format="%.2f"
                ),
                "Average Value": st.column_config.NumberColumn(
                    "Avg Value (M฿)",
                    width="medium",
                    format="%.2f"
                ),
                "Price Cut": st.column_config.NumberColumn(
                    "Price Cut (%)",
                    width="small",
                    format="%.2f"
                )
            },
            hide_index=True,
            key=f"{key_prefix}company_table_view"
        )