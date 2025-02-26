# src/pages/04_🔍_AdvancedSearch.py

import streamlit as st
import pandas as pd
from datetime import datetime
import logging

from components.filters.KeywordFilter import KeywordFilter
from components.tables.ProjectsTable import ProjectsTable
from components.common.LoadingState import LoadingState
from components.common.MetricCard import MetricCard
from components.charts.TreemapChart import TreemapChart
from components.charts.StackedBarChart import StackedBarChart
from components.filters.AdvancedFilters import AdvancedFilters

from analytics.projects.metrics import ProjectMetrics
from analytics.projects.trends import ProjectTrends
from services.database.mongodb import MongoDBService

st.set_page_config(layout="wide")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def AdvancedSearch():
    st.title("🔍 Advanced Project Search")
    
    # Initialize services
    mongo = MongoDBService()
    project_metrics = ProjectMetrics()
    project_trends = ProjectTrends()
    
    # Initialize keyword filter
    keyword_filter = KeywordFilter(
        key_prefix="advanced_search",
        config={
            'min_keyword_length': 2,
            'max_keywords': 5,
            'show_advanced': True,
            'default_search_fields': ['project_name', 'winner']
        }
    )
    
    # Render search interface
    st.write("Search for projects by keywords in project name or company name")
    
    # Keyword search
    keyword_params = keyword_filter.render(
        search_fields=["project_name", "winner", "dept_name", "purchase_method_name"]
    )
    
    # Initialize projects_df as empty DataFrame
    projects_df = pd.DataFrame()
    
    # Build initial query from keywords
    if keyword_params and keyword_params.get('include_keywords'):
        keyword_query = keyword_filter.build_query(keyword_params)
        if keyword_query:
            # Fetch initial search results
            with LoadingState("Searching projects..."):
                projects_df = mongo.get_dataframe("projects", keyword_query)
    
    # Only show advanced filters if we have search results
    if not projects_df.empty:
        st.success(f"Found {len(projects_df)} projects matching your search criteria")
        
        # Initialize advanced filters with search results
        advanced_filters = AdvancedFilters(
            data=projects_df,
            key_prefix="search",
            config={
                'show_value_range': True,
                'show_date_range': True,
                'show_departments': True,
                'show_subdepartments': True,
                'show_project_types': True,
                'show_procurement_methods': True,
                'show_companies': True,
                'max_selections': 10
            }
        )
        
        # Get filter values and apply them
        filter_values = advanced_filters.render()
        
        # Apply filters to search results
        filtered_df = projects_df.copy()
        
        # Apply value range filter
        if filter_values['value_min'] is not None:
            filtered_df = filtered_df[
                filtered_df['sum_price_agree'] >= filter_values['value_min'] * 1e6
            ]
        if filter_values['value_max'] is not None:
            filtered_df = filtered_df[
                filtered_df['sum_price_agree'] <= filter_values['value_max'] * 1e6
            ]
        
        # Apply date range filter - Convert Timestamp to date for comparison
        filtered_df = filtered_df[
            (pd.to_datetime(filtered_df['transaction_date']).dt.date >= filter_values['date_start']) &
            (pd.to_datetime(filtered_df['transaction_date']).dt.date <= filter_values['date_end'])
        ]
        
        # Apply department filters
        if filter_values['departments']:
            filtered_df = filtered_df[
                filtered_df['dept_name'].isin(filter_values['departments'])
            ]
        
        if filter_values['subdepartments']:
            filtered_df = filtered_df[
                filtered_df['dept_sub_name'].isin(filter_values['subdepartments'])
            ]
        
        # Apply project type filters
        if filter_values['project_types']:
            filtered_df = filtered_df[
                filtered_df['project_type_name'].isin(filter_values['project_types'])
            ]
        
        if filter_values['procurement_methods']:
            filtered_df = filtered_df[
                filtered_df['purchase_method_name'].isin(filter_values['procurement_methods'])
            ]
        
        if filter_values['companies']:
            filtered_df = filtered_df[
                filtered_df['winner'].isin(filter_values['companies'])
            ]
        
        # Update projects_df with filtered results
        projects_df = filtered_df
        
        # Display results if we have any after filtering
        if len(projects_df) > 0:
            # Calculate metrics
            with LoadingState("Calculating metrics..."):
                metrics = project_metrics.calculate_summary_metrics(projects_df)
                time_trends = project_trends.analyze_monthly_trends(projects_df)
            
            # Display metrics
            st.subheader("Search Results Overview")
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                MetricCard(
                    title="Total Projects",
                    value=metrics['total_projects'],
                    formatter=lambda x: f"{x:,}"
                ).render()
            
            with col2:
                MetricCard(
                    title="Total Value",
                    value=metrics['total_value'],
                    prefix="฿",
                    suffix="M",
                    formatter=lambda x: f"{x/1e6:,.2f}"
                ).render()
            
            with col3:
                MetricCard(
                    title="Average Value",
                    value=metrics['average_value'],
                    prefix="฿",
                    suffix="M",
                    formatter=lambda x: f"{x/1e6:,.2f}"
                ).render()
            
            with col4:
                MetricCard(
                    title="Companies",
                    value=metrics['unique_companies'],
                    formatter=lambda x: f"{x:,}"
                ).render()
            
            with col5:
                MetricCard(
                    title="Price Cut",
                    value=metrics['price_cut'],
                    suffix="%",
                    formatter=lambda x: f"{x:.1f}",
                    color="success" if metrics['price_cut'] > 0 else "danger"
                ).render()
            
            # Distribution Overview
            st.subheader("Purchase Methods & Project Types Distribution")
            
            # Purchase Methods Distribution
            st.write("Top Method:", 
                    f"{metrics['purchase_methods']['top_method']} "
                    f"({metrics['purchase_methods']['top_method_percentage']:.1f}%)")
            
            # Project Types Distribution
            st.write("Top Type:", 
                    f"{metrics['project_types']['top_type']} "
                    f"({metrics['project_types']['top_type_percentage']:.1f}%)")
            
            # Quick Statistics
            st.subheader("📊 Quick Statistics")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("Department Overview")
                if metrics['department_stats']:
                    for dept in metrics['department_stats']:
                        st.write(f"**{dept['dept_name']}**")
                        st.write(f"Projects: {dept['projects']:,}")
                        st.write(f"Value: ฿{dept['value']/1e6:,.1f}M")
                        st.write(f"Companies: {dept['companies']:,}")
            
            with col2:
                st.write("Top Companies")
                if metrics['top_companies']:
                    for company in metrics['top_companies']:
                        st.write(f"**{company['company']}**")
                        st.write(f"฿{company['value']/1e6:,.1f}M ({company['projects']} projects)")
            
            with col3:
                st.write("Procurement Methods")
                for method, count in metrics['purchase_methods']['distribution'].items():
                    percentage = metrics['purchase_methods']['percentages'][method]
                    st.write(f"**{method}**")
                    st.write(f"{count:,} projects ({percentage:.1f}%)")
            
            # Display visualizations
            st.subheader("Analysis")
            
            tab1, tab2 = st.tabs(["Company Distribution", "Department Distribution"])
            
            with tab1:
                # Company distribution
                if len(projects_df) > 0:
                    # Aggregate by company
                    company_df = projects_df.groupby('winner').agg(
                        project_count=('project_name', 'count'),
                        total_value=('sum_price_agree', 'sum')
                    ).reset_index()
                    
                    company_df = company_df.sort_values('total_value', ascending=False)
                    
                    # Create treemap
                    company_treemap = TreemapChart(
                        data=company_df,
                        value_column='total_value',
                        path_columns=['winner'],
                        title="Project Value by Company",
                        height=400,
                        color_scheme='Blues',
                        max_items=20
                    )
                    company_treemap.render()
            
            with tab2:
                # Department distribution
                if len(projects_df) > 0:
                    # Aggregate by department
                    dept_df = projects_df.groupby('dept_name').agg(
                        project_count=('project_name', 'count'),
                        total_value=('sum_price_agree', 'sum')
                    ).reset_index()
                    
                    dept_df = dept_df.sort_values('total_value', ascending=False)
                    
                    # Create treemap
                    dept_treemap = TreemapChart(
                        data=dept_df,
                        value_column='total_value',
                        path_columns=['dept_name'],
                        title="Project Value by Department",
                        height=400,
                        color_scheme='Greens',
                        max_items=20
                    )
                    dept_treemap.render()
            
            # Time-based Analysis
            st.subheader("Project Timeline")
            
            if len(projects_df) > 0:
                # Prepare timeline data
                timeline_df = projects_df.copy()
                timeline_df['year'] = pd.to_datetime(timeline_df['transaction_date']).dt.year
                timeline_df['value_millions'] = timeline_df['sum_price_agree'] / 1e6
                
                # Group by year and value range
                timeline_data = []
                
                # Define value ranges
                VALUE_RANGES = [
                    {'name': '>300M', 'min': 300, 'max': float('inf')},
                    {'name': '100-300M', 'min': 100, 'max': 300},
                    {'name': '50-100M', 'min': 50, 'max': 100},
                    {'name': '10-50M', 'min': 10, 'max': 50},
                    {'name': '0-10M', 'min': 0, 'max': 10}
                ]
                
                # Create data for each range
                for value_range in VALUE_RANGES:
                    range_df = timeline_df[
                        (timeline_df['value_millions'] >= value_range['min']) &
                        (timeline_df['value_millions'] < value_range['max'])
                    ]
                    
                    if not range_df.empty:
                        year_values = range_df.groupby('year')['value_millions'].sum().reset_index()
                        year_values['value_range'] = value_range['name']
                        timeline_data.append(year_values)
                
                if timeline_data:
                    timeline_df = pd.concat(timeline_data)
                    
                    # Create stacked bar chart
                    timeline_chart = StackedBarChart(
                        data=timeline_df,
                        x_column='year',
                        y_column='value_millions',
                        color_column='value_range',
                        title="Project Values by Year",
                        height=400
                    )
                    timeline_chart.render(show_totals=True)
            
            # Analyze trends
            with LoadingState("Analyzing trends..."):
                trends = project_trends.analyze_monthly_trends(projects_df)
                value_dist = project_trends.analyze_value_distribution(projects_df)
                insights = project_trends.get_trend_insights(trends)
            
            # Display insights if available
            if insights:
                st.subheader("Key Insights")
                cols = st.columns(len(insights))
                for i, insight in enumerate(insights):
                    with cols[i]:
                        MetricCard(
                            title=insight['title'],
                            value=insight['description'],
                            formatter=lambda x: x  # Pass through formatter
                        ).render()
            
            # Display projects table
            st.subheader("Projects")
            projects_table = ProjectsTable(projects_df)
            projects_table.render(
                allow_column_config=True,
                show_stats=True
            )
        else:
            st.info("No projects match the selected filters")
    
    elif keyword_params and keyword_params.get('include_keywords'):
        st.info("No projects found matching your search criteria")
    
    else:
        st.info("Enter keywords to search for projects")

if __name__ == "__main__":
    AdvancedSearch() 