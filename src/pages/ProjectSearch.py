# src/pages/ProjectSearch.py

import streamlit as st
import pandas as pd
from datetime import datetime
from components.layout.Header import Header
from components.layout.Sidebar import Sidebar
from components.layout.MetricsSummary import MetricsSummary
from components.filters.KeywordFilter import KeywordFilter, build_keyword_query
from components.tables.ProjectsTable import ProjectsTable
from state.session import SessionState
from services.database.mongodb import MongoDBService

st.set_page_config(layout="wide")

def ProjectSearch():
    """Project search page with keyword filtering"""
    # Initialize session state
    SessionState.initialize_state()
    
    # Initialize MongoDB service
    mongo_service = MongoDBService()
    
    # Header
    Header(current_page="Project Search")
    
    # Get current filters from session state
    filters = SessionState.get_filters()
    
    # Keyword search section
    include_keywords, exclude_keywords = KeywordFilter(
        current_include=st.session_state.get('include_keywords', []),
        current_exclude=st.session_state.get('exclude_keywords', []),
        key_prefix="search_"
    )
    
    # Store keywords in session state
    st.session_state.include_keywords = include_keywords
    st.session_state.exclude_keywords = exclude_keywords
    
    # Search button
    col1, col2 = st.columns([1, 5])
    with col1:
        search_clicked = st.button("🔎 Search", type="primary", use_container_width=True)
    
    # Clear button
    with col2:
        if st.button("❌ Clear Search", use_container_width=True):
            st.session_state.include_keywords = []
            st.session_state.exclude_keywords = []
            st.session_state.search_results = None
            st.rerun()
    
    # Process search
    if search_clicked and (include_keywords or exclude_keywords):
        with st.spinner("Searching projects..."):
            try:
                # Build keyword query
                keyword_query = build_keyword_query(include_keywords, exclude_keywords)
                
                # Combine with existing filters if any
                if filters and st.session_state.filters_applied:
                    from state.filters import FilterManager
                    filter_query = FilterManager.build_mongo_query(filters)
                    if filter_query:
                        if "$and" in keyword_query:
                            keyword_query["$and"].extend(
                                filter_query.get("$and", [])
                            )
                        else:
                            keyword_query["$and"] = filter_query.get("$and", [])
                
                # Fetch results with limit
                df = mongo_service.get_projects(
                    query=keyword_query,
                    max_documents=20000
                )
                
                if df is not None and not df.empty:
                    st.session_state.search_results = df
                    
                    # Display summary metrics
                    MetricsSummary(df)
                    
                    # Display quick stats
                    st.markdown("### 📊 Quick Statistics")
                    
                    # Calculate company statistics
                    company_stats = df.groupby('winner').agg({
                        'sum_price_agree': ['sum', 'mean'],
                        'project_name': 'count'
                    }).reset_index()
                    
                    # Flatten column names and rename
                    company_stats.columns = ['winner', 'total_value', 'avg_value', 'project_count']
                    
                    # Top companies by value
                    top_by_value = company_stats.sort_values('total_value', ascending=False).head(5)
                    
                    # Top companies by project count
                    top_by_count = company_stats.sort_values('project_count', ascending=False).head(5)
                    
                    # Top departments by project count
                    top_departments = df.groupby('dept_name')['project_name'].count().sort_values(ascending=False).head(5)
                    
                    # Display stats in columns
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("**Top Companies by Value**")
                        for idx, (company, row) in enumerate(top_by_value.iterrows(), 1):
                            st.markdown(f"{idx}. **{row['winner']}**  \n"
                                      f"฿{row['total_value']/1e6:.1f}M ({row['project_count']} projects)")
                    
                    with col2:
                        st.markdown("**Top Companies by Projects**")
                        for idx, (company, row) in enumerate(top_by_count.iterrows(), 1):
                            st.markdown(f"{idx}. **{row['winner']}**  \n"
                                      f"{row['project_count']} projects (avg ฿{row['avg_value']/1e6:.1f}M)")
                    
                    with col3:
                        st.markdown("**Top Departments by Projects**")
                        for idx, (dept, count) in enumerate(top_departments.items(), 1):
                            st.markdown(f"{idx}. **{dept}**  \n"
                                      f"{count} projects")
                    
                    st.markdown("---")
                    
                    # Display results table with built-in search and sorting
                    st.markdown(f"### Search Results ({len(df):,} projects found)")
                    ProjectsTable(
                        df=df,
                        filters=filters,
                        show_search=True,
                        key_prefix="search_results_"
                    )
                    
                    # Add export functionality
                    if st.button("📥 Export to CSV", key="export_results"):
                        # Prepare export data
                        export_df = df.copy()
                        export_df['transaction_date'] = pd.to_datetime(
                            export_df['transaction_date']
                        ).dt.strftime('%Y-%m-%d')
                        
                        # Generate filename
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"project_search_results_{timestamp}.csv"
                        
                        # Convert to CSV
                        csv = export_df.to_csv(index=False)
                        
                        # Create download button
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv,
                            file_name=filename,
                            mime="text/csv",
                            key="download_results"
                        )
                    
                else:
                    st.warning("No projects found matching your search criteria.")
                    
            except Exception as e:
                st.error(f"Error performing search: {str(e)}")
                
    elif st.session_state.get('search_results') is not None:
        # Display previous results
        MetricsSummary(st.session_state.search_results)
        st.markdown(f"### Previous Search Results ({len(st.session_state.search_results):,} projects)")
        ProjectsTable(
            df=st.session_state.search_results,
            filters=filters,
            show_search=True,
            key_prefix="search_results_"
        )
    else:
        st.info("Enter keywords above and click Search to find projects.")

if __name__ == "__main__":
    ProjectSearch()