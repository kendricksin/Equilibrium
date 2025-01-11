# src/pages/Home.py

import streamlit as st
import pandas as pd
from services.database.mongodb import MongoDBService
from services.analytics.treemap_serivce import TreemapService
from services.cache.department_cache import get_departments, get_department_stats
import logging
from components.layout.PageLayout import PageLayout

logger = logging.getLogger(__name__)

def Home():
    """Home page with department overview and analysis"""
    try:
        mongo_service = MongoDBService()
        
        # Get metadata
        collection = mongo_service.get_collection("department_distribution")
        data = process_department_data(collection)
        
        if not data:
            st.warning("No department data available for analysis")
            return
        
        render_overview_metrics(data["metadata"])
        render_department_distribution(mongo_service)
        render_department_details()
        
    except Exception as e:
        logger.error(f"Error in Home page: {e}")
        st.error("An unexpected error occurred. Please try again later.")
    finally:
        mongo_service.disconnect()

def process_department_data(collection):
    """Process department distribution data"""
    try:
        totals = collection.find_one({"_id": "totals"})
        if not totals:
            return None
        
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
        return None

def render_overview_metrics(metadata):
    """Render overview metrics section"""
    st.markdown("### 📊 Overview")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Total Projects",
            f"{metadata['total_projects']:,}",
            help="Total number of projects in the database"
        )
    with col2:
        st.metric(
            "Total Value",
            f"฿{metadata['total_value']/1e6:,.2f}M",
            help="Total value of all projects"
        )
    with col3:
        avg_value = metadata['total_value'] / metadata['total_projects']
        st.metric(
            "Average Project Value",
            f"฿{avg_value/1e6:,.2f}M",
            help="Average value per project"
        )

def render_department_distribution(mongo_service):
    """Render department distribution section"""
    st.markdown("### 🏢 Department Distribution")
    
    view_type = st.radio(
        "View by:",
        ["Project Count", "Total Value"],
        horizontal=True
    )
    
    dept_data = mongo_service.get_department_summary(
        view_by="count" if view_type == "Project Count" else "total_value",
        limit=20
    )
    
    if not dept_data:
        st.warning("No department data available")
        return
        
    dept_df = pd.DataFrame(dept_data)
    
    # Create visualization based on view type
    value_col = 'count' if view_type == "Project Count" else 'total_value_millions'
    hover_data = create_hover_template(view_type)
    custom_data = create_custom_data(dept_df, view_type)
    
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
        },
        text_template="<b>{}</b><br>{:.1f}%"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_department_details():
    """Render department details section"""
    st.markdown("### 🔍 Department Details")
    
    dept_options = get_departments()
    dept_display_options = format_department_options(dept_options)
    dept_mapping = dict(zip(dept_display_options, dept_options))
    
    selected_display = st.selectbox(
        "Select Department for Detailed Analysis",
        options=dept_display_options
    )
    
    if selected_display:
        display_department_metrics(dept_mapping[selected_display])

def create_hover_template(view_type):
    """Create hover template based on view type"""
    if view_type == "Project Count":
        return {
            'department': '%{label}',
            'count': 'Projects: %{value:,}',
            'total_value_millions': 'Value: ฿%{customdata.total_value_millions:.1f}M',
            'unique_companies': 'Companies: %{customdata.unique_companies:,}'
        }
    else:
        return {
            'department': '%{label}',
            'total_value_millions': 'Value: ฿%{value:.1f}M',
            'count': 'Projects: %{customdata.count:,}',
            'unique_companies': 'Companies: %{customdata.unique_companies:,}'
        }

def create_custom_data(df, view_type):
    """Create custom data for treemap based on view type"""
    if view_type == "Project Count":
        return df[['total_value_millions', 'unique_companies']].to_dict('records')
    else:
        return df[['count', 'unique_companies']].to_dict('records')

def format_department_options(departments):
    """Format department options with statistics"""
    options = []
    for dept in departments:
        stats = get_department_stats(dept)
        if stats:
            count = stats.get('count', 0)
            value = stats.get('total_value_millions', 0)
            options.append(f"{dept} ({count:,} projects, ฿{value:.1f}M)")
        else:
            options.append(dept)
    return options

def display_department_metrics(dept_name):
    """Display detailed metrics for selected department"""
    dept_stats = get_department_stats(dept_name)
    if not dept_stats:
        return
        
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Projects", f"{dept_stats['count']:,}")
    with col2:
        st.metric("Total Value", f"฿{dept_stats['total_value_millions']:.2f}M")
    with col3:
        st.metric("Market Share", f"{dept_stats['value_percentage']:.1f}%")
    with col4:
        st.metric("Unique Companies", f"{dept_stats['unique_companies']:,}")

if __name__ == "__main__":
    PageLayout(Home)