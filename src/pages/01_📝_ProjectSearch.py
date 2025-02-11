# src/pages/ProjectSearch.py

import streamlit as st
import pandas as pd
from datetime import datetime
import math
from components.layout.MetricsSummary import MetricsSummary
from components.filters.KeywordFilter import KeywordFilter, build_keyword_query
from components.filters.TableFilter import filter_projects
from components.tables.ProjectsTable import ProjectsTable
from state.session import SessionState
from services.database.mongodb import MongoDBService
from services.analytics.period_analysis import PeriodAnalysisService
from services.analytics.company_projects import CompanyProjectsService
from services.analytics.subdept_projects import display_subdepartment_distribution

st.set_page_config(layout="wide")

def ProjectSearch():
    """Project search page with keyword filtering and secondary filtering"""
    # Initialize session state
    SessionState.initialize_state()
    
    # Initialize MongoDB service
    mongo_service = MongoDBService()
    
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
            st.session_state.filtered_results = None
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
                    st.session_state.filtered_results = None  # Reset filtered results
                    st.rerun()
                else:
                    st.warning("No projects found matching your search criteria.")
                    
            except Exception as e:
                st.error(f"Error performing search: {str(e)}")
                
    # Display and filter results
    if st.session_state.get('search_results') is not None:
        df = st.session_state.search_results
        
        # Apply secondary filters if results exist
        filtered_df = filter_projects(
            df,
            key_prefix="secondary_",
            config={
                'value_column': 'sum_price_agree',
                'value_unit': 1e6,
                'value_label': 'Million Baht',
                'expander_default': True
            }
        )
        st.session_state.filtered_results = filtered_df
        
        # Use filtered results if available, otherwise use original results
        display_df = filtered_df if filtered_df is not None else df
        
        # Display metrics for current view
        MetricsSummary(display_df)
        
        # Display quick stats
        st.markdown("### 📊 Quick Statistics")
        
        # Calculate company statistics
        company_stats = display_df.groupby('winner').agg({
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
            top_departments = display_df.groupby('dept_name')['project_name'].count()
            top_departments = top_departments.nlargest(5)
            for idx, (dept, count) in enumerate(top_departments.items()):
                st.markdown(f"{idx+1}. **{dept}**  \n"
                          f"{count} projects")
        
        st.markdown("---")

        st.markdown("### Sub-department Analysis")

        # Display the new sub-department distribution
        display_subdepartment_distribution(filtered_df)

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

        st.markdown("### 📊 Company Project Distribution by Value Range")

        try:
            # Prepare data for all ranges
            range_data = CompanyProjectsService.prepare_data(display_df)
            
            # Show statistics in columns
            st.markdown("#### Distribution Statistics")
            stats = CompanyProjectsService.get_range_statistics(range_data)
            
            # Calculate optimal column layout (3 stats per row)
            num_stats = len(stats)
            stats_per_row = 3
            num_rows = math.ceil(num_stats / stats_per_row)
            
            # Display statistics in rows
            for row in range(num_rows):
                start_idx = row * stats_per_row
                end_idx = min(start_idx + stats_per_row, num_stats)
                row_stats = stats[start_idx:end_idx]
                
                # Create columns for this row
                cols = st.columns(stats_per_row)
                
                # Fill columns with stats
                for col_idx, stat in enumerate(row_stats):
                    with cols[col_idx]:
                        st.markdown(
                            f"""<div style='padding: 10px; border-radius: 5px; background-color: {stat['color']}20;'>
                            <h4>{stat['range']}</h4>
                            Projects: {stat['total_projects']:,}<br>
                            Companies: {stat['total_companies']:,}<br>
                            Total Value: ฿{stat['total_value']:.1f}M<br>
                            Avg Value: ฿{stat['avg_value']:.1f}M
                            </div>""",
                            unsafe_allow_html=True
                        )
                
                # Add empty columns if needed to complete the row
                remaining_cols = stats_per_row - len(row_stats)
                if remaining_cols > 0:
                    for _ in range(remaining_cols):
                        with cols[-(remaining_cols)]:
                            st.empty()
            
            # Create individual charts
            st.markdown("#### Project Distribution")
            for value_range in CompanyProjectsService.VALUE_RANGES:
                range_name = value_range['name']
                if range_name in range_data:
                    fig = CompanyProjectsService.create_chart_for_range(
                        range_data[range_name],
                        range_name,
                        value_range['color']
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    st.markdown("---")
            
        except Exception as e:
            st.error(f"Error creating company distribution charts: {str(e)}")
            st.exception(e)  # This will show the full traceback in development

        st.markdown("---")
        
        # Display results table with built-in search and sorting
        st.markdown(f"### Search Results ({len(display_df):,} projects)")
        ProjectsTable(
            df=display_df,
            filters=filters,
            show_search=True,
            key_prefix="search_results_"
        )
        
        # Add export functionality
        if st.button("📥 Export to CSV", key="export_results"):
            # Prepare export data
            export_df = display_df.copy()
            export_df['transaction_date'] = export_df['transaction_date'].dt.strftime('%Y-%m-%d')
            
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
        st.info("Enter keywords above and click Search to find projects.")

if __name__ == "__main__":
    ProjectSearch()