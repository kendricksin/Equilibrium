# src/app.py

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from services.database.mongodb import MongoDBService
from services.analytics.treemap_serivce import TreemapService
from state.session import SessionState
import logging

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
        mongo_service = MongoDBService()
        
        try:
            # Get metadata
            collection = mongo_service.get_collection("department_distribution")
            data = process_department_data(collection)
            
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
            
            # Get pre-aggregated department data
            dept_data = mongo_service.get_department_summary(
                view_by="count" if view_type == "Project Count" else "total_value"
            )
            
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
                custom_data = [
                    dept_df['total_value_millions'].tolist(),
                    dept_df['unique_companies'].tolist()
                ]
            else:
                value_col = 'total_value_millions'
                hover_data = {
                    'department': '%{label}',
                    'total_value_millions': 'Value: ฿%{value:.1f}M',
                    'count': 'Projects: %{customdata[0]:,}',
                    'unique_companies': 'Companies: %{customdata[1]:,}'
                }
                custom_data = [
                    dept_df['count'].tolist(),
                    dept_df['unique_companies'].tolist()
                ]

            # Create department treemap
            fig = TreemapService.create_treemap(
                data=dept_df,
                id_col='department',
                value_col=value_col,
                hover_data=hover_data,
                custom_data=custom_data,
                title="Department Distribution",
                height=600,
                color_scheme='Blues',
                show_percentages=True,
                layout_options={
                    "margin": dict(t=50, l=10, r=10, b=10),
                    "uniformtext": dict(minsize=11, mode='hide')
                },
                text_template="<b>{}</b><br>{:.1f}%"  # Format for label and percentage
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Department Details Section
            st.header("Department Details")
            
            # Get departments for selector
            dept_options = dept_df['department'].tolist()
            selected_dept = st.selectbox(
                "Select Department for Detailed Analysis",
                options=sorted(dept_options)
            )
            
            if selected_dept:
                # Get pre-aggregated subdepartment data
                subdept_data = mongo_service.get_subdepartment_data(selected_dept)
                subdept_df = pd.DataFrame(subdept_data)
                
                if not subdept_df.empty:
                    # Display metrics using first department record
                    dept_info = dept_df[dept_df['department'] == selected_dept].iloc[0]
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Projects", f"{dept_info['count']:,}")
                    with col2:
                        st.metric("Total Value", f"฿{dept_info['total_value_millions']:.2f}M")
                    with col3:
                        st.metric("Market Share", f"{dept_info['value_percentage']:.1f}%")
                    with col4:
                        st.metric("Unique Companies", f"{dept_info['unique_companies']:,}")
                    
                    # Create subdepartment visualization
                    metric_choice = st.radio(
                        "View by:",
                        ["Project Count", "Total Value"],
                        horizontal=True,
                        key="subdept_metric"
                    )
                    
                    if metric_choice == "Project Count":
                        value_col = 'count'
                        hover_data = {
                            'subdepartment': '%{label}',
                            'count': 'Projects: %{value:,}',
                            'total_value_millions': 'Value: ฿%{customdata[0]:.1f}M',
                            'unique_companies': 'Companies: %{customdata[1]:,}'
                        }
                        custom_data = [
                            subdept_df['total_value_millions'].tolist(),
                            subdept_df['unique_companies'].tolist()
                        ]
                    else:
                        value_col = 'total_value_millions'
                        hover_data = {
                            'subdepartment': '%{label}',
                            'total_value_millions': 'Value: ฿%{value:.1f}M',
                            'count': 'Projects: %{customdata[0]:,}',
                            'unique_companies': 'Companies: %{customdata[1]:,}'
                        }
                        custom_data = [
                            subdept_df['count'].tolist(),
                            subdept_df['unique_companies'].tolist()
                        ]

                    # Create subdepartment treemap
                    subdept_fig = TreemapService.create_treemap(
                        data=subdept_df,
                        id_col='subdepartment',
                        value_col=value_col,
                        hover_data=hover_data,
                        custom_data=custom_data,
                        title=f"Sub-departments of {selected_dept}",
                        height=400,
                        color_scheme='Blues',
                        show_percentages=True,
                        text_template="<b>{}</b><br>{:.1f}%"
                    )
                    
                    st.plotly_chart(subdept_fig, use_container_width=True)

        finally:
            mongo_service.disconnect()

    except Exception as e:
        logger.error(f"Error in application: {e}")
        st.error("An unexpected error occurred. Please try again later.")

if __name__ == "__main__":
    main()