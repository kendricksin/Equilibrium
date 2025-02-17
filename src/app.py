import streamlit as st
import logging
from services.analytics.department_analysis import DepartmentAnalysisService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Project Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

def main():
    """Main function for the landing page"""
    try:
        st.title("📊 Project Analytics Dashboard")
        
        # Initialize department analysis service
        dept_service = DepartmentAnalysisService()
        
        # Get department overview
        dept_data, metadata = dept_service.get_department_overview()
        
        if not dept_data:
            st.warning("No department data available for analysis")
            return
        
        # Display key metrics
        st.header("Overview")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Projects",
                f"{metadata['total_projects']:,}",
                help="Total number of projects across all departments"
            )
        
        with col2:
            st.metric(
                "Total Value",
                f"฿{metadata['total_value']/1e6:,.2f}M",
                help="Total value of all projects"
            )
        
        with col3:
            st.metric(
                "Departments",
                f"{metadata['unique_departments']:,}",
                help="Number of unique departments"
            )
        
        with col4:
            st.metric(
                "Companies",
                f"{metadata['unique_companies']:,}",
                help="Number of unique companies"
            )

        # Department Distribution Section
        st.header("Department Distribution")
        
        # Analysis controls
        col1, col2 = st.columns([2, 1])
        
        with col1:
            view_type = st.radio(
                "View by:",
                ["Project Count", "Total Value"],
                horizontal=True,
                help="Choose how to visualize the department distribution"
            )
        
        with col2:
            num_depts = st.slider(
                "Number of Departments",
                min_value=5,
                max_value=50,
                value=20,
                help="Number of top departments to display"
            )
        
        # Get department distribution data
        distribution_df = dept_service.get_department_distribution(
            view_by="count" if view_type == "Project Count" else "value",
            limit=num_depts
        )
        
        if not distribution_df.empty:
            # Create visualization
            fig = dept_service.create_distribution_visualization(
                df=distribution_df,
                view_type="count" if view_type == "Project Count" else "value"
            )
            
            # Display the visualization
            st.plotly_chart(fig, use_container_width=True)
            
            # Show detailed metrics
            with st.expander("📊 Detailed Department Metrics"):
                # Format DataFrame for display
                display_df = distribution_df.copy()
                
                # Configure columns for display
                st.dataframe(
                    display_df,
                    column_config={
                        "department": st.column_config.TextColumn(
                            "Department",
                            width="large"
                        ),
                        "count": st.column_config.NumberColumn(
                            "Projects",
                            format="%d",
                            width="small"
                        ),
                        "total_value_millions": st.column_config.NumberColumn(
                            "Value (M฿)",
                            format="%.2f",
                            width="medium"
                        ),
                        "count_percentage": st.column_config.NumberColumn(
                            "Project %",
                            format="%.1f%%",
                            width="small"
                        ),
                        "value_percentage": st.column_config.NumberColumn(
                            "Value %",
                            format="%.1f%%",
                            width="small"
                        ),
                        "unique_companies": st.column_config.NumberColumn(
                            "Companies",
                            format="%d",
                            width="small"
                        )
                    },
                    hide_index=True,
                    use_container_width=True
                )
        
        # Department Details Section
        st.header("Department Details")
        
        # Department selector
        selected_dept = st.selectbox(
            "Select Department",
            options=[dept["department"] for dept in dept_data],
            help="Select a department to view detailed analysis"
        )
        
        if selected_dept:
            # Get sub-department analysis
            subdept_df = dept_service.get_subdepartment_analysis(selected_dept)
            
            if not subdept_df.empty:
                # Display sub-department metrics
                st.subheader(f"Sub-departments of {selected_dept}")
                
                # Show metrics in columns
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Sub-departments",
                        f"{len(subdept_df):,}",
                        help="Number of sub-departments"
                    )
                
                with col2:
                    total_subdept_value = subdept_df['total_value'].sum()
                    st.metric(
                        "Total Value",
                        f"฿{total_subdept_value/1e6:,.2f}M",
                        help="Total value across sub-departments"
                    )
                
                with col3:
                    total_subdept_projects = subdept_df['count'].sum()
                    st.metric(
                        "Total Projects",
                        f"{total_subdept_projects:,}",
                        help="Total projects across sub-departments"
                    )
                
                # Display sub-department table
                st.dataframe(
                    subdept_df,
                    column_config={
                        "subdepartment": st.column_config.TextColumn(
                            "Sub-department",
                            width="large"
                        ),
                        "count": st.column_config.NumberColumn(
                            "Projects",
                            format="%d",
                            width="small"
                        ),
                        "total_value_millions": st.column_config.NumberColumn(
                            "Value (M฿)",
                            format="%.2f",
                            width="medium"
                        ),
                        "count_percentage": st.column_config.NumberColumn(
                            "Project %",
                            format="%.1f%%",
                            width="small"
                        ),
                        "value_percentage": st.column_config.NumberColumn(
                            "Value %",
                            format="%.1f%%",
                            width="small"
                        ),
                        "unique_companies": st.column_config.NumberColumn(
                            "Companies",
                            format="%d",
                            width="small"
                        )
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info(f"No sub-department data available for {selected_dept}")
                
    except Exception as e:
        logger.error(f"Error in main application: {e}")
        st.error("An unexpected error occurred. Please try again later.")

if __name__ == "__main__":
    main()