# src/pages/Analysis.py

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from components.layout.Header import Header
from components.layout.Sidebar import Sidebar
from components.layout.MetricsSummary import MetricsSummary
from services.analytics.analytics_service import AnalyticsService
from services.analytics.insights_service import InsightsService
from state.session import SessionState

def Analysis():
    """Analysis page with detailed metrics and visualizations"""
    # Initialize session state
    SessionState.initialize_state()
    
    # Render header
    Header(current_page="Analysis")
    
    # Get filtered data
    df = SessionState.get_filtered_data()
    if df is None or df.empty:
        st.warning("Please apply filters and select data to analyze")
        return
    
    # Initialize services
    analytics = AnalyticsService()
    insights = InsightsService()
    
    # Render metrics summary
    MetricsSummary(df)
    
    # Main content
    st.header("Detailed Analysis")
    
    # Top-level metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Average Project Value",
            f"฿{df['sum_price_agree'].mean()/1e6:,.2f}M"
        )
    
    with col2:
        st.metric(
            "Total Companies",
            f"{df['winner'].nunique():,}"
        )
    
    with col3:
        st.metric(
            "Total Departments",
            f"{df['dept_name'].nunique():,}"
        )
    
    # Time series analysis
    st.subheader("Project Timeline")
    monthly_data = df.resample('M', on='transaction_date').agg({
        'project_name': 'count',
        'sum_price_agree': 'sum'
    })
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly_data.index,
        y=monthly_data['project_name'],
        name="Project Count",
        line=dict(color='blue')
    ))
    
    fig.add_trace(go.Scatter(
        x=monthly_data.index,
        y=monthly_data['sum_price_agree'] / 1e6,
        name="Total Value (M฿)",
        yaxis="y2",
        line=dict(color='red')
    ))
    
    fig.update_layout(
        title="Projects and Values Over Time",
        yaxis=dict(title="Number of Projects"),
        yaxis2=dict(title="Total Value (M฿)", overlaying="y", side="right"),
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Department analysis
    st.subheader("Department Analysis")
    
    dept_metrics = df.groupby('dept_name').agg({
        'project_name': 'count',
        'sum_price_agree': ['sum', 'mean']
    })
    
    dept_metrics.columns = ['Projects', 'Total Value', 'Avg Value']
    dept_metrics = dept_metrics.sort_values('Total Value', ascending=False)
    
    fig_dept = px.bar(
        dept_metrics,
        x=dept_metrics.index,
        y='Total Value',
        title="Total Project Value by Department"
    )
    
    st.plotly_chart(fig_dept, use_container_width=True)
    
    # Company analysis
    st.subheader("Company Analysis")
    
    company_metrics = analytics.analyze_company_performance(df)
    top_companies = company_metrics.sort_values('total_value', ascending=False).head(10)
    
    fig_company = px.bar(
        top_companies,
        x=top_companies.index,
        y='market_share',
        title="Top 10 Companies by Market Share"
    )
    
    st.plotly_chart(fig_company, use_container_width=True)
    
    # Competitive landscape
    st.subheader("Competitive Landscape")
    landscape = analytics.analyze_competitive_landscape(df)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Market Concentration", landscape['market_concentration'])
        st.metric("Top 3 Concentration", f"{landscape['top_3_concentration']:.1f}%")
    
    with col2:
        st.metric("HHI Index", f"{landscape['hhi']:.0f}")
        st.metric("Total Players", landscape['total_players'])
    
    # Insights
    st.header("Key Insights")
    insights_list = insights.generate_key_insights(df)
    
    for insight in insights_list:
        st.markdown(f"• {insight}")

if __name__ == "__main__":
    Analysis()