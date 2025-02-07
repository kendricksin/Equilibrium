# src/pages/DepartmentSearch.py

import streamlit as st
import pandas as pd
from datetime import datetime
from components.layout.MetricsSummary import MetricsSummary
from components.filters.TableFilter import filter_projects
from components.tables.ProjectsTable import ProjectsTable
from state.session import SessionState
from services.database.mongodb import MongoDBService
from services.analytics.period_analysis import PeriodAnalysisService
from services.cache.department_cache import (
    get_departments,
    get_department_stats,
    get_subdepartment_stats
)

st.set_page_config(layout="wide")

def DepartmentSearch():
    """Department search page with multi-department selection and secondary filtering"""
    # Initialize session state
    SessionState.initialize_state()
    
    # Initialize MongoDB service
    mongo_service = MongoDBService()
    
    # Get current filters from session state
    filters = SessionState.get_filters()
    
    # Department selection section
    st.markdown("### 🏢 Department Selection")
    
    # Get departments with cached statistics
    dept_options = get_departments()
    
    # Format department options to show stats
    dept_display_options = []
    dept_mapping = {}  # To map display strings back to department names
    
    for dept in dept_options:
        stats = get_department_stats(dept)
        if stats:
            display_text = f"{dept} ({stats['count']:,} projects, ฿{stats['total_value_millions']:.1f}M)"
            dept_display_options.append(display_text)
            dept_mapping[display_text] = dept
    
    # Multi-select for departments with statistics
    selected_display_depts = st.multiselect(
        "Select Departments",
        options=dept_display_options,
        key="department_select",
        help="Select one or more departments to analyze"
    )
    
    # Convert display selections back to department names
    selected_departments = [dept_mapping[display] for display in selected_display_depts]
    
    # Sub-department selection (only show if departments are selected)
    selected_subdepartments = []
    if selected_departments:
        # Get sub-department stats for all selected departments
        all_subdept_stats = {}
        for dept in selected_departments:
            subdept_stats = get_subdepartment_stats(dept)
            all_subdept_stats.update(subdept_stats)
        
        # Create formatted sub-department options
        subdept_display_options = []
        subdept_mapping = {}
        
        for subdept, stats in all_subdept_stats.items():
            if pd.notna(subdept):  # Filter out NaN/None values
                display_text = f"{subdept} ({stats['count']:,} projects, ฿{stats['total_value_millions']:.1f}M)"
                subdept_display_options.append(display_text)
                subdept_mapping[display_text] = subdept
        
        # Multi-select for sub-departments
        selected_display_subdepts = st.multiselect(
            "Select Sub-departments (Optional)",
            options=sorted(subdept_display_options),
            key="subdepartment_select",
            help="Optionally select specific sub-departments to narrow your search"
        )
        
        # Convert display selections back to sub-department names
        selected_subdepartments = [subdept_mapping[display] for display in selected_display_subdepts]
    
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
            # Clear selections from session state
            if "department_select" in st.session_state:
                del st.session_state.department_select
            if "subdepartment_select" in st.session_state:
                del st.session_state.subdepartment_select
            st.session_state.department_results = None
            st.session_state.filtered_results = None
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

        # Period Analysis Section
        st.markdown("### 📈 Period Analysis")

        metric = st.selectbox(
            "Select Metric",
            options=['project_value', 'project_count'],
            format_func=lambda x: "Project Value" if x == "project_value" else "Project Count",
            key="metric"
        )

        try:
            # Calculate period analysis for all periods
            results = PeriodAnalysisService.analyze_all_periods(
                display_df,
                metric=metric
            )
            
            # Create visualization
            fig = PeriodAnalysisService.create_combined_chart(results, metric)
            st.plotly_chart(fig, use_container_width=True)
            
            # Display summary in columns
            st.markdown("#### Summary")
            cols = st.columns(4)
            for idx, (period_name, (_, summary)) in enumerate(results.items()):
                with cols[idx]:
                    formatter = summary['formatter']
                    st.markdown(f"""
                    **{period_name}**  
                    Current: {formatter(summary['current_value'])}  
                    Change: {summary['change_percentage']:.1f}%  
                    ({summary['trend']})
                    """)

        except Exception as e:
            st.error(f"Error performing period analysis: {str(e)}")

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

if __name__ == "__main__":
    DepartmentSearch()