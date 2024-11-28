# src/app.py

import streamlit as st
import logging
from components.layout.MetricsSummary import MetricsSummary
from components.layout.Sidebar import Sidebar
from components.tables.ProjectsTable import ProjectsTable
from services.cache.filter_cache import get_filtered_data
from state.session import SessionState

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main application function"""
    try:
        st.set_page_config(
            page_title="Project Analytics",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Initialize session state
        SessionState.initialize_state()
        
        # Render sidebar and get filters
        filters = Sidebar(
            filters=SessionState.get_filters(),
            selected_companies=SessionState.get_selected_companies()
        )
        
        st.title("Project Database")
        MetricsSummary(SessionState.get_filtered_data())
        
        if st.session_state.filters_applied:
            if SessionState.get_filtered_data() is None:
                with st.spinner("Loading projects..."):
                    df = get_filtered_data(filters)
                    if df is not None and not df.empty:
                        SessionState.set_filtered_data(df)
                        st.rerun()
            
            filtered_df = SessionState.get_filtered_data()
            if filtered_df is not None:
                st.header("Projects")
                ProjectsTable(filtered_df, filters=filters, show_search=True, key_prefix="main_")

                if len(filtered_df) >= 10000:
                    st.warning("Results have been limited to 10,000 records. Please apply more specific filters to see all matching data.")
                
                st.header("Quick Stats")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Top Companies by Projects")
                    top_companies = filtered_df['winner'].value_counts().head(5)
                    for company, count in top_companies.items():
                        st.markdown(f"• **{company}**: {count} projects")
                
                with col2:
                    st.subheader("Top Sub-departments by Value")
                    dept_values = filtered_df.groupby('dept_sub_name')['sum_price_agree'].sum().sort_values(ascending=False).head(5)
                    for dept, value in dept_values.items():
                        st.markdown(f"• **{dept}**: {value/1e6:,.2f}M฿")
            else:
                st.info("No projects found. Please adjust your filters.")
        else:
            st.info("Please apply filters to view projects.")
    
    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error("An error occurred. Please try again or contact support.")

if __name__ == "__main__":
    main()
