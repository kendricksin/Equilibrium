# src/pages/DepartmentSearch.py

import streamlit as st
import pandas as pd
from datetime import datetime
from components.layout.MetricsSummary import MetricsSummary
from components.filters.TableFilter import filter_projects
from components.tables.ProjectsTable import ProjectsTable
from components.layout.ContextSelector import ContextSelector
from components.layout.SaveCollection import SaveCollection
from services.analytics.department_analysis import DepartmentAnalysisService
from services.analytics.visualization import VisualizationService
from services.analytics.price_analysis import PriceAnalysisService

def DepartmentSearch():
    """Enhanced department search and analysis page"""
    st.set_page_config(layout="wide")
    
    # Initialize ContextSelector
    ContextSelector()
    
    # Initialize services
    dept_service = DepartmentAnalysisService()
    viz_service = VisualizationService()
    price_service = PriceAnalysisService()
    
    st.title("🏛️ Department Analysis")
    
    # Department Selection Section
    st.markdown("### Department Selection")
    
    # Get department data and metadata
    dept_data, metadata = dept_service.get_department_overview()
    
    if not dept_data:
        st.warning("No department data available for analysis")
        return
    
    # Show overall metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Projects", f"{metadata['total_projects']:,}")
    with col2:
        st.metric("Total Value", f"฿{metadata['total_value']/1e9:.1f}B")
    with col3:
        st.metric("Departments", f"{metadata['unique_departments']:,}")
    with col4:
        st.metric("Companies", f"{metadata['unique_companies']:,}")
    
    # Create formatted options for department selection
    dept_options = {
        f"{dept['department']} ({dept['count']:,} projects, ฿{dept['total_value_millions']:.1f}M)": dept['department']
        for dept in dept_data
    }
    
    # Department multi-select
    selected_display_depts = st.multiselect(
        "Select Departments",
        options=sorted(dept_options.keys()),
        help="Select one or more departments to analyze"
    )
    
    selected_departments = [dept_options[display] for display in selected_display_depts]
    
    # Sub-department selection
    selected_subdepartments = []
    if selected_departments:
        subdept_data = []
        for dept in selected_departments:
            subdepts = dept_service.get_subdepartment_analysis(dept)
            if isinstance(subdepts, list):
                subdept_data.extend(subdepts)
        
        if subdept_data:
            subdept_options = {
                f"{sub.get('subdepartment', 'Unknown')} ({sub.get('projects', 0):,} projects, ฿{sub.get('total_value_millions', 0):.1f}M)": sub.get('subdepartment')
                for sub in subdept_data
                if sub and sub.get('subdepartment') is not None
            }
            
            selected_display_subdepts = st.multiselect(
                "Select Sub-departments (Optional)",
                options=sorted(subdept_options.keys()),
                help="Optionally select specific sub-departments"
            )
            
            selected_subdepartments = [subdept_options[display] for display in selected_display_subdepts]
    
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
            st.session_state.department_results = None
            st.session_state.filtered_results = None
            st.rerun()
    
    # Process search
    if search_clicked and selected_departments:
        with st.spinner("Analyzing departments..."):
            # Get projects by filtering in PostgreSQL
            df = dept_service.get_department_projects(
                departments=selected_departments,
                subdepartments=selected_subdepartments
            )
            
            if df is not None and not df.empty:
                st.session_state.department_results = df
                st.session_state.filtered_results = None
                st.rerun()
            else:
                st.warning("No projects found for the selected departments.")
    
    # Display and filter results
    if hasattr(st.session_state, 'department_results') and st.session_state.department_results is not None:
        df = st.session_state.department_results
        
        # Apply secondary filters
        filtered_df = filter_projects(
            df,
            key_prefix="dept_secondary_",
            config={
                'value_column': 'sum_price_agree',
                'value_unit': 1e6,
                'value_label': 'Million Baht',
                'expander_default': True,
                'show_department_filter': False
            }
        )
        st.session_state.filtered_results = filtered_df
        
        # Use filtered results if available
        display_df = filtered_df if filtered_df is not None else df
        
        # Display metrics summary
        MetricsSummary(display_df)
        
        # Quick Statistics
        st.markdown("### 📊 Quick Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Department Overview**")
            for dept in selected_departments:
                dept_stats = next((d for d in dept_data if d['department'] == dept), None)
                if dept_stats:
                    st.markdown(f"""
                    **{dept}**  
                    Projects: {dept_stats['count']:,}  
                    Value: ฿{dept_stats['total_value_millions']:.1f}M  
                    Companies: {dept_stats['unique_companies']:,}
                    """)
        
        with col2:
            st.markdown("**Top Companies**")
            company_stats = display_df.groupby('winner').agg({
                'sum_price_agree': 'sum',
                'project_name': 'count'
            }).reset_index()
            
            top_companies = company_stats.nlargest(5, 'sum_price_agree')
            for _, row in top_companies.iterrows():
                st.markdown(f"""
                **{row['winner']}**  
                ฿{row['sum_price_agree']/1e6:.1f}M ({row['project_name']} projects)
                """)
        
        with col3:
            st.markdown("**Procurement Methods**")
            method_stats = display_df.groupby('purchase_method_name')['project_name'].count()
            total_projects = len(display_df)
            
            for method, count in method_stats.nlargest(5).items():
                if pd.notna(method):
                    percentage = (count / total_projects) * 100
                    st.markdown(f"""
                    **{method}**  
                    {count:,} projects ({percentage:.1f}%)
                    """)
        
        st.markdown("---")
        
        # Price Analysis Section
        st.markdown("### 💰 Price Analysis")
        
        price_metrics = price_service.get_price_distribution()
        fig = viz_service.create_dual_axis_chart(
            df=price_metrics,
            x_col='range',
            y1_col='total_value',
            y2_col='avg_cut',
            y1_label='Total Value (M฿)',
            y2_label='Average Price Cut (%)',
            title='Price Distribution and Price Cuts by Value Range'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Project Timeline
        st.markdown("### 📅 Project Timeline")
        
        timeline_data = dept_service.get_project_timeline(display_df)
        fig = viz_service.create_time_series(
            df=timeline_data,
            x_col='period',
            y_cols=['project_count', 'total_value'],
            labels=['Number of Projects', 'Total Value (M฿)'],
            title='Project Timeline'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Results Table
        st.markdown(f"### Department Projects ({len(display_df):,} projects)")
        ProjectsTable(
            df=display_df,
            show_search=True,
            key_prefix="dept_results_"
        )
        
        # Save Collection option
        SaveCollection(
            df=display_df,
            source="department_search",
            key_prefix="dept_"
        )
        
    else:
        st.info("Select one or more departments above and click Search to find projects.")

if __name__ == "__main__":
    DepartmentSearch()