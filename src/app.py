import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from services.database.postgres import PostgresService
from services.analytics.treemap_serivce import TreemapService
import logging

st.set_page_config(layout="wide")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_department_data(postgres_service):
    """Process department distribution data from PostgreSQL"""
    try:
        # Get all departments without limit
        dept_data = postgres_service.get_department_summary(limit=None)
        
        if not dept_data:
            return None
            
        # Calculate metadata from department data
        total_projects = sum(dept['count'] for dept in dept_data)
        total_value = sum(dept['total_value'] for dept in dept_data)
        unique_departments = len(dept_data)
        unique_companies = sum(dept['unique_companies'] for dept in dept_data)
        
        return {
            "department_data": dept_data,
            "metadata": {
                "total_projects": total_projects,
                "total_value": total_value,
                "unique_departments": unique_departments,
                "unique_companies": unique_companies
            }
        }
    except Exception as e:
        logger.error(f"Error processing department data: {e}")
        raise

def main():
    """Department analysis page using PostgreSQL"""
    try:
        # Initialize PostgreSQL service
        postgres_service = PostgresService()
        
        try:
            # Get metadata and department data
            data = process_department_data(postgres_service)
            
            if not data:
                st.warning("No department data available for analysis")
                return
            
            metadata = data["metadata"]
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Projects", f"{metadata['total_projects']:,}")
            with col2:
                st.metric("Total Value", f"฿{metadata['total_value']/1e6:,.2f}M")
            with col3:
                avg_value = metadata['total_value'] / metadata['total_projects']
                st.metric("Average Project Value", f"฿{avg_value/1e6:,.2f}M")

            # Department Distribution Section
            st.header("Department Distribution")
            
            view_type = st.radio(
                "View by:",
                ["Project Count", "Total Value"],
                horizontal=True
            )
            
            # Get department data with limit for visualization
            dept_data = postgres_service.get_department_summary(
                view_by="count" if view_type == "Project Count" else "total_value",
                limit=20
            )
            
            if dept_data:
                # Convert to DataFrame
                dept_df = pd.DataFrame(dept_data)
                
                # Create treemap based on view type
                if view_type == "Project Count":
                    value_col = 'count'
                    hover_data = {
                        'department': '%{label}',
                        'count': 'Projects: %{value:,}',
                        'total_value_millions': 'Value: ฿%{customdata[0]:.1f}M',
                        'unique_companies': 'Companies: %{customdata[1]:,}'
                    }
                else:
                    value_col = 'total_value_millions'
                    hover_data = {
                        'department': '%{label}',
                        'total_value_millions': 'Value: ฿%{value:.1f}M',
                        'count': 'Projects: %{customdata[0]:,}',
                        'unique_companies': 'Companies: %{customdata[1]:,}'
                    }
                
                custom_data = dept_df[['count', 'unique_companies']].values.tolist()
                
                # Create treemap
                fig = TreemapService.create_treemap(
                    data=dept_df,
                    id_col='department',
                    value_col=value_col,
                    hover_data=hover_data,
                    custom_data=custom_data,
                    title="Department Distribution",
                    height=600,
                    color_scheme='Reds',
                    show_percentages=True,
                    layout_options={
                        "margin": dict(t=50, l=10, r=10, b=10),
                        "uniformtext": dict(minsize=11, mode='hide')
                    }
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
        finally:
            postgres_service.disconnect()

    except Exception as e:
        logger.error(f"Error in application: {e}")
        st.error("An unexpected error occurred. Please try again later.")

if __name__ == "__main__":
    main()