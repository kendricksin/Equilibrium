# src/components/layout/MetricsSummary.py

import streamlit as st
import pandas as pd
from typing import Optional

def MetricsSummary(df: Optional[pd.DataFrame] = None):
    """Enhanced metrics summary with purchase method and project type data"""
    with st.container():
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
            
            if df is not None and not df.empty:
                col1, col2, col3, col4, col5 = st.columns(5)
                
                total_projects = len(df)
                total_value = df['sum_price_agree'].sum()
                avg_value = df['sum_price_agree'].mean()
                unique_companies = df['winner'].nunique()
                unique_methods = df['purchase_method_name'].nunique()
                
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
                        label="Companies",
                        value=f"{unique_companies:,}"
                    )
                with col5:
                    st.metric(
                        label="Methods",
                        value=f"{unique_methods:,}"
                    )
                
                # Additional metrics row
                col1, col2 = st.columns(2)
                with col1:
                    top_method = df['purchase_method_name'].mode().iloc[0]
                    method_count = len(df[df['purchase_method_name'] == top_method])
                    st.metric(
                        label="Top Purchase Method",
                        value=f"{top_method} ({method_count} projects)"
                    )
                with col2:
                    top_type = df['project_type_name'].mode().iloc[0]
                    type_count = len(df[df['project_type_name'] == top_type])
                    st.metric(
                        label="Top Project Type",
                        value=f"{top_type} ({type_count} projects)"
                    )
            else:
                st.metric(label="Total Projects", value="-")
                st.metric(label="Total Value", value="-")
                st.metric(label="Average Value", value="-")
                st.metric(label="Companies", value="-")
                st.metric(label="Methods", value="-")
            
            st.markdown('</div>', unsafe_allow_html=True)