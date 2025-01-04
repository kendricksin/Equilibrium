# src/pages/CompanyComparison.py

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from components.layout.Header import Header
from components.layout.MetricsSummary import MetricsSummary
from services.analytics.company_comparison import CompanyComparisonService
from state.session import SessionState

st.set_page_config(layout="wide")

def CompanyComparison():
    """Company comparison page with price cut analysis"""
    # Initialize session state
    SessionState.initialize_state()
    
    # Get selected companies and data
    selected_companies = SessionState.get_selected_companies()
    df = SessionState.get_filtered_data()
    
    if not selected_companies or len(selected_companies) < 2:
        st.warning("Please select at least 2 companies to compare")
        return
    
    if df is None or df.empty:
        st.warning("No data available for analysis")
        return
    
    # Initialize comparison service
    comparison_service = CompanyComparisonService()
    
    # Header
    st.title("Company Price Cut Analysis")
    
    # Calculate metrics
    metrics_df = comparison_service.calculate_price_cuts(df, selected_companies)
    yearly_cuts_df = comparison_service.calculate_yearly_price_cuts(df, selected_companies)
    
    # Display summary table
    st.header("Summary Comparison")
    
    # Format the metrics table
    display_df = metrics_df.copy()
    display_df['price_cut_percent'] = display_df['price_cut_percent'].round(2).astype(str) + '%'
    display_df['avg_price_agree'] = (display_df['avg_price_agree'] / 1e6).round(2).astype(str) + ' MB'
    display_df.columns = ['Company Name', 'Price Cut %', 'Avg Project Value', 'Project Count']
    
    st.dataframe(
        display_df,
        hide_index=True,
        use_container_width=True
    )
    
    # Horizontal bar chart of price cuts
    st.header("Price Cut Comparison")
    
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=metrics_df['price_cut_percent'],
        y=metrics_df['company_name'],
        orientation='h',
        text=metrics_df['price_cut_percent'].round(2).astype(str) + '%',
        textposition='auto',
    ))
    
    fig_bar.update_layout(
        title="Companies Ranked by Price Cut",
        xaxis_title="Price Cut %",
        yaxis_title="Company",
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # Line chart of yearly price cut trends
    st.header("Price Cut Trends")
    
    fig_line = px.line(
        yearly_cuts_df,
        x='year',
        y='price_cut_percent',
        color='company_name',
        title="Yearly Price Cut Trends",
        labels={
            'year': 'Budget Year',
            'price_cut_percent': 'Price Cut %',
            'company_name': 'Company'
        }
    )
    
    fig_line.update_traces(mode='lines+markers')
    fig_line.update_layout(height=400)
    
    st.plotly_chart(fig_line, use_container_width=True)
    
    # Detailed company metrics
    st.header("Individual Company Details")
    
    for company in selected_companies:
        with st.expander(f"📊 {company}"):
            details = comparison_service.get_company_details(df, company)
            
            if details:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Projects", f"{details['total_projects']:,}")
                    st.metric("Price Cut", f"{details['price_cut_percent']:.2f}%")
                
                with col2:
                    st.metric("Total Value", f"฿{details['total_value']/1e6:.2f}M")
                    st.metric("Departments", details['departments'])
                
                with col3:
                    st.metric("Avg Project Value", f"฿{details['avg_project_value']/1e6:.2f}M")
                    st.metric("Years Active", details['years_active'])

if __name__ == "__main__":
    CompanyComparison()