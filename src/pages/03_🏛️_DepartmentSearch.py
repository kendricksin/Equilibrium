# src/pages/DepartmentSearch.py

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import time

# Import components
from components.layout.MetricsDashboard import MetricsDashboard, display_metrics
from components.filters.AdvancedFilters import filter_projects
from components.tables.ProjectsTable import ProjectsTable
from components.charts.StackedBarChart import generate_subdept_charts
from components.charts.PriceCutScatterPlot import plot_price_cut_scatter
from components.tables.PriceCutTable import add_combined_price_analysis
from components.common.LoadingState import LoadingState
from components.common.MetricCard import MetricCard
from components.charts.TreemapChart import TreemapChart
from components.layout.SaveCollection import SaveCollection

# Import services
from services.database.mongodb import MongoDBService
from services.cache.department_cache import (
    get_departments,
    get_department_stats,
    get_subdepartment_stats
)
from state.session import SessionState

# Set page configuration
st.set_page_config(layout="wide")

logger = logging.getLogger(__name__)

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
        key_prefix="dept_search"
    )

def DepartmentSearch():
    """Department search page with department/sub-department selection and filtering"""
    # Initialize session state
    if "initialize_state" in dir(SessionState):
        SessionState.initialize_state()
    
    # Initialize services
    mongo = MongoDBService()
    
    st.title("🏛️ Department Analysis")
    
    # Department and Sub-department selection section
    st.markdown("### Department Selection")
    
    # Get department data with metrics using the cached service
    with LoadingState("Loading departments..."):
        # Get departments with stats from cache 
        departments = get_departments()
        
        # Create options for the dropdown with metrics included
        department_options = []
        dept_mapping = {}
        
        for dept_name in departments:
            # Get department stats from cache
            stats = get_department_stats(dept_name)
            if stats:
                # Create display option with metrics
                total_value = stats.get('total_value_millions', 0)
                project_count = stats.get('count', 0)
                display_option = f"{dept_name} ({project_count:,} projects, ฿{total_value:.1f}M)"
                department_options.append((display_option, total_value))  # Store with value for sorting
                
                # Map display option back to department name
                dept_mapping[display_option] = dept_name
        
        # Sort department options by total value (descending)
        department_options.sort(key=lambda x: x[1], reverse=True)
        
        # Extract just the display options after sorting
        department_options = [option[0] for option in department_options]
    
    # Department selection
    selected_department_options = st.multiselect(
        "Select Departments",
        options=department_options,
        default=st.session_state.get('selected_department_options', []),
        help="Select one or more departments to analyze",
        key="dept_select_departments"
    )
    
    # Convert selected options back to actual department names
    selected_departments = [dept_mapping[option] for option in selected_department_options]
    
    # Store selected department options in session state
    st.session_state.selected_department_options = selected_department_options
    st.session_state.selected_departments = selected_departments
    
    # Subdepartment selection - only show if departments are selected
    selected_subdepartments = []
    if selected_departments:
        # Get sub-departments for selected departments using cache
        with LoadingState("Loading sub-departments..."):
            # Get subdepartment options with metrics
            subdept_options = []
            subdept_mapping = {}
            
            # Get all subdepartments for all selected departments
            for dept in selected_departments:
                subdept_stats = get_subdepartment_stats(dept)
                
                for subdept_name, stats in subdept_stats.items():
                    if pd.notna(subdept_name):  # Skip if not a valid name
                        # Get metrics
                        total_value = stats.get('total_value_millions', 0)
                        project_count = stats.get('count', 0)
                        
                        # Create shortened parent department
                        short_dept = dept[:15] + '...' if len(dept) > 15 else dept
                        
                        # Create display option
                        display_option = f"{subdept_name} [{short_dept}] ({project_count:,} projects, ฿{total_value:.1f}M)"
                        subdept_options.append((display_option, total_value))  # Store with value for sorting
                        
                        # Map display option back to subdepartment name
                        subdept_mapping[display_option] = subdept_name
            
            # Sort subdepartment options by total value (descending)
            subdept_options.sort(key=lambda x: x[1], reverse=True)
            
            # Extract just the display options after sorting
            subdept_options = [option[0] for option in subdept_options]
            
            # Select subdepartments with the new display format
            selected_subdept_options = st.multiselect(
                "Select Sub-Departments",
                options=subdept_options,
                default=st.session_state.get('selected_subdept_options', []),
                help="Select one or more sub-departments to analyze (optional)",
                key="dept_select_subdepartments"
            )
            
            # Convert selected options back to actual subdepartment names
            selected_subdepartments = [subdept_mapping[option] for option in selected_subdept_options]
            
            # Store selected subdepartment options in session state
            st.session_state.selected_subdept_options = selected_subdept_options
            st.session_state.selected_subdepartments = selected_subdepartments
    else:
        selected_subdepartments = []
        st.session_state.selected_subdept_options = []
        st.session_state.selected_subdepartments = []
    
    # Search button
    col1, col2 = st.columns([1, 5])
    with col1:
        search_clicked = st.button(
            "🔎 Search", 
            type="primary", 
            use_container_width=True,
            disabled=not selected_departments
        )
    
    # Clear button
    with col2:
        if st.button("❌ Clear Selection", use_container_width=True):
            # Reset all session state values related to selection
            st.session_state.selected_department_options = []
            st.session_state.selected_departments = []
            st.session_state.selected_subdept_options = []
            st.session_state.selected_subdepartments = []
            st.session_state.dept_search_results = None
            st.session_state.dept_filtered_results = None
            st.rerun()
    
    # Process search
    if search_clicked and selected_departments:
        with st.spinner("Searching projects..."):
            try:
                # Build query for projects collection
                projects_query = {"dept_name": {"$in": selected_departments}}
                if selected_subdepartments:
                    projects_query["dept_sub_name"] = {"$in": selected_subdepartments}
                
                # Fetch detailed project data with a reasonable limit
                df = mongo.get_projects(
                    query=projects_query,
                    max_documents=10000
                )
                
                if df is not None and not df.empty:
                    # Store results in session state
                    st.session_state.dept_search_results = df
                    st.session_state.dept_filtered_results = None  # Reset filtered results
                    
                    # Add quick metrics from the search
                    st.success(f"Found {len(df):,} projects across {len(selected_departments):,} departments" + 
                              (f" and {len(selected_subdepartments):,} sub-departments" if selected_subdepartments else ""))
                    
                    # Show a loading message and delay slightly to ensure the rerun works
                    with st.spinner("Loading results..."):
                        time.sleep(0.3)
                    st.rerun()
                else:
                    st.warning("No projects found for the selected departments.")
                    
            except Exception as e:
                st.error(f"Error performing search: {str(e)}")
                logger.error(f"Error in department search: {e}", exc_info=True)
    
    # Display and filter results
    if 'dept_search_results' in st.session_state and st.session_state.dept_search_results is not None:
        df = st.session_state.dept_search_results
        
        # Show search summary
        search_params = []
        if selected_departments:
            if len(selected_departments) <= 3:
                search_params.append(f"Departments: {', '.join(selected_departments)}")
            else:
                search_params.append(f"Departments: {len(selected_departments)} selected")
        
        if selected_subdepartments:
            if len(selected_subdepartments) <= 3:
                search_params.append(f"Sub-departments: {', '.join(selected_subdepartments)}")
            else:
                search_params.append(f"Sub-departments: {len(selected_subdepartments)} selected")
        
        st.markdown(f"### Search Results: {len(df):,} projects")
        st.markdown(f"**Search criteria:** {' | '.join(search_params)}")
        
        # Apply in-memory secondary filters
        st.markdown("### 🎯 Refine Results")
        filtered_df, filter_summary = filter_projects(
            df,
            key_prefix="dept_secondary_",
            config={
                'value_column': 'sum_price_agree',
                'value_unit': 1e6,
                'value_label': 'Million Baht',
                'show_department_filter': False  # Hide department filter since we're already filtering by department
            }
        )
        
        # Store filtered results in session state
        st.session_state.dept_filtered_results = filtered_df

        # Create metrics for the MetricsDashboard component
        metrics = {
            'total_projects': len(filtered_df),
            'total_value': filtered_df['sum_price_agree'].sum() if 'sum_price_agree' in filtered_df.columns else 0,
            'average_value': filtered_df['sum_price_agree'].mean() if 'sum_price_agree' in filtered_df.columns else 0,
            'unique_companies': filtered_df['winner'].nunique() if 'winner' in filtered_df.columns else 0,
            'price_cut': 0  # Will calculate below if we have the data
        }

        # Calculate price cut if we have the required columns
        if 'sum_price_agree' in filtered_df.columns and 'price_build' in filtered_df.columns:
            # Calculate average price cut percentage
            price_cut_df = filtered_df.dropna(subset=['sum_price_agree', 'price_build'])
            if not price_cut_df.empty:
                total_budget = price_cut_df['price_build'].sum()
                total_agreed = price_cut_df['sum_price_agree'].sum()
                if total_budget > 0:
                    metrics['price_cut'] = ((total_budget - total_agreed) / total_budget) * 100

        # Calculate purchase method distribution
        if 'purchase_method_name' in filtered_df.columns:
            purchase_methods = filtered_df['purchase_method_name'].value_counts()
            metrics['purchase_methods'] = {
                'distribution': purchase_methods.to_dict(),
                'percentages': (purchase_methods / len(filtered_df) * 100).to_dict(),
                'top_method': purchase_methods.index[0] if not purchase_methods.empty else None,
                'top_method_percentage': (purchase_methods.iloc[0] / len(filtered_df) * 100) if not purchase_methods.empty else 0
            }
        else:
            metrics['purchase_methods'] = {
                'distribution': {},
                'percentages': {},
                'top_method': None,
                'top_method_percentage': 0
            }

        # Calculate project type distribution
        if 'project_type_name' in filtered_df.columns:
            project_types = filtered_df['project_type_name'].value_counts()
            metrics['project_types'] = {
                'distribution': project_types.to_dict(),
                'percentages': (project_types / len(filtered_df) * 100).to_dict(),
                'top_type': project_types.index[0] if not project_types.empty else None,
                'top_type_percentage': (project_types.iloc[0] / len(filtered_df) * 100) if not project_types.empty else 0
            }
        else:
            metrics['project_types'] = {
                'distribution': {},
                'percentages': {},
                'top_type': None, 
                'top_type_percentage': 0
            }

        # Top companies
        if 'winner' in filtered_df.columns and 'project_name' in filtered_df.columns:
            company_stats = filtered_df.groupby('winner').agg({
                'project_name': 'count',
                'sum_price_agree': 'sum'
            }).reset_index()
            company_stats = company_stats.sort_values('sum_price_agree', ascending=False)
            company_stats.columns = ['company', 'projects', 'value']
            metrics['top_companies'] = company_stats.head().to_dict('records')
        else:
            metrics['top_companies'] = []

        # Department stats
        if 'dept_name' in filtered_df.columns and 'project_name' in filtered_df.columns:
            dept_stats = filtered_df.groupby('dept_name').agg({
                'project_name': 'count',
                'sum_price_agree': 'sum',
                'winner': 'nunique'
            }).reset_index()
            dept_stats.columns = ['dept_name', 'projects', 'value', 'companies']
            metrics['department_stats'] = dept_stats.to_dict('records')
        else:
            metrics['department_stats'] = []

        # Display metrics summary with calculated data
        display_metrics(metrics)
        
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
            st.markdown("**Top Sub-departments by Projects**")
            if 'dept_sub_name' in filtered_df.columns:
                top_subdepts = filtered_df.groupby('dept_sub_name')['project_name'].count()
                top_subdepts = top_subdepts.nlargest(5)
                for idx, (subdept, count) in enumerate(top_subdepts.items()):
                    st.markdown(f"{idx+1}. **{subdept}**  \n"
                            f"{count} projects")
            else:
                st.markdown("Sub-department data not available")
        
        st.markdown("---")
        
        # Display results table with built-in search and sorting
        st.markdown(f"### Detailed Results ({len(filtered_df):,} projects)")
        ProjectsTable(
            df=filtered_df,
            filters=None,
            show_search=True,
            key_prefix="dept_search_results_"
        )

        # Display the save collection component
        SaveCollection(
            df=filtered_df,
            source="department_search",  # Source identifier
            key_prefix="dept_search_"   # Unique prefix for component keys
        )
        
        # Add export functionality
        if st.button("📥 Export to CSV", key="dept_export_results"):
            # Prepare export data
            export_df = filtered_df.copy()
            export_df['transaction_date'] = export_df['transaction_date'].dt.strftime('%Y-%m-%d')
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"department_search_results_{timestamp}.csv"
            
            # Convert to CSV
            csv = export_df.to_csv(index=False)
            
            # Create download button
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=filename,
                mime="text/csv",
                key="dept_download_results"
            )

if __name__ == "__main__":
    DepartmentSearch()