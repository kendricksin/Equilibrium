# src/pages/CompanySelection.py

import streamlit as st
from components.layout.Header import Header
from components.layout.Sidebar import Sidebar
from components.layout.MetricsSummary import MetricsSummary
from components.tables.CompanyTable import CompanyTable
from state.session import SessionState
from services.cache.filter_cache import get_filtered_data

st.set_page_config(layout="wide")

def CompanySelection():
    """Company selection page with enhanced filter responsiveness"""
    # Initialize session state
    SessionState.initialize_state()

    # Render sidebar and get filters
    filters = Sidebar(
        filters=SessionState.get_filters(),
        selected_companies=SessionState.get_selected_companies(),
        on_filter_change=lambda f: st.session_state.update({'filtered_df': None})
    )
    
    # Render header
    Header(current_page="Company Selection")
    
    # Handle filter changes and data loading
    if st.session_state.filters_applied:
        if SessionState.get_filtered_data() is None:
            with st.spinner("Loading projects..."):
                df = get_filtered_data(filters)
                if df is not None and not df.empty:
                    SessionState.set_filtered_data(df)
                    st.rerun()
        
        filtered_df = SessionState.get_filtered_data()
        if filtered_df is not None:
            # Display metrics summary
            MetricsSummary(filtered_df)
            
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
            
            # Apply search and minimum project filters to the dataframe
            if search:
                filtered_df = filtered_df[
                    filtered_df['winner'].str.contains(search, case=False, na=False)
                ]
            
            if min_projects > 1:
                company_counts = filtered_df['winner'].value_counts()
                valid_companies = company_counts[company_counts >= min_projects].index
                filtered_df = filtered_df[filtered_df['winner'].isin(valid_companies)]
            
            # Company selection table
            selected_companies = CompanyTable(
                df=filtered_df,
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
                    if st.button("📊 Compare Companies", type="primary", use_container_width=True):
                        st.session_state.current_page = 'company_comparison'
                        st.rerun()
                else:
                    st.button(
                        "📊 Compare Companies",
                        type="primary",
                        disabled=True,
                        use_container_width=True
                    )
        else:
            st.info("No projects found matching the current filters.")
    else:
        st.info("Please apply filters to view and select companies.")

if __name__ == "__main__":
    CompanySelection()