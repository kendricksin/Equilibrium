# src/components/layout/Navigation.py

import streamlit as st
from typing import Dict, Any, Optional
import pandas as pd
from io import BytesIO

def render_navigation():
    """Render the sidebar navigation with sections and icons"""
    
    # Home section
    if st.sidebar.button("🏠 Home", use_container_width=True):
        st.switch_page("pages/Home.py")  # Main script is always "app.py"
    
    st.sidebar.markdown("#### 01 - Search & Analysis")
    
    if st.sidebar.button("🔍 Project Search", use_container_width=True):
        st.switch_page("pages/ProjectSearch.py")
        
    if st.sidebar.button("🏢 Department Search", use_container_width=True):
        st.switch_page("pages/DepartmentSearch.py")
        
    if st.sidebar.button("💼 Company Search", use_container_width=True):
        st.switch_page("pages/CompanySearch.py")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### 02 - Define Context")
    
    if st.sidebar.button("📚 Context Manager", use_container_width=True):
        st.switch_page("pages/ContextManager.py")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### 03 - Compare & Visualize")
    
    if st.sidebar.button("📊 Stacked Company Analysis", use_container_width=True):
        st.switch_page("pages/StackedCompany.py")
    
    # Add export section if data is loaded
    if 'filtered_df' in st.session_state and st.session_state.filtered_df is not None:
        st.sidebar.markdown("---")
        render_export_options()

def render_export_options():
    """Render export options in sidebar"""
    with st.sidebar.expander("📥 Export Options", expanded=False):
        if st.button("Export to CSV", use_container_width=True):
            export_to_csv()
        if st.button("Export to Excel", use_container_width=True):
            export_to_excel()

def export_to_csv():
    """Export current data to CSV"""
    if st.session_state.filtered_df is not None:
        csv = st.session_state.filtered_df.to_csv(index=False)
        st.download_button(
            "Download CSV",
            csv,
            "data_export.csv",
            "text/csv",
            key='download-csv'
        )

def export_to_excel():
    """Export current data to Excel"""
    if st.session_state.filtered_df is not None:
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            st.session_state.filtered_df.to_excel(writer, index=False)
        st.download_button(
            "Download Excel",
            buffer,
            "data_export.xlsx",
            "application/vnd.ms-excel",
            key='download-excel'
        )