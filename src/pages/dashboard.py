# pages/dashboard_analysis.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
from pymongo import MongoClient
import logging
from special_functions.metrics import display_metrics_dashboard
from special_functions.filter_cache import get_filtered_data
from special_functions.department_cache import render_sidebar_filters

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_time_series(df):
    """Create time series analysis of projects over time"""
    monthly_projects = df.resample('M', on='transaction_date')['project_name'].count()
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=monthly_projects.index,
            y=monthly_projects.values,
            mode='lines+markers',
            name='Projects'
        )
    )
    fig.update_layout(
        title='Projects Over Time',
        xaxis_title='Date',
        yaxis_title='Number of Projects',
        height=400
    )
    return fig

def create_department_distribution(df):
    """Create department distribution visualization"""
    dept_counts = df['dept_name'].value_counts().head(10)
    fig = go.Figure(
        go.Bar(
            x=dept_counts.values,
            y=dept_counts.index,
            orientation='h'
        )
    )
    fig.update_layout(
        title='Top 10 Departments by Project Count',
        xaxis_title='Number of Projects',
        yaxis_title='Department',
        height=400
    )
    return fig

def create_price_distribution(df):
    """Create price distribution visualization"""
    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=df['sum_price_agree'] / 1e6,  # Convert to millions
            nbinsx=30,
            name='Price Distribution'
        )
    )
    fig.update_layout(
        title='Project Price Distribution',
        xaxis_title='Price (Million Baht)',
        yaxis_title='Count',
        height=400
    )
    return fig

def create_status_breakdown(df):
    """Create project status breakdown"""
    if 'status' in df.columns:
        status_counts = df['status'].value_counts()
        fig = go.Figure(
            go.Pie(
                labels=status_counts.index,
                values=status_counts.values,
                hole=0.4
            )
        )
        fig.update_layout(
            title='Project Status Distribution',
            height=400
        )
        return fig
    return None

def dashboard_page():
    st.title("Project Analytics Dashboard")
    
    # Get filters from sidebar
    filters = render_sidebar_filters()
    
    # Validate price range
    if filters['price_start'] > filters['price_end']:
        st.sidebar.error("Start price should be less than end price")
        return
    
    # Apply filters button in sidebar
    if st.sidebar.button("Apply Filters", key="apply_filters"):
        with st.spinner("Fetching and analyzing data..."):
            df = get_filtered_data(filters)
            
            if df is not None and not df.empty:
                # Dashboard-specific filters
                col1, col2 = st.columns(2)
                with col1:
                    selected_year = st.selectbox(
                        "Filter by Year",
                        options=sorted(df['transaction_date'].dt.year.unique()),
                        key="dashboard_year"
                    )
                
                with col2:
                    price_threshold = st.slider(
                        "Price Threshold (Million Baht)",
                        min_value=float(df['sum_price_agree'].min()) / 1e6,
                        max_value=float(df['sum_price_agree'].max()) / 1e6,
                        value=float(df['sum_price_agree'].median()) / 1e6,
                        key="dashboard_price"
                    )
                
                # Filter data based on dashboard-specific filters
                df_filtered = df[
                    (df['transaction_date'].dt.year == selected_year) &
                    (df['sum_price_agree'] <= price_threshold * 1e6)
                ]
                
                # Display key metrics
                st.subheader("Key Metrics")
                metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
                
                with metrics_col1:
                    st.metric(
                        "Total Projects",
                        len(df_filtered),
                        delta=f"{(len(df_filtered) - len(df)) / len(df):.1%}" if len(df) > 0 else "0%"
                    )
                    
                with metrics_col2:
                    total_value = df_filtered['sum_price_agree'].sum() / 1e6
                    st.metric(
                        "Total Value (M฿)",
                        f"{total_value:,.1f}",
                        delta=f"{total_value - df['sum_price_agree'].sum() / 1e6:,.1f}"
                    )
                    
                with metrics_col3:
                    avg_value = df_filtered['sum_price_agree'].mean() / 1e6
                    st.metric(
                        "Avg Value (M฿)",
                        f"{avg_value:,.1f}",
                        delta=f"{avg_value - df['sum_price_agree'].mean() / 1e6:,.1f}"
                    )
                    
                with metrics_col4:
                    dept_count = df_filtered['dept_name'].nunique()
                    st.metric(
                        "Active Departments",
                        dept_count,
                        delta=dept_count - df['dept_name'].nunique()
                    )
                
                # Create and display visualizations
                st.subheader("Project Analysis")
                
                # Time series analysis
                st.plotly_chart(create_time_series(df_filtered), use_container_width=True)
                
                # Department distribution and price distribution
                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(create_department_distribution(df_filtered), use_container_width=True)
                
                with col2:
                    st.plotly_chart(create_price_distribution(df_filtered), use_container_width=True)
                
                # Status breakdown if available
                status_chart = create_status_breakdown(df_filtered)
                if status_chart:
                    st.plotly_chart(status_chart, use_container_width=True)
                
                # Additional analysis section
                st.subheader("Detailed Analysis")
                
                # Add department comparison
                dept_metrics = df_filtered.groupby('dept_name').agg({
                    'project_name': 'count',
                    'sum_price_agree': ['sum', 'mean']
                }).round(2)
                
                dept_metrics.columns = ['Project Count', 'Total Value', 'Average Value']
                dept_metrics = dept_metrics.sort_values('Project Count', ascending=False)
                
                st.dataframe(
                    dept_metrics,
                    use_container_width=True,
                    height=400
                )
                
            else:
                st.warning("No data available for the selected filters. Please adjust your selection.")

if __name__ == "__main__":
    dashboard_page()