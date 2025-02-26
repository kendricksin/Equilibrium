# src/pages/02_🏢_CompanySearch.py

import streamlit as st
import pandas as pd
from datetime import datetime
import logging

from components.filters.KeywordFilter import KeywordFilter
from components.tables.CompanyTable import CompanyTable
from components.charts.TreemapChart import TreemapChart
from components.common.LoadingState import LoadingState
from components.common.MetricCard import MetricCard

from analytics.company.comparison import CompanyAnalytics
from analytics.company.metrics import CompanyMetrics
from services.database.mongodb import MongoDBService

logger = logging.getLogger(__name__)

def CompanySearch():
    st.title("🏢 Company Search & Comparison")
    
    # Initialize services
    mongo = MongoDBService()
    company_analytics = CompanyAnalytics()
    company_metrics = CompanyMetrics()
    
    # Initialize search
    keyword_filter = KeywordFilter(key_prefix="company_search")
    
    # Render filters in sidebar
    with st.sidebar:
        search_params = keyword_filter.render(
            search_fields=["winner"]
        )
    
    # Fetch companies
    with LoadingState("Loading companies..."):
        companies_df = mongo.get_company_summary()
    
    if len(companies_df) > 0:
        # Company search and selection
        search_params = keyword_filter.render(
            search_fields=["winner"]
        )
        
        # Filter companies based on search
        if search_params and search_params['include_keywords']:
            search_query = keyword_filter.build_query(search_params)
            filtered_df = companies_df[
                companies_df['winner'].str.contains(
                    '|'.join(search_params['include_keywords']),
                    case=not search_params['case_sensitive']
                )
            ]
        else:
            filtered_df = companies_df
        
        # Company selection table
        st.subheader("Select Companies to Compare")
        company_table = CompanyTable(filtered_df, max_selections=5)
        selected_companies = company_table.render(
            show_search=False  # Already using keyword filter
        )
        
        # Company comparison
        if selected_companies:
            st.subheader("Company Comparison")
            
            # Fetch detailed data for selected companies
            with LoadingState("Analyzing companies..."):
                comparison_data = company_analytics.calculate_competition_metrics(
                    companies_df,
                    list(selected_companies)
                )
            
            if comparison_data:
                # Display comparison metrics
                col1, col2 = st.columns(2)
                
                with col1:
                    # Competition matrix
                    st.write("Competition Matrix")
                    st.dataframe(
                        comparison_data['competition_matrix'],
                        use_container_width=True
                    )
                
                with col2:
                    # Department overlap
                    st.write("Department Overlap")
                    st.dataframe(
                        comparison_data['department_overlap'],
                        use_container_width=True
                    )
                
                # Company metrics
                st.subheader("Company Metrics")
                for company, metrics in comparison_data['company_metrics'].items():
                    with st.expander(company):
                        col1, col2, col3 = st.columns(3)
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
                                formatter=lambda x: f"฿{x:,.0f}M"
                            ).render()
                        with col3:
                            MetricCard(
                                "Win Rate",
                                metrics['win_rate'],
                                formatter=lambda x: f"{x:.1%}"
                            ).render()
                
                # Department distribution treemap
                st.subheader("Department Distribution")
                treemap = TreemapChart(
                    filtered_df[filtered_df['winner'].isin(selected_companies)],
                    value_column='total_value',
                    path_columns=['winner', 'dept_name'],
                    title="Project Value Distribution by Department"
                )
                treemap.render()
    else:
        st.error("No company data available")

if __name__ == "__main__":
    CompanySearch()