import streamlit as st
import pandas as pd
from datetime import datetime
import logging
from services.database.mongodb import MongoDBService
from typing import List, Dict, Any, Optional
import plotly.graph_objects as go
from components.tables.ProjectsTable import ProjectsTable
from components.layout.PageLayout import PageLayout


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

def calculate_competitive_metrics(df: pd.DataFrame, companies: List[str]) -> Dict[str, Any]:
    """Calculate competitive analysis metrics between companies"""
    try:
        company1, company2 = companies
        
        # Get departments for each company
        depts1 = set(df[df['winner'] == company1]['dept_name'].unique())
        depts2 = set(df[df['winner'] == company2]['dept_name'].unique())
        shared_depts = depts1.intersection(depts2)
        
        # Get projects in shared departments
        shared_dept_projects = df[df['dept_name'].isin(shared_depts)]
        competitions = shared_dept_projects[shared_dept_projects['winner'].isin(companies)]
        
        # Calculate win rates
        wins = competitions['winner'].value_counts()
        win_rates = (wins / len(competitions) * 100).to_dict()
        
        # Calculate price cuts
        def get_price_cut(company_df):
            return ((company_df['sum_price_agree'].sum() / company_df['price_build'].sum()) - 1) * 100
        
        price_cuts = {
            company: get_price_cut(df[df['winner'] == company])
            for company in companies
        }
        
        # Calculate project overlap percentage
        total_projects = len(df[df['winner'].isin(companies)])
        overlap_percentage = (len(competitions) / total_projects * 100)
        
        return {
            'shared_departments': len(shared_depts),
            'total_departments': {
                company1: len(depts1),
                company2: len(depts2)
            },
            'total_competitions': len(competitions),
            'win_rates': win_rates,
            'price_cuts': price_cuts,
            'price_competition': abs(price_cuts[company1] - price_cuts[company2]),
            'overlap_percentage': overlap_percentage
        }
        
    except Exception as e:
        logger.error(f"Error calculating competitive metrics: {e}")
        return {}

def display_competitive_analysis(metrics: Dict[str, Any], company1: str, company2: str):
    """Display competitive analysis metrics in Streamlit"""
    st.markdown("### 🤝 Competitive Analysis")
    
    # Create three columns for key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Shared Departments",
            f"{metrics['shared_departments']} depts",
            f"{metrics['overlap_percentage']:.1f}% overlap"
        )
    
    with col2:
        st.metric(
            "Head-to-Head Projects",
            f"{metrics['total_competitions']} projects",
            f"{metrics['win_rates'].get(company1, 0):.1f}% win rate"
        )
    
    with col3:
        price_diff = metrics['price_competition']
        better_pricer = company1 if metrics['price_cuts'][company1] < metrics['price_cuts'][company2] else company2
        st.metric(
            "Price Competition",
            f"{abs(price_diff):.1f}% diff",
            f"{better_pricer} more competitive"
        )
    
    # Create win rate visualization
    st.markdown("#### Win Rates in Shared Departments")
    
    # Use streamlit progress bars for win rates
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**{company1}**")
        st.progress(metrics['win_rates'].get(company1, 0) / 100)
        st.caption(f"{metrics['win_rates'].get(company1, 0):.1f}%")
    
    with col2:
        st.markdown(f"**{company2}**")
        st.progress(metrics['win_rates'].get(company2, 0) / 100)
        st.caption(f"{metrics['win_rates'].get(company2, 0):.1f}%")

def display_comparative_analysis(df: pd.DataFrame, selected_companies: List[str]):
    """Display comparative analysis using compact distribution bars"""
    st.markdown("### 📈 Comparative Analysis")
    
    from components.layout.MetricsSummary import create_distribution_bar
    
    # Department Distribution section
    st.markdown("#### Department Distribution")
    for company in selected_companies:
        company_df = df[df['winner'] == company]
        dept_counts = company_df['dept_name'].value_counts()
        fig = create_distribution_bar(dept_counts, company)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # Show top departments as caption
        top_depts = dept_counts.head(3)
        dept_text = ", ".join(f"{dept} ({count} projects)" for dept, count in top_depts.items())
        st.caption(f"Top departments: {dept_text}")
    
    # Procurement Methods section
    st.markdown("#### Procurement Methods")
    for company in selected_companies:
        company_df = df[df['winner'] == company]
        method_counts = company_df['purchase_method_name'].value_counts()
        fig = create_distribution_bar(method_counts, company)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # Show top methods as caption
        top_method = method_counts.index[0]
        method_share = method_counts.iloc[0] / len(company_df) * 100
        st.caption(f"Primary method: {top_method} ({method_share:.1f}%)")

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

def display_detailed_analysis(df: pd.DataFrame, selected_companies: List[str]):
    """Display detailed analysis with horizontal layout and stacked comparisons"""
    st.markdown("### 🔍 Detailed Analysis")
    
    # Project Size Distribution with both companies on same plot
    fig = go.Figure()
    colors = ['rgb(31, 119, 180)', 'rgb(255, 127, 14)']
    
    for i, company in enumerate(selected_companies):
        company_df = df[df['winner'] == company]
        values = company_df['sum_price_agree'] / 1e6
        
        fig.add_trace(go.Box(
            x=values,  # Changed to x for horizontal orientation
            name=company,
            boxpoints='all',
            jitter=0.3,
            pointpos=-1.8,
            orientation='h',  # Make boxes horizontal
            marker_color=colors[i],
            boxmean=True  # Show mean line
        ))

    fig.update_layout(
        title="Project Value Distribution Comparison",
        height=400,
        xaxis_title="Project Value (Million ฿)",
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False
        ),
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray',
            zeroline=True,
            zerolinecolor='lightgray'
        ),
        plot_bgcolor='white'
    )
    st.plotly_chart(fig, use_container_width=True)

    # Add summary statistics below
    summary_data = []
    for company in selected_companies:
        company_df = df[df['winner'] == company]
        values = company_df['sum_price_agree'] / 1e6
        summary_data.append({
            'Company': company,
            'Median': f"฿{values.median():.1f}M",
            'Average': f"฿{values.mean():.1f}M",
            'Min-Max': f"฿{values.min():.1f}M - ฿{values.max():.1f}M",
            'Projects': f"{len(values):,}"
        })
    
    # Display summary as a table
    st.markdown("**Project Value Statistics**")
    st.table(pd.DataFrame(summary_data).set_index('Company'))

def CompanySearch():
    """Enhanced company search and comparison page"""

    # Initialize session state
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        st.session_state.default_company = None
        st.session_state.company1 = None
        st.session_state.company2 = None
    
    # Initialize MongoDB service
    mongo = MongoDBService()
    mongo.ensure_connection()
    
    try:
        # Get companies data
        companies = get_all_companies()
        
        if not companies:
            st.error("Unable to retrieve company data. Please try again later.")
            return
        
        # Create company options with random default selection
        import random
        company_options = [""]
        company_map = {}
        
        # Filter out companies with very few projects (e.g., less than 5)
        valid_companies = [c for c in companies if len(c.get('project_ids', [])) >= 5]
        
        for company in valid_companies:
            actual_count = len(company.get('project_ids', []))
            option_text = f"{company['winner']} ({actual_count} projects)"
            company_options.append(option_text)
            company_map[option_text] = company['winner']
        
        # Get default selection if not already in session state
        if 'default_company' not in st.session_state:
            # Randomly select a company with at least 5 projects
            default_company = random.choice(company_options[1000:2000])  # Skip empty option
            st.session_state.default_company = default_company
        
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
                    
                    # Display distributions using compact bars
                    display_comparative_analysis(df, selected_companies)

                    # Calculate competitive metrics
                    competitive_metrics = calculate_competitive_metrics(df, selected_companies)
                    
                    # Display competitive analysis
                    display_competitive_analysis(competitive_metrics, *selected_companies)
                        
                        
                    # Display detailed analysis
                    display_detailed_analysis(df, selected_companies)
                    
                    # Projects Table
                    st.markdown("### 📋 Project Details")
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
    PageLayout(CompanySearch)