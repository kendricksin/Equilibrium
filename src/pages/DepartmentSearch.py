# src/pages/DepartmentSearch.py

import streamlit as st
import pandas as pd
from datetime import datetime
from components.layout.MetricsSummary import MetricsSummary
from components.filters.TableFilter import filter_projects
from components.tables.ProjectsTable import ProjectsTable
from state.session import SessionState
from services.database.mongodb import MongoDBService
from services.cache.department_cache import (
    get_departments,
    get_department_stats,
    get_subdepartment_stats
)
from components.layout.PageLayout import PageLayout
from special_functions.url_params import URLParamsHandler

def DepartmentSearch():
    """Department search page with URL parameter support"""
    # Initialize session state
    SessionState.initialize_state()
    
    # Initialize MongoDB service and URL parameters handler
    mongo_service = MongoDBService()
    url_params = URLParamsHandler.get_query_params()
    
    # Get current filters from session state or URL parameters
    filters = SessionState.get_filters()
    
    # Department selection section
    st.markdown("### 🏢 Department Selection")
    
    # Get departments with cached statistics
    dept_options = get_departments()
    
    # Format department options and create mapping
    dept_display_options = []
    dept_mapping = {}
    reverse_dept_mapping = {}
    
    for dept in dept_options:
        stats = get_department_stats(dept)
        if stats:
            display_text = f"{dept} ({stats['count']:,} projects, ฿{stats['total_value_millions']:.1f}M)"
            dept_display_options.append(display_text)
            dept_mapping[display_text] = dept
            reverse_dept_mapping[dept] = display_text
    
    # Pre-select departments from URL parameters
    default_depts = []
    if 'departments' in url_params:
        default_depts = [
            reverse_dept_mapping[dept]
            for dept in url_params['departments']
            if dept in reverse_dept_mapping
        ]
    
    # Multi-select for departments with statistics
    selected_display_depts = st.multiselect(
        "Select Departments",
        options=dept_display_options,
        default=default_depts,
        key="department_select",
        help="Select one or more departments to analyze"
    )
    
    # Convert display selections back to department names
    selected_departments = [dept_mapping[display] for display in selected_display_depts]
    
    # Sub-department selection
    selected_subdepartments = []
    if selected_departments:
        # Get sub-department stats and create mapping
        all_subdept_stats = {}
        subdept_display_options = []
        subdept_mapping = {}
        reverse_subdept_mapping = {}
        
        for dept in selected_departments:
            subdept_stats = get_subdepartment_stats(dept)
            all_subdept_stats.update(subdept_stats)
        
        for subdept, stats in all_subdept_stats.items():
            if pd.notna(subdept):
                display_text = f"{subdept} ({stats['count']:,} projects, ฿{stats['total_value_millions']:.1f}M)"
                subdept_display_options.append(display_text)
                subdept_mapping[display_text] = subdept
                reverse_subdept_mapping[subdept] = display_text
        
        # Pre-select subdepartments from URL parameters
        default_subdepts = []
        if 'subdepartments' in url_params:
            default_subdepts = [
                reverse_subdept_mapping[subdept]
                for subdept in url_params['subdepartments']
                if subdept in reverse_subdept_mapping
            ]
        
        # Multi-select for sub-departments
        selected_display_subdepts = st.multiselect(
            "Select Sub-departments (Optional)",
            options=sorted(subdept_display_options),
            default=default_subdepts,
            key="subdepartment_select",
            help="Optionally select specific sub-departments to narrow your search"
        )
        
        selected_subdepartments = [subdept_mapping[display] for display in selected_display_subdepts]
    
    # Update URL parameters based on selections
    url_params = {
        'departments': selected_departments,
        'subdepartments': selected_subdepartments
    }
    URLParamsHandler.update_query_params(url_params)
    
    # Search and Clear buttons
    col1, col2 = st.columns([1, 5])
    with col1:
        search_clicked = st.button(
            "🔎 Search",
            type="primary",
            use_container_width=True,
            disabled=not selected_departments
        )
    
    with col2:
        if st.button("❌ Clear Selection", use_container_width=True):
            # Clear selections and URL parameters
            if "department_select" in st.session_state:
                del st.session_state.department_select
            if "subdepartment_select" in st.session_state:
                del st.session_state.subdepartment_select
            st.session_state.department_results = None
            st.session_state.filtered_results = None
            URLParamsHandler.update_query_params({})
            st.rerun()
    
    # Process search
    if search_clicked and selected_departments:
        with st.spinner("Searching departments..."):
            try:
                # Build department query
                query = {"dept_name": {"$in": selected_departments}}
                
                # Add sub-department filter if selected
                if selected_subdepartments:
                    query["dept_sub_name"] = {"$in": selected_subdepartments}
                
                # Fetch results with limit
                df = mongo_service.get_projects(
                    query=query,
                    max_documents=20000
                )
                
                if df is not None and not df.empty:
                    st.session_state.department_results = df
                    st.session_state.filtered_results = None  # Reset filtered results
                    st.rerun()
                else:
                    st.warning("No projects found for the selected departments.")
                    
            except Exception as e:
                st.error(f"Error performing search: {str(e)}")
    
    # Display and filter results
    if st.session_state.get('department_results') is not None:
        df = st.session_state.department_results
        
        # Apply secondary filters if results exist
        filtered_df = filter_projects(
            df,
            key_prefix="dept_secondary_",
            config={
                'value_column': 'sum_price_agree',
                'value_unit': 1e6,
                'value_label': 'Million Baht',
                'expander_default': True,
                'show_department_filter': False  # Hide department filter since we're already filtering by department
            }
        )
        st.session_state.filtered_results = filtered_df
        
        # Use filtered results if available, otherwise use original results
        display_df = filtered_df if filtered_df is not None else df
        
        # Display metrics for current view
        MetricsSummary(display_df)
        
        # Display quick stats using pre-aggregated data where possible
        st.markdown("### 📊 Quick Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Department Overview**")
            for dept in selected_departments:
                stats = get_department_stats(dept)
                if stats:
                    st.markdown(f"**{dept}**  \n"
                              f"Projects: {stats['count']:,}  \n"
                              f"Value: ฿{stats['total_value_millions']:.1f}M  \n"
                              f"Companies: {stats['unique_companies']:,}")
        
        with col2:
            st.markdown("**Top Companies**")
            company_stats = display_df.groupby('winner').agg({
                'sum_price_agree': 'sum',
                'project_name': 'count'
            }).reset_index()
            
            top_companies = company_stats.nlargest(5, 'sum_price_agree')
            for idx, row in top_companies.iterrows():
                st.markdown(f"{idx+1}. **{row['winner']}**  \n"
                          f"฿{row['sum_price_agree']/1e6:.1f}M ({row['project_name']} projects)")
        
        with col3:
            st.markdown("**Procurement Methods**")
            method_stats = display_df.groupby('purchase_method_name')['project_name'].count()
            method_stats = method_stats.nlargest(5)
            
            total_projects = len(display_df)
            for method, count in method_stats.items():
                if pd.notna(method):
                    percentage = (count / total_projects) * 100
                    st.markdown(f"**{method}**  \n"
                              f"{count:,} projects ({percentage:.1f}%)")
        
        st.markdown("---")
        
        # Display results table with built-in search and sorting
        st.markdown(f"### Department Projects ({len(display_df):,} projects)")
        ProjectsTable(
            df=display_df,
            filters=filters,
            show_search=True,
            key_prefix="dept_results_"
        )
        
        # Add export functionality
        if st.button("📥 Export to CSV", key="export_dept_results"):
            # Prepare export data
            export_df = display_df.copy()
            export_df['transaction_date'] = export_df['transaction_date'].dt.strftime('%Y-%m-%d')
            
            # Generate filename with department names
            dept_names = "_".join(selected_departments)[:50]  # Limit length
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dept_{dept_names}_{timestamp}.csv"
            
            # Convert to CSV
            csv = export_df.to_csv(index=False)
            
            # Create download button
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=filename,
                mime="text/csv",
                key="download_dept_results"
            )
    else:
        st.info("Select one or more departments above and click Search to find projects.")

    # Add share button
    if selected_departments:
        shareable_url = URLParamsHandler.get_shareable_link()
        st.markdown("#### 🔗 Share this view")
        st.code(shareable_url)
        
        # Copy button
        if st.button("📋 Copy URL"):
            st.write("URL copied to clipboard!")
            st.experimental_set_clipboard(shareable_url)

if __name__ == "__main__":
    PageLayout(DepartmentSearch)