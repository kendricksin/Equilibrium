# src/app.py

import streamlit as st
import pandas as pd
from datetime import datetime
import logging

from components.charts.TreemapChart import TreemapChart
from components.common.MetricCard import MetricCard
from components.common.LoadingState import LoadingState
from services.database.mongodb import MongoDBService
from services.database.analytics import AnalyticsService
from services.database.caching import CachingService

st.set_page_config(layout="wide")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_department_data(collection):
    """Process department distribution data from MongoDB collection"""
    try:
        # Get totals document
        totals = collection.find_one({"_id": "totals"})
        if not totals:
            raise ValueError("Totals document not found")
        
        return {
            "metadata": {
                "total_projects": totals["total_count"],
                "total_value": totals["total_value"],
                "unique_departments": totals["unique_departments"],
                "unique_companies": totals["unique_companies"],
                "last_updated": totals["last_updated"]
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing department data: {e}")
        raise

def main():
    """Department and sub-department analysis page using aggregated data"""
    try:
        # Initialize services
        mongo = MongoDBService()
        analytics = AnalyticsService()
        cache = CachingService()
        
        try:
            # Get metadata
            with LoadingState("Loading department data..."):
                collection = mongo.get_collection("department_distribution")
                data = process_department_data(collection)
            
            if not data:
                st.warning("No department data available for analysis")
                return
            
            metadata = data["metadata"]
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                MetricCard(
                    "Total Projects",
                    metadata['total_projects'],
                    formatter=lambda x: f"{x:,}"
                ).render()
            with col2:
                MetricCard(
                    "Total Value",
                    metadata['total_value'],
                    formatter=lambda x: f"฿{x/1e6:,.2f}M"
                ).render()
            with col3:
                avg_value = metadata['total_value'] / metadata['total_projects']
                MetricCard(
                    "Average Project Value",
                    avg_value,
                    formatter=lambda x: f"฿{x/1e6:,.2f}M"
                ).render()

            # Department Distribution Section
            st.header("Department Distribution")
            
            # View options
            col1, col2 = st.columns([3, 1])
            with col1:
                view_type = st.radio(
                    "View by:",
                    ["Project Count", "Total Value"],
                    horizontal=True
                )
            with col2:
                dept_limit = st.selectbox(
                    "Number of departments:",
                    options=[10, 20, 30, 50, 100],
                    index=1  # Default to 20
                )
            
            # Get pre-aggregated department data
            with LoadingState("Loading department distribution..."):
                dept_data = mongo.get_department_summary(
                    view_by="count" if view_type == "Project Count" else "total_value",
                    limit=dept_limit
                )
                dept_df = pd.DataFrame(dept_data)
            
            if len(dept_df) > 0:
                # Add this before creating the department treemap
                st.write(f"Department data shape: {dept_df.shape}")
                st.write(f"Department columns: {dept_df.columns.tolist()}")
                if len(dept_df) > 0:
                    st.write("Sample department data:")
                    st.write(dept_df.head(3))
                
                # Create department treemap
                dept_treemap = TreemapChart(
                    data=dept_df,
                    value_column='count' if view_type == "Project Count" else 'total_value_millions',
                    path_columns=['department'],
                    title=f"Top {dept_limit} Departments by {view_type}",
                    height=600,
                    color_scheme='Reds',
                    max_items=dept_limit
                )
                dept_treemap.render()
                
                # Department Details Section
                st.header("Department Details")
                
                # Department selection with stats
                departments = dept_df['department'].tolist()
                dept_options = []
                
                for dept in departments:
                    dept_stats = dept_df[dept_df['department'] == dept].iloc[0]
                    dept_options.append(
                        f"{dept} ({int(dept_stats['count']):,} projects, "
                        f"฿{dept_stats['total_value_millions']:.1f}M)"
                    )
                
                # Create mapping from display string back to department name
                dept_mapping = dict(zip(dept_options, departments))
                
                selected_display = st.selectbox(
                    "Select Department for Detailed Analysis",
                    options=dept_options
                )
                
                if selected_display:
                    selected_dept = dept_mapping[selected_display]
                    dept_stats = dept_df[dept_df['department'] == selected_dept].iloc[0]
                    
                    # Display department metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        MetricCard(
                            "Total Projects",
                            dept_stats['count'],
                            formatter=lambda x: f"{int(x):,}"
                        ).render()
                    with col2:
                        MetricCard(
                            "Total Value",
                            dept_stats['total_value_millions'],
                            formatter=lambda x: f"฿{x:.2f}M"
                        ).render()
                    with col3:
                        MetricCard(
                            "Market Share",
                            dept_stats['value_percentage'],
                            formatter=lambda x: f"{x:.1f}%"
                        ).render()
                    with col4:
                        MetricCard(
                            "Unique Companies",
                            dept_stats['unique_companies'],
                            formatter=lambda x: f"{int(x):,}"
                        ).render()
                    
                    # Sub-department options
                    col1, col2 = st.columns([3, 1])
                    with col2:
                        subdept_limit = st.selectbox(
                            "Number of sub-departments:",
                            options=[10, 20, 30, 50, 100],
                            index=1  # Default to 20
                        )
                    
                    # Get and display subdepartment data
                    with LoadingState("Loading subdepartment data..."):
                        subdept_data = mongo.get_subdepartment_data(
                            selected_dept, 
                            limit=subdept_limit
                        )
                        subdept_df = pd.DataFrame(subdept_data)
                        
                        if len(subdept_df) > 0:
                            # Add this before creating the subdepartment treemap
                            st.write(f"Subdepartment data shape: {subdept_df.shape}")
                            st.write(f"Subdepartment columns: {subdept_df.columns.tolist()}")
                            if len(subdept_df) > 0:
                                st.write("Sample subdepartment data:")
                                st.write(subdept_df.head(3))
                            
                            subdept_treemap = TreemapChart(
                                data=subdept_df,
                                value_column='count' if view_type == "Project Count" else 'total_value_millions',
                                path_columns=['subdepartment'],
                                title=f"Top {subdept_limit} Sub-departments of {selected_dept}",
                                height=400,
                                color_scheme='Reds',
                                max_items=subdept_limit
                            )
                            subdept_treemap.render()
                        else:
                            st.info(f"No sub-department data available for {selected_dept}")

        finally:
            mongo.disconnect()

    except Exception as e:
        logger.error(f"Error in application: {e}")
        st.error("An unexpected error occurred. Please try again later.")

if __name__ == "__main__":
    main()