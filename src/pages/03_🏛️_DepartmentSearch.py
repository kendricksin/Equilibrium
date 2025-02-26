# src/pages/DepartmentSearch.py

import streamlit as st
import pandas as pd
from datetime import datetime
import logging

from components.filters.TableFilter import TableFilter
from components.charts.TreemapChart import TreemapChart
from components.common.LoadingState import LoadingState
from components.common.MetricCard import MetricCard

from analytics.department.aggregation import DepartmentAnalytics
from analytics.department.distribution import DepartmentDistribution
from services.database.mongodb import MongoDBService

logger = logging.getLogger(__name__)

def DepartmentSearch():
    st.title("🏛️ Department Analysis")
    
    # Initialize services
    mongo = MongoDBService()
    dept_analytics = DepartmentAnalytics()
    dept_distribution = DepartmentDistribution()
    
    # Initialize filters
    table_filter = TableFilter(
        key_prefix="dept_search",
        config={
            'show_company_filter': False,
            'show_department_filter': False  # Department selection handled differently
        }
    )
    
    # Get filter options
    with LoadingState("Loading departments..."):
        departments = mongo.get_distinct_values("projects", "dept_name")
    
    # Render filters in sidebar
    with st.sidebar:
        filters = table_filter.render(departments=departments)
    
    # Fetch data
    with LoadingState("Analyzing departments..."):
        dept_data = dept_analytics.calculate_department_metrics(
            mongo.get_dataframe("projects", filters)  # ProjectFilters class not found, using filters directly
        )
        
        distribution_data = dept_distribution.analyze_project_distribution(
            mongo.get_dataframe("projects")
        )
    
    if dept_data:
        # Display overall metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            MetricCard(
                "Total Departments",
                len(dept_data),
                suffix=" depts"
            ).render()
        with col2:
            total_value = sum(d['total_value'] for d in dept_data)
            MetricCard(
                "Total Value",
                total_value,
                formatter=lambda x: f"฿{x:,.0f}M"
            ).render()
        with col3:
            avg_projects = sum(d['project_count'] for d in dept_data) / len(dept_data)
            MetricCard(
                "Avg Projects per Dept",
                avg_projects,
                formatter=lambda x: f"{x:.1f}"
            ).render()
        
        # Department distribution visualization
        st.subheader("Department Distribution")
        
        # Create treemap
        df = pd.DataFrame(dept_data)
        treemap = TreemapChart(
            df,
            value_column='total_value',
            path_columns=['department'],
            title="Project Value Distribution by Department"
        )
        treemap.render()
        
        # Department concentration metrics
        st.subheader("Department Concentration")
        
        # Display top departments
        st.write("Top 5 Departments by Value")
        top_5_df = pd.DataFrame(distribution_data['top_5_departments'])
        st.dataframe(
            top_5_df,
            use_container_width=True,
            column_config={
                "dept_name": "Department",
                "sum_price_agree": st.column_config.NumberColumn(
                    "Total Value",
                    format="฿%.2fM"
                ),
                "value_percentage": st.column_config.ProgressColumn(
                    "% of Total Value",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100
                )
            }
        )
        
        # Gini coefficient
        st.metric(
            "Department Concentration (Gini)",
            f"{distribution_data['gini_coefficient']:.3f}",
            help="0 = perfectly equal, 1 = perfectly unequal"
        )
    else:
        st.error("No department data available")

if __name__ == "__main__":
    DepartmentSearch()