# src/app.py

import streamlit as st
import logging
from datetime import datetime
from components.layout.MetricsSummary import MetricsSummary
from components.tables.ProjectsTable import ProjectsTable
from services.cache.filter_cache import get_filtered_data
from services.database.mongodb import MongoDBService
from state.session import SessionState
from services.department_service import get_departments, get_sub_departments

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def render_filters():
    """Render the filter section"""
    st.title("Project Database")
    
    # Initialize session state if needed
    SessionState.initialize_state()
    
    # Get current filters
    filters = SessionState.get_filters()
    
    with st.sidebar:
        st.title("🔍 Filters")
        
        # Department Filters
        st.subheader("Department")
        departments = get_departments()
        dept_name = st.selectbox(
            "Department",
            options=[""] + departments,
            index=0 if not filters['dept_name'] else departments.index(filters['dept_name']) + 1,
            key="dept_filter"
        )
        
        sub_dept_name = ""
        if dept_name:
            sub_departments = get_sub_departments(dept_name)
            sub_dept_name = st.selectbox(
                "Sub-Department",
                options=[""] + sub_departments,
                index=0 if not filters['dept_sub_name'] else sub_departments.index(filters['dept_sub_name']) + 1,
                key="sub_dept_filter"
            )
        
        # Date Range
        st.subheader("Date Range")
        date_start = st.date_input(
            "Start Date",
            value=filters['date_start'],
            key="date_start_filter"
        )
        date_end = st.date_input(
            "End Date",
            value=filters['date_end'],
            key="date_end_filter"
        )
        
        # Price Range
        st.subheader("Price Range (Million Baht)")
        price_col1, price_col2 = st.columns(2)
        
        with price_col1:
            price_start = st.number_input(
                "From",
                min_value=0.0,
                max_value=10000.0,
                value=float(filters['price_start']),
                step=10.0,
                format="%.1f",
                key="price_start_filter"
            )
        
        with price_col2:
            price_end = st.number_input(
                "To",
                min_value=0.0,
                max_value=20000.0,
                value=float(filters['price_end']),
                step=10.0,
                format="%.1f",
                key="price_end_filter"
            )
        
        # Apply Filters button
        if st.button("🔄 Apply Filters", type="primary", use_container_width=True):
            new_filters = {
                'dept_name': dept_name,
                'dept_sub_name': sub_dept_name,
                'date_start': date_start,
                'date_end': date_end,
                'price_start': price_start,
                'price_end': price_end
            }
            SessionState.update_filters(new_filters)
            st.session_state.filters_applied = True
            st.rerun()
        
        # Clear Filters button
        if st.button("❌ Clear Filters", use_container_width=True):
            SessionState.clear_filters()
            st.rerun()

def main():
    """Main application function"""
    try:
        # Set page config
        st.set_page_config(
            page_title="Project Analytics",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Render filters
        render_filters()
        
        # Display metrics summary if data is available
        filtered_df = SessionState.get_filtered_data()
        MetricsSummary(filtered_df)
        
        # Main content area
        if st.session_state.filters_applied:
            if SessionState.get_filtered_data() is None:
                with st.spinner("Loading projects..."):
                    df = get_filtered_data(SessionState.get_filters())
                    if df is not None and not df.empty:
                        SessionState.set_filtered_data(df)
                        st.rerun()
            
            if filtered_df is not None:
                st.header("Projects")
                ProjectsTable(
                    filtered_df,
                    filters=SessionState.get_filters(),
                    show_search=True,
                    key_prefix="main_"
                )
                
                # Quick Stats
                st.header("Quick Stats")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Top Companies by Projects")
                    top_companies = filtered_df['winner'].value_counts().head(5)
                    for company, count in top_companies.items():
                        st.markdown(f"• **{company}**: {count} projects")
                
                with col2:
                    st.subheader("Top Departments by Value")
                    dept_values = filtered_df.groupby('dept_name')['sum_price_agree'].sum().sort_values(ascending=False).head(5)
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