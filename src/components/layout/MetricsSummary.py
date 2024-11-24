# src/components/layout/MetricsSummary.py

import streamlit as st
import pandas as pd
from typing import Optional

def MetricsSummary(df: Optional[pd.DataFrame] = None):
    """
    A component that displays key metrics at the top of each page.
    
    Args:
        df (Optional[pd.DataFrame]): The filtered dataframe containing project data
    """
    with st.container():
        # Create a container with a subtle background
        st.markdown("""
            <style>
            .metrics-summary {
                background-color: #f8f9fa;
                padding: 1rem;
                border-radius: 0.5rem;
                margin-bottom: 1rem;
            }
            </style>
        """, unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="metrics-summary">', unsafe_allow_html=True)
            
            # Display metrics in columns
            col1, col2, col3, col4 = st.columns(4)
            
            if df is not None and not df.empty:
                # Calculate metrics
                total_projects = len(df)
                total_value = df['sum_price_agree'].sum() if 'sum_price_agree' in df.columns else 0
                avg_value = df['sum_price_agree'].mean() if 'sum_price_agree' in df.columns else 0
                unique_companies = df['winner'].nunique() if 'winner' in df.columns else 0
                
                # Display metrics with formatting
                with col1:
                    st.metric(
                        label="Total Projects",
                        value=f"{total_projects:,}"
                    )
                with col2:
                    st.metric(
                        label="Total Value",
                        value=f"฿{total_value/1e6:,.2f}M"
                    )
                with col3:
                    st.metric(
                        label="Average Value",
                        value=f"฿{avg_value/1e6:,.2f}M"
                    )
                with col4:
                    st.metric(
                        label="Unique Companies",
                        value=f"{unique_companies:,}"
                    )
            else:
                # Display placeholder values when no data is available
                with col1:
                    st.metric(label="Total Projects", value="-")
                with col2:
                    st.metric(label="Total Value", value="-")
                with col3:
                    st.metric(label="Average Value", value="-")
                with col4:
                    st.metric(label="Unique Companies", value="-")
            
            st.markdown('</div>', unsafe_allow_html=True)