# src/pages/CompanySelection.py

import streamlit as st
from components.layout.Header import Header
from components.layout.Sidebar import Sidebar
from components.layout.MetricsSummary import MetricsSummary
from components.tables.CompanyTable import CompanyTable
from state.session import SessionState

def CompanySelection():
    """Company selection page"""
    # Initialize session state
    SessionState.initialize_state()

    # Render sidebar and get filters
    filters = Sidebar(
        filters=SessionState.get_filters(),
        selected_companies=SessionState.get_selected_companies()
    )
    
    # Render header
    Header(current_page="Company Selection")
    
    # Get filtered data
    df = SessionState.get_filtered_data()
    if df is None or df.empty:
        st.warning("Please apply filters first to select companies")
        return
    
    # Display metrics summary
    MetricsSummary(df)
    
    # Main content
    st.header("Select Companies to Analyze")
    
    # Search and filter options
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search = st.text_input("🔍 Search companies")
    
    with col2:
        min_projects = st.number_input(
            "Min. Projects",
            min_value=1,
            value=1,
            step=1
        )
    
    # Company selection table
    selected_companies = CompanyTable(
        df=df,
        selected_companies=SessionState.get_selected_companies(),
        on_selection_change=SessionState.update_selected_companies,
        editable=True,
        key_prefix="selection_"
    )
    
    # Navigation buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Reset Selection", use_container_width=True):
            SessionState.clear_selections()
            st.rerun()
    
    with col2:
        if selected_companies:
            if st.button("📊 View Analysis", type="primary", use_container_width=True):
                st.session_state.current_page = 'analysis'
                st.rerun()
        else:
            st.button(
                "📊 View Analysis",
                type="primary",
                disabled=True,
                use_container_width=True
            )

if __name__ == "__main__":
    CompanySelection()