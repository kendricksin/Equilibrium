import streamlit as st
import pandas as pd
from datetime import datetime
import logging
from services.database.mongodb import MongoDBService
from typing import List, Dict, Any, Optional
import plotly.graph_objects as go

logger = logging.getLogger(__name__)

def get_company_quarterly_trends(projects_df: pd.DataFrame, company_names: List[str]) -> List[Dict[str, Any]]:
    """Calculate quarterly project value trends for companies"""
    quarterly_data = []
    
    # Convert to datetime if not already
    projects_df['transaction_date'] = pd.to_datetime(projects_df['transaction_date'])
    
    # Add quarter column
    projects_df['quarter'] = projects_df['transaction_date'].dt.to_period('Q')
    
    # Calculate quarterly totals for each company
    for quarter in sorted(projects_df['quarter'].unique()):
        quarter_data = {'quarter': str(quarter)}
        
        for company in company_names:
            company_quarter_data = projects_df[
                (projects_df['quarter'] == quarter) & 
                (projects_df['winner'] == company)
            ]
            quarter_data[company] = company_quarter_data['sum_price_agree'].sum() / 1e6  # Convert to millions
            
        quarterly_data.append(quarter_data)
    
    return quarterly_data

def get_department_distribution(projects_df: pd.DataFrame, company_names: List[str]) -> List[Dict[str, Any]]:
    """Calculate department distribution for companies"""
    dept_data = []
    
    # Calculate total projects per company for percentage calculation
    company_totals = {
        company: len(projects_df[projects_df['winner'] == company])
        for company in company_names
    }
    
    # Get all unique departments
    departments = sorted(projects_df['dept_name'].unique())
    
    for dept in departments:
        dept_info = {'department': dept}
        
        for company in company_names:
            dept_count = len(projects_df[
                (projects_df['dept_name'] == dept) & 
                (projects_df['winner'] == company)
            ])
            # Calculate percentage
            if company_totals[company] > 0:
                dept_info[company] = (dept_count / company_totals[company]) * 100
            else:
                dept_info[company] = 0
            
        dept_data.append(dept_info)
    
    return dept_data

def get_procurement_distribution(projects_df: pd.DataFrame, company_names: List[str]) -> List[Dict[str, Any]]:
    """Calculate procurement method distribution for companies"""
    proc_data = []
    
    # Calculate total projects per company
    company_totals = {
        company: len(projects_df[projects_df['winner'] == company])
        for company in company_names
    }
    
    # Get all unique procurement methods
    methods = sorted(projects_df['purchase_method_name'].unique())
    
    for method in methods:
        method_info = {'method': method}
        
        for company in company_names:
            method_count = len(projects_df[
                (projects_df['purchase_method_name'] == method) & 
                (projects_df['winner'] == company)
            ])
            # Calculate percentage
            if company_totals[company] > 0:
                method_info[company] = (method_count / company_totals[company]) * 100
            else:
                method_info[company] = 0
            
        proc_data.append(method_info)
    
    return proc_data

def create_distribution_chart(data: List[Dict[str, Any]], companies: List[str], title: str) -> go.Figure:
    """Create a horizontal stacked bar chart for distribution comparison"""
    fig = go.Figure()
    
    # Colors for companies
    colors = ['rgb(31, 119, 180)', 'rgb(255, 127, 14)']
    
    for i, company in enumerate(companies):
        fig.add_trace(go.Bar(
            y=[item['department' if 'department' in item else 'method'] for item in data],
            x=[item[company] for item in data],
            name=company,
            orientation='h',
            marker_color=colors[i],
        ))
    
    fig.update_layout(
        title=title,
        barmode='group',
        yaxis={'categoryorder': 'total ascending'},
        height=max(400, len(data) * 30),  # Dynamic height based on number of items
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title="Percentage of Projects (%)",
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99
        )
    )
    
    return fig

def create_trend_chart(data: List[Dict[str, Any]], companies: List[str]) -> go.Figure:
    """Create a line chart for quarterly trends"""
    fig = go.Figure()
    
    # Colors for companies
    colors = ['rgb(31, 119, 180)', 'rgb(255, 127, 14)']
    
    for i, company in enumerate(companies):
        fig.add_trace(go.Scatter(
            x=[d['quarter'] for d in data],
            y=[d[company] for d in data],
            name=company,
            line=dict(color=colors[i], width=2),
            mode='lines+markers'
        ))
    
    fig.update_layout(
        title="Quarterly Project Values",
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title="Quarter",
        yaxis_title="Project Value (Million ฿)",
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99
        )
    )
    
    return fig

@st.cache_data(ttl=3600)
def get_all_companies():
    """Get all companies with caching"""
    mongo = MongoDBService()
    mongo.ensure_connection()  # Ensure fresh connection
    
    try:
        collection = mongo.get_collection("companies")
        
        # Convert cursor to list immediately to avoid cursor timeout
        companies = list(collection.find(
            {},
            {"winner": 1, "project_count": 1, "project_ids": 1}
        ).sort("project_count", -1))
        
        logger.info(f"Retrieved {len(companies)} companies from database")
        return companies
        
    except Exception as e:
        logger.error(f"Error retrieving companies: {e}")
        return []

def CompanySearch():
    """Enhanced company search and comparison page"""
    st.set_page_config(layout="wide")
    
    # Initialize MongoDB service
    mongo = MongoDBService()
    mongo.ensure_connection()
    
    try:
        # Get companies data
        companies = get_all_companies()
        
        if not companies:
            st.error("Unable to retrieve company data. Please try again later.")
            return
        
        # Create company options
        company_options = [""]
        company_map = {}
        for company in companies:
            actual_count = len(company.get('project_ids', []))
            option_text = f"{company['winner']} ({actual_count} projects)"
            company_options.append(option_text)
            company_map[option_text] = company['winner']
        
        # Search section
        st.markdown("### 🔍 Company Search")
        st.markdown("Type to search companies - fuzzy matching is supported")
        
        # Company selection
        col1, col2 = st.columns(2)
        selected_companies = []
        company_data = []
        
        with col1:
            st.markdown("##### Company 1")
            selected1 = st.selectbox(
                "Select first company",
                options=company_options,
                key="company1",
                placeholder="Search companies..."
            )
            if selected1:
                company_name = company_map[selected1]
                selected_companies.append(company_name)
                company_doc = get_company_data(company_name, mongo)
                if company_doc:
                    company_data.append(company_doc)
        
        with col2:
            st.markdown("##### Company 2")
            available_options = [opt for opt in company_options if opt not in [selected1]]
            selected2 = st.selectbox(
                "Select second company",
                options=available_options,
                key="company2",
                placeholder="Search companies..."
            )
            if selected2:
                company_name = company_map[selected2]
                selected_companies.append(company_name)
                company_doc = get_company_data(company_name, mongo)
                if company_doc:
                    company_data.append(company_doc)
        
        # Display comparison if companies are selected
        if len(company_data) > 0:
            st.markdown("### 📊 Company Overview")
            
            # Basic metrics
            cols = st.columns(len(company_data))
            for idx, (col, data) in enumerate(zip(cols, company_data)):
                with col:
                    st.markdown(f"#### {data['winner']}")
                    actual_project_count = len(data['project_ids'])
                    st.metric("Total Projects", f"{actual_project_count:,}")
                    st.metric("Total Value", f"฿{data['total_value']/1e6:.2f}M")
                    st.metric("Average Project Value", f"฿{data['avg_project_value']/1e6:.2f}M")
                    st.metric("Active Years", data['active_years'])
            
            # Get project details for visualizations
            if company_data:
                all_project_ids = []
                for data in company_data:
                    all_project_ids.extend(data.get('project_ids', []))
                
                if all_project_ids:
                    projects_collection = mongo.get_collection("projects")
                    projects = list(projects_collection.find(
                        {"project_id": {"$in": all_project_ids}},
                        {
                            "project_id": 1,
                            "project_name": 1,
                            "winner": 1,
                            "dept_name": 1,
                            "purchase_method_name": 1,
                            "transaction_date": 1,
                            "sum_price_agree": 1,
                            "price_build": 1
                        }
                    ))
                    
                    if projects:
                        df = pd.DataFrame(projects)
                        
                        # Create visualizations
                        st.markdown("### 📈 Comparative Analysis")
                        
                        # Department Distribution
                        dept_data = get_department_distribution(df, selected_companies)
                        dept_chart = create_distribution_chart(
                            dept_data, 
                            selected_companies, 
                            "Department Distribution"
                        )
                        st.plotly_chart(dept_chart, use_container_width=True)
                        
                        # Procurement Methods
                        proc_data = get_procurement_distribution(df, selected_companies)
                        proc_chart = create_distribution_chart(
                            proc_data, 
                            selected_companies, 
                            "Procurement Methods"
                        )
                        st.plotly_chart(proc_chart, use_container_width=True)
                        # Quarterly Trends
                        quarterly_data = get_quarterly_trends(df, selected_companies)
                        trend_chart = create_trend_chart(quarterly_data, selected_companies)
                        st.plotly_chart(trend_chart, use_container_width=True)
                        
                        # Additional Analysis Section
                        st.markdown("### 🔍 Detailed Analysis")
                        
                        # Project Size Distribution
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### Project Size Distribution")
                            for company in selected_companies:
                                company_df = df[df['winner'] == company]
                                fig = go.Figure()
                                fig.add_trace(go.Box(
                                    y=company_df['sum_price_agree'] / 1e6,
                                    name=company,
                                    boxpoints='all',
                                    jitter=0.3,
                                    pointpos=-1.8
                                ))
                                fig.update_layout(
                                    title=f"{company} Project Values",
                                    yaxis_title="Project Value (Million ฿)",
                                    showlegend=False,
                                    height=300
                                )
                                st.plotly_chart(fig, use_container_width=True)
                        
                        with col2:
                            st.markdown("#### Price Cut Analysis")
                            for company in selected_companies:
                                company_df = df[df['winner'] == company]
                                company_df['price_cut'] = ((company_df['sum_price_agree'] / company_df['price_build']) - 1) * 100
                                fig = go.Figure()
                                fig.add_trace(go.Histogram(
                                    x=company_df['price_cut'],
                                    name=company,
                                    nbinsx=20
                                ))
                                fig.update_layout(
                                    title=f"{company} Price Cuts",
                                    xaxis_title="Price Cut (%)",
                                    yaxis_title="Number of Projects",
                                    showlegend=False,
                                    height=300
                                )
                                st.plotly_chart(fig, use_container_width=True)
                        
                        # Projects Table
                        st.markdown("### 📋 Project Details")
                        from components.tables.ProjectsTable import ProjectsTable
                        ProjectsTable(
                            df=df,
                            show_search=True,
                            key_prefix="company_comparison_"
                        )
                        
                        # Export functionality
                        col1, col2, col3 = st.columns([2,2,1])
                        with col1:
                            csv = df.to_csv(index=False)
                            st.download_button(
                                "📥 Download Project Details",
                                csv,
                                "company_projects_comparison.csv",
                                "text/csv",
                                key='download-projects'
                            )
                        
                        # Export analysis data
                        with col2:
                            analysis_data = {
                                'quarterly_trends': quarterly_data,
                                'department_distribution': dept_data,
                                'procurement_distribution': proc_data
                            }
                            analysis_df = pd.DataFrame(analysis_data)
                            st.download_button(
                                "📥 Download Analysis Data",
                                analysis_df.to_csv(index=False),
                                "company_analysis_data.csv",
                                "text/csv",
                                key='download-analysis'
                            )
                            
    except Exception as e:
        logger.error(f"Error in CompanySearch: {e}")
        st.error("An error occurred while processing your request. Please try again later.")

def get_quarterly_trends(df: pd.DataFrame, companies: List[str]) -> List[Dict[str, Any]]:
    """Calculate quarterly trends for the selected companies"""
    # Convert to datetime and create quarter column
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    df['quarter'] = df['transaction_date'].dt.to_period('Q')
    
    # Calculate quarterly values for each company
    quarterly_data = []
    for quarter in sorted(df['quarter'].unique()):
        quarter_values = {'quarter': str(quarter)}
        
        for company in companies:
            company_quarter = df[
                (df['quarter'] == quarter) &
                (df['winner'] == company)
            ]
            quarter_values[company] = company_quarter['sum_price_agree'].sum() / 1e6
        
        quarterly_data.append(quarter_values)
    
    return quarterly_data

def get_company_data(company_name: str, mongo_service: MongoDBService) -> Optional[Dict]:
    """Get company data with proper connection management"""
    try:
        collection = mongo_service.get_collection("companies")
        company_doc = collection.find_one({"winner": company_name})
        
        if company_doc:
            # Calculate additional metrics
            project_ids = company_doc.get('project_ids', [])
            if project_ids:
                projects = list(mongo_service.get_collection("projects").find(
                    {"project_id": {"$in": project_ids}},
                    {"sum_price_agree": 1, "transaction_date": 1}
                ))
                
                if projects:
                    df = pd.DataFrame(projects)
                    company_doc['total_value'] = df['sum_price_agree'].sum()
                    company_doc['avg_project_value'] = df['sum_price_agree'].mean()
                    
                    # Calculate active years
                    df['year'] = pd.to_datetime(df['transaction_date']).dt.year
                    company_doc['active_years'] = len(df['year'].unique())
        
        return company_doc
        
    except Exception as e:
        logger.error(f"Error fetching company data for {company_name}: {e}")
        return None

if __name__ == "__main__":
    CompanySearch()