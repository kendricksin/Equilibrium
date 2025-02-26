# src/pages/ProjectSearch.py

import streamlit as st
import pandas as pd
from datetime import datetime
import logging

from components.filters.TableFilter import TableFilter
from components.filters.KeywordFilter import KeywordFilter
from components.tables.ProjectsTable import ProjectsTable
from components.common.LoadingState import LoadingState
from components.common.MetricCard import MetricCard

from analytics.projects.filters import ProjectFilters
from analytics.projects.metrics import ProjectMetrics
from services.database.mongodb import MongoDBService

logger = logging.getLogger(__name__)

def ProjectSearch():
    st.title("📝 Project Search")
    
    # Initialize services
    mongo = MongoDBService()
    project_metrics = ProjectMetrics()
    
    # Initialize filters
    table_filter = TableFilter(key_prefix="project_search")
    keyword_filter = KeywordFilter(key_prefix="project_search")
    
    # Get filter options
    with LoadingState("Loading filter options..."):
        departments = mongo.get_distinct_values("projects", "dept_name")
        companies = mongo.get_distinct_values("projects", "winner")
    
    # Render filters in sidebar for better space usage
    with st.sidebar:
        filters = table_filter.render(departments=departments, companies=companies)
        keyword_params = keyword_filter.render(
            search_fields=["project_name", "winner", "dept_name", "purchase_method_name"]
        )
    
    # Build query
    query = {}
    if filters:
        query.update(ProjectFilters.build_mongo_query(filters))
    if keyword_params:
        keyword_query = keyword_filter.build_query(keyword_params)
        if keyword_query:
            query.update(keyword_query)
    
    # Fetch data
    with LoadingState("Fetching projects..."):
        projects_df = mongo.get_dataframe("projects", query)
    
    if len(projects_df) > 0:
        # Calculate metrics
        metrics = project_metrics.calculate_summary_metrics(projects_df)
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            MetricCard(
                "Total Projects",
                metrics['total_projects'],
                formatter=lambda x: f"{x:,}"
            ).render()
        with col2:
            MetricCard(
                "Total Value",
                metrics['total_value'],
                formatter=lambda x: f"฿{x:,.0f}M",
                help_text="Total project value in millions"
            ).render()
        with col3:
            MetricCard(
                "Departments",
                metrics['unique_departments'],
                suffix=" depts"
            ).render()
        with col4:
            MetricCard(
                "Companies",
                metrics['unique_companies'],
                suffix=" companies"
            ).render()
        
        # Display projects table
        st.subheader("Projects")
        projects_table = ProjectsTable(projects_df)
        projects_table.render(
            allow_column_config=True,
            show_stats=False  # Already showing metrics above
        )
    else:
        st.info("No projects found matching the criteria")

if __name__ == "__main__":
    ProjectSearch()