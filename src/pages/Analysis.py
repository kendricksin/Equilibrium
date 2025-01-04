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
from services.cache.filter_cache import get_filtered_data

st.set_page_config(layout="wide")

def Analysis():
    """Analysis page with enhanced filter responsiveness and loading states"""
    # Initialize session state
    SessionState.initialize_state()

    # Render sidebar and get filters
    filters = Sidebar(
        filters=SessionState.get_filters(),
        selected_companies=SessionState.get_selected_companies(),
        on_filter_change=lambda f: st.session_state.update({'filtered_df': None})
    )
    
    # Render header
    Header(current_page="Analysis")
    
    # Handle filter changes and data loading
    if st.session_state.filters_applied:
        if SessionState.get_filtered_data() is None:
            with st.spinner("Loading projects..."):
                df = get_filtered_data(filters)
                if df is not None and not df.empty:
                    SessionState.set_filtered_data(df)
                    st.rerun()
        
        df = SessionState.get_filtered_data()
        if df is not None and not df.empty:
            # Initialize services
            analytics = AnalyticsService()
            insights = InsightsService()
            
            # Render metrics summary
            MetricsSummary(df)
            
            # Create tabs for different analyses
            tab1, tab2, tab3 = st.tabs([
                "📈 Overview", 
                "🏢 Department Analysis",
                "🤝 Company Analysis"
            ])
            
            with tab1:
                st.header("Overview Metrics")
                
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
                
                # Time series analysis with progress indicator
                st.subheader("Project Timeline")
                with st.spinner("Generating timeline..."):
                    monthly_data = df.resample('ME', on='transaction_date').agg({
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
            
            with tab2:
                st.header("Department Analysis")
                with st.spinner("Analyzing departments..."):
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
                    
                    # Department details table
                    st.subheader("Department Details")
                    st.dataframe(
                        dept_metrics.style.format({
                            'Total Value': '฿{:,.2f}M',
                            'Avg Value': '฿{:,.2f}M'
                        }),
                        use_container_width=True
                    )
            
            with tab3:
                st.header("Company Analysis")
                with st.spinner("Analyzing companies..."):
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
            with st.spinner("Generating insights..."):
                insights_list = insights.generate_key_insights(df)
                
                for insight in insights_list:
                    st.markdown(f"• {insight}")
        else:
            st.info("No projects found matching the current filters.")
    else:
        st.info("Please apply filters to view analysis.")

if __name__ == "__main__":
    Analysis()