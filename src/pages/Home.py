# src/pages/Home.py

import streamlit as st
from components.layout.Header import Header
from components.layout.Sidebar import Sidebar
from components.layout.MetricsSummary import MetricsSummary
from components.tables.ProjectsTable import ProjectsTable
from services.cache.filter_cache import get_filtered_data
from state.session import SessionState

st.set_page_config(layout="wide")

def Home():
    """Main home page of the application."""
    # Initialize session state
    SessionState.initialize_state()
    
    # Render header
    Header(current_page="Home")
    
    # Render sidebar and get filters
    filters = Sidebar(
        filters=SessionState.get_filters(),
        selected_companies=SessionState.get_selected_companies()
    )
    
    # Display metrics summary (empty if no data)
    MetricsSummary(SessionState.get_filtered_data())
    
    # Main content
    st.markdown("### Recent Projects")
    
    if st.session_state.filters_applied:
        if SessionState.get_filtered_data() is None:
            with st.spinner("Loading projects..."):
                df = get_filtered_data(filters)
                if df is not None and not df.empty:
                    SessionState.set_filtered_data(df)
                    st.rerun()
        
        if SessionState.get_filtered_data() is not None:
            ProjectsTable(
                SessionState.get_filtered_data(),
                filters=filters,
                show_search=True,
                key_prefix="home_"
            )
        else:
            st.warning("No projects found. Please adjust your filters.")
    else:
        st.info("Please apply filters to view projects.")
    
    # Quick Stats
    if SessionState.get_filtered_data() is not None:
        df = SessionState.get_filtered_data()
        
        st.markdown("### Quick Stats")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Top Companies by Projects")
            top_companies = df['winner'].value_counts().head(5)
            for company, count in top_companies.items():
                st.markdown(f"• **{company}**: {count} projects")
        
        with col2:
            st.subheader("Top Sub-departments by Value")
            dept_values = df.groupby('dept_sub_name')['sum_price_agree'].sum().sort_values(ascending=False).head(5)
            for dept, value in dept_values.items():
                st.markdown(f"• **{dept}**: {value/1e6:,.2f}M฿")

if __name__ == "__main__":
    Home()