import streamlit as st
import pandas as pd
from datetime import datetime
import logging
from services.database.mongodb import MongoDBService
from components.filters.TableFilter import filter_projects
from components.layout.MetricsSummary import MetricsSummary
from components.tables.ProjectsTable import ProjectsTable
from state.session import SessionState

logger = logging.getLogger(__name__)

@st.cache_data(ttl=3600)
def get_company_options():
    """Get all companies with project counts"""
    mongo = MongoDBService()
    try:
        collection = mongo.get_collection("companies")
        companies = list(collection.find(
            {},
            {"winner": 1, "project_count": 1, "project_ids": 1}
        ).sort("project_count", -1))
        
        # Format options with project counts
        options = []
        for company in companies:
            project_count = len(company.get('project_ids', []))
            if project_count >= 5:  # Filter out companies with few projects
                options.append({
                    'name': company['winner'],
                    'display': f"{company['winner']} ({project_count:,} projects)",
                    'count': project_count
                })
        
        return options
    except Exception as e:
        logger.error(f"Error retrieving companies: {e}")
        return []

def CompanySearch():
    """Company search and analysis page"""
    # Initialize session state
    SessionState.initialize_state()
    
    # Initialize MongoDB service
    mongo_service = MongoDBService()
    
    st.markdown("### 🏢 Company Selection")
    
    # Get company options
    companies = get_company_options()
    if not companies:
        st.error("Unable to retrieve company data")
        return
    
    # Create display options and mapping
    company_options = [comp['display'] for comp in companies]
    company_map = {comp['display']: comp['name'] for comp in companies}
    
    # Multi-select for companies
    selected_display = st.multiselect(
        "Select Companies",
        options=company_options,
        help="Select one or more companies to analyze their projects"
    )
    
    # Convert display selections to company names
    selected_companies = [company_map[display] for display in selected_display]
    
    # Search and Clear buttons
    col1, col2 = st.columns([1, 5])
    with col1:
        search_clicked = st.button(
            "🔎 Search",
            type="primary",
            use_container_width=True,
            disabled=not selected_companies
        )
    
    with col2:
        if st.button("❌ Clear Selection", use_container_width=True):
            if "company_results" in st.session_state:
                del st.session_state.company_results
            if "filtered_results" in st.session_state:
                del st.session_state.filtered_results
            st.rerun()

    # Process search
    if search_clicked and selected_companies:
        with st.spinner("Searching projects..."):
            try:
                # Build query for selected companies
                query = {"winner": {"$in": selected_companies}}
                
                # Fetch results
                df = mongo_service.get_projects(
                    query=query,
                    max_documents=20000
                )
                
                if df is not None and not df.empty:
                    st.session_state.company_results = df
                    st.session_state.filtered_results = None
                    st.rerun()
                else:
                    st.warning("No projects found for the selected companies.")
                    
            except Exception as e:
                st.error(f"Error performing search: {str(e)}")

    # Display and filter results
    if st.session_state.get('company_results') is not None:
        df = st.session_state.company_results
        
        # Apply filters
        filtered_df = filter_projects(
            df,
            key_prefix="company_secondary_",
            config={
                'value_column': 'sum_price_agree',
                'value_unit': 1e6,
                'value_label': 'Million Baht',
                'expander_default': True,
                'show_company_filter': False
            }
        )
        st.session_state.filtered_results = filtered_df
        
        # Use filtered results if available
        display_df = filtered_df if filtered_df is not None else df
        
        # Display metrics
        MetricsSummary(display_df)
        
        # Quick Statistics
        st.markdown("### 📊 Quick Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Company Overview**")
            company_stats = display_df.groupby('winner').agg({
                'sum_price_agree': ['sum', 'mean'],
                'project_name': 'count'
            })
            company_stats.columns = ['total_value', 'avg_value', 'projects']
            
            for company in selected_companies:
                if company in company_stats.index:
                    stats = company_stats.loc[company]
                    st.markdown(f"**{company}**  \n"
                              f"Projects: {stats['projects']:,}  \n"
                              f"Total Value: ฿{stats['total_value']/1e6:.1f}M  \n"
                              f"Avg Value: ฿{stats['avg_value']/1e6:.1f}M")
        
        with col2:
            st.markdown("**Top Departments**")
            dept_stats = display_df.groupby('dept_name')['project_name'].count()
            dept_stats = dept_stats.nlargest(5)
            
            total_projects = len(display_df)
            for dept, count in dept_stats.items():
                percentage = (count / total_projects) * 100
                st.markdown(f"**{dept}**  \n"
                          f"{count:,} projects ({percentage:.1f}%)")
        
        with col3:
            st.markdown("**Procurement Methods**")
            method_stats = display_df.groupby('purchase_method_name')['project_name'].count()
            method_stats = method_stats.nlargest(5)
            
            for method, count in method_stats.items():
                if pd.notna(method):
                    percentage = (count / total_projects) * 100
                    st.markdown(f"**{method}**  \n"
                              f"{count:,} projects ({percentage:.1f}%)")
        
        st.markdown("---")
        
        # Display projects table
        st.markdown(f"### Company Projects ({len(display_df):,} projects)")
        ProjectsTable(
            df=display_df,
            show_search=True,
            key_prefix="company_results_"
        )
        
        # Export functionality
        if st.button("📥 Export to CSV", key="export_company_results"):
            export_df = display_df.copy()
            export_df['transaction_date'] = export_df['transaction_date'].dt.strftime('%Y-%m-%d')
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"company_projects_{timestamp}.csv"
            
            csv = export_df.to_csv(index=False)
            
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=filename,
                mime="text/csv",
                key="download_company_results"
            )
    else:
        st.info("Select one or more companies above and click Search to find projects.")

if __name__ == "__main__":
    CompanySearch()