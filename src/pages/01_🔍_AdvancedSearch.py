# src/pages/AdvancedSearch.py

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List

from components.layout.MetricsSummary import MetricsSummary
from components.filters.KeywordFilter import KeywordFilter, build_keyword_query
from components.filters.AdvancedFilters import filter_projects
from components.tables.ProjectsTable import ProjectsTable
from components.charts.StackedBarChart import generate_subdept_charts
from components.charts.PriceCutScatterPlot import plot_price_cut_scatter
from components.tables.PriceCutTable import add_combined_price_analysis
from components.layout.SaveCollection import SaveCollection
from components.charts.TreemapChart import TreemapChart

from state.session import SessionState
from state.filters import FilterManager
from services.database.mongodb import MongoDBService

st.set_page_config(layout="wide")

def generate_price_cut_visualization(df: pd.DataFrame):
    """Generate price cut visualization by company"""
    # Make sure data has the required columns
    if 'sum_price_agree' not in df.columns or 'price_build' not in df.columns:
        st.warning("Cannot create price cut visualization: missing required columns")
        return
    
    st.markdown("## Price Cut Analysis by Company")
    
    # Choose visualization options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        max_companies = st.slider("Max Companies", min_value=5, max_value=30, value=15, step=5)
    
    with col2:
        size_by_value = st.checkbox("Size dots by project value", value=True)
    
    with col3:
        color_options = ["None", "dept_name", "project_type_name", "purchase_method_name", "budget_year"]
        color_option = st.selectbox("Color dots by", options=color_options)
    
    # Process color option
    color_by = None if color_option == "None" else color_option
    
    # Create and display the visualization
    plot_price_cut_scatter(
        df=df,
        title="Project Price Cut Analysis by Company",
        height=600,
        max_companies=max_companies,
        use_size_by_value=size_by_value,
        color_by=color_by,
        key_prefix="adv_search"
    )

def EnhancedKeywordFilter(
    current_include_all: List[str] = None,
    current_include_any: List[str] = None,
    current_exclude: List[str] = None,
    key_prefix: str = ""
):
    """Custom layout for keyword filter with columns"""
    if current_include_all is None:
        current_include_all = []
    if current_include_any is None:
        current_include_any = []
    if current_exclude is None:
        current_exclude = []
        
    st.markdown("### 🔍 Keyword Search")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    # Include ALL keywords - takes up half the width
    with col1:
        include_all_input = st.text_area(
            "Must include ALL these keywords (one per line)",
            value="\n".join(current_include_all),
            height=150,
            help="Enter keywords that MUST ALL be present. Projects must contain ALL these keywords.",
            key=f"{key_prefix}include_all_keywords"
        )
    
    # Include ANY keywords
    with col2:
        include_any_input = st.text_area(
            "Must include ANY of these (one per line)",
            value="\n".join(current_include_any),
            height=150,
            help="Enter keywords where at least ONE must be present. Projects must contain AT LEAST ONE of these keywords.",
            key=f"{key_prefix}include_any_keywords"
        )
    
    # Exclude keywords
    with col3:
        exclude_input = st.text_area(
            "Exclude keywords (one per line)",
            value="\n".join(current_exclude),
            height=150,
            help="Enter keywords to exclude. Projects containing ANY of these keywords will be excluded.",
            key=f"{key_prefix}exclude_keywords"
        )
    
    # Process inputs
    include_all_keywords = [
        keyword.strip() 
        for keyword in include_all_input.split("\n") 
        if keyword.strip()
    ]
    
    include_any_keywords = [
        keyword.strip() 
        for keyword in include_any_input.split("\n") 
        if keyword.strip()
    ]
    
    exclude_keywords = [
        keyword.strip() 
        for keyword in exclude_input.split("\n") 
        if keyword.strip()
    ]
    
    return include_all_keywords, include_any_keywords, exclude_keywords

def AdvancedSearch():
    """Advanced search page with keyword search and in-memory secondary filtering"""
    # Initialize session state
    SessionState.initialize_state()
    
    # Initialize MongoDB service
    mongo_service = MongoDBService()
    
    st.title("🔎 Advanced Project Search")
    
    # Keyword search section with enhanced layout
    include_all_keywords, include_any_keywords, exclude_keywords = EnhancedKeywordFilter(
        current_include_all=st.session_state.get('include_all_keywords', []),
        current_include_any=st.session_state.get('include_any_keywords', []),
        current_exclude=st.session_state.get('exclude_keywords', []),
        key_prefix="adv_search_"
    )
    
    # Store keywords in session state
    st.session_state.include_all_keywords = include_all_keywords
    st.session_state.include_any_keywords = include_any_keywords
    st.session_state.exclude_keywords = exclude_keywords
    
    # Search button
    col1, col2 = st.columns([1, 5])
    with col1:
        search_clicked = st.button("🔎 Search", type="primary", use_container_width=True)
    
    # Clear button
    with col2:
        if st.button("❌ Clear Search", use_container_width=True):
            st.session_state.include_all_keywords = []
            st.session_state.include_any_keywords = []
            st.session_state.exclude_keywords = []
            st.session_state.adv_search_results = None
            st.session_state.adv_filtered_results = None
            st.rerun()
    
    # Process search
    if search_clicked and (include_all_keywords or include_any_keywords or exclude_keywords):
        with st.spinner("Searching projects..."):
            try:
                # Build keyword query
                keyword_query = build_keyword_query(include_all_keywords, include_any_keywords, exclude_keywords)
                
                # Fetch results with limit
                df = mongo_service.get_projects(
                    query=keyword_query,
                    max_documents=20000
                )
                
                if df is not None and not df.empty:
                    st.session_state.adv_search_results = df
                    st.session_state.adv_filtered_results = None  # Reset filtered results
                    st.rerun()
                else:
                    st.warning("No projects found matching your search criteria.")
                    
            except Exception as e:
                st.error(f"Error performing search: {str(e)}")
                
    # Display and filter results
    if 'adv_search_results' in st.session_state and st.session_state.adv_search_results is not None:
        df = st.session_state.adv_search_results
        
        # Show search summary
        search_params = []
        if include_all_keywords:
            search_params.append(f"Must include ALL: {', '.join(include_all_keywords)}")
        if include_any_keywords:
            search_params.append(f"Must include ANY: {', '.join(include_any_keywords)}")
        if exclude_keywords:
            search_params.append(f"Exclude: {', '.join(exclude_keywords)}")
        
        st.markdown(f"### Search Results: {len(df):,} projects")
        st.markdown(f"**Search criteria:** {' | '.join(search_params)}")

        # Apply in-memory secondary filters using the improved AdvancedFilters component
        st.markdown("### 🎯 Refine Results")
        filtered_df, filter_summary = filter_projects(
            df,
            key_prefix="adv_secondary_",
            config={
                'value_column': 'sum_price_agree',
                'value_unit': 1e6,
                'value_label': 'Million Baht'
            }
        )

        # Store filtered results in session state
        st.session_state.adv_filtered_results = filtered_df

        # Display metrics for current view
        MetricsSummary(filtered_df)
        
        # Add the subdepartment charts 
        generate_subdept_charts(filtered_df)

        # Add the price cut visualization
        generate_price_cut_visualization(filtered_df)

        # Add the combined price analysis   
        add_combined_price_analysis(filtered_df)

        # Display quick stats
        st.markdown("### 📊 Quick Statistics")
        
        # Calculate company statistics
        company_stats = filtered_df.groupby('winner').agg({
            'sum_price_agree': ['sum', 'mean'],
            'project_name': 'count'
        }).reset_index()
        
        # Flatten column names and rename
        company_stats.columns = ['winner', 'total_value', 'avg_value', 'project_count']
        
        # Display stats in columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Top Companies by Value**")
            top_by_value = company_stats.nlargest(5, 'total_value')
            for idx, row in top_by_value.iterrows():
                st.markdown(f"{idx+1}. **{row['winner']}**  \n"
                          f"฿{row['total_value']/1e6:.1f}M ({row['project_count']} projects)")
        
        with col2:
            st.markdown("**Top Companies by Projects**")
            top_by_count = company_stats.nlargest(5, 'project_count')
            for idx, row in top_by_count.iterrows():
                st.markdown(f"{idx+1}. **{row['winner']}**  \n"
                          f"{row['project_count']} projects (avg ฿{row['avg_value']/1e6:.1f}M)")
        
        with col3:
            st.markdown("**Top Departments by Projects**")
            top_departments = filtered_df.groupby('dept_name')['project_name'].count()
            top_departments = top_departments.nlargest(5)
            for idx, (dept, count) in enumerate(top_departments.items()):
                st.markdown(f"{idx+1}. **{dept}**  \n"
                          f"{count} projects")
        
        st.markdown("---")
        
        # Display results table with built-in search and sorting
        st.markdown(f"### Detailed Results ({len(filtered_df):,} projects)")
        ProjectsTable(
            df=filtered_df,
            filters=None,
            show_search=True,
            key_prefix="adv_search_results_"
        )
        
        # Display the save collection component
        SaveCollection(
            df=filtered_df,
            source="advanced_search",  # Source identifier
            key_prefix="adv_search_"   # Unique prefix for component keys
        )


        # Add export functionality
        if st.button("📥 Export to CSV", key="adv_export_results"):
            # Prepare export data
            export_df = filtered_df.copy()
            export_df['transaction_date'] = export_df['transaction_date'].dt.strftime('%Y-%m-%d')
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"advanced_search_results_{timestamp}.csv"
            
            # Convert to CSV
            csv = export_df.to_csv(index=False)
            
            # Create download button
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=filename,
                mime="text/csv",
                key="adv_download_results"
            )
    else:
        st.info("Enter keywords above and click Search to find projects.")

if __name__ == "__main__":
    AdvancedSearch()