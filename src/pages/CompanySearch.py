# src/pages/CompanySearch.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import logging
from services.database.mongodb import MongoDBService

# Configure logging
logger = logging.getLogger(__name__)

def CompanySearch():
    """Company search and comparison page"""
    
    # Page config
    st.set_page_config(layout="wide")
    
    # Initialize MongoDB service
    mongo = MongoDBService()
    collection = mongo.get_collection("companies")
    
    # Get all companies once and cache them using st.cache_data
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def get_all_companies():
        companies = list(collection.find(
            {},
            {"winner": 1, "project_count": 1, "project_ids": 1}
        ).sort("project_count", -1))  # Sort by project count descending
        
        logger.info(f"Retrieved {len(companies)} companies from database")
        
        # Validate project counts
        for company in companies:
            project_ids_count = len(company.get('project_ids', []))
            stated_count = company.get('project_count', 0)
            if project_ids_count != stated_count:
                logger.warning(
                    f"Project count mismatch for {company['winner']}: "
                    f"stated={stated_count}, actual={project_ids_count}"
                )
        
        return companies
    
    companies = get_all_companies()
    
    # Create company options with validated project counts
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
    
    # Create two columns for company selection
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
            company_doc = collection.find_one({"winner": company_name})
            if company_doc:
                logger.info(
                    f"Company 1 details - Name: {company_name}, "
                    f"Project Count: {company_doc['project_count']}, "
                    f"Project IDs: {len(company_doc['project_ids'])}"
                )
                company_data.append(company_doc)
    
    with col2:
        st.markdown("##### Company 2")
        # Filter out the first selected company from options
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
            company_doc = collection.find_one({"winner": company_name})
            if company_doc:
                logger.info(
                    f"Company 2 details - Name: {company_name}, "
                    f"Project Count: {company_doc['project_count']}, "
                    f"Project IDs: {len(company_doc['project_ids'])}"
                )
                company_data.append(company_doc)
    
    # Display comparison if companies are selected
    if len(company_data) > 0:
        st.markdown("### 📊 Company Comparison")
        
        # Create metric columns
        cols = st.columns(len(company_data))
        
        for idx, (col, data) in enumerate(zip(cols, company_data)):
            with col:
                st.markdown(f"#### {data['winner']}")
                
                # Log actual project counts vs project IDs
                actual_project_count = len(data['project_ids'])
                logger.info(
                    f"Company {data['winner']} metrics - "
                    f"Stated Count: {data['project_count']}, "
                    f"Project IDs: {actual_project_count}"
                )
                
                # Use actual project count from project_ids
                st.metric("Total Projects", f"{actual_project_count:,}")
                st.metric("Total Value", f"฿{data['total_value']/1e6:.2f}M")
                st.metric("Average Project Value", f"฿{data['avg_project_value']/1e6:.2f}M")
                st.metric("Active Years", data['active_years'])
                st.metric("Departments", len(data['departments']))
                
                # Show departments
                st.markdown("##### Departments:")
                for dept in data['departments']:
                    st.markdown(f"• {dept}")

        # Projects comparison table
        if len(company_data) > 0:
            st.markdown("### 📋 Project Comparison")

            # Get project IDs from both companies
            all_project_ids = []
            for data in company_data:
                project_ids = data.get('project_ids', [])
                logger.info(
                    f"Adding {len(project_ids)} project IDs for {data['winner']}"
                )
                all_project_ids.extend(project_ids)

            logger.info(f"Total unique project IDs to fetch: {len(set(all_project_ids))}")

            # Fetch projects from main collection
            projects_collection = mongo.get_collection("projects")
            projects = list(projects_collection.find(
                {"project_id": {"$in": all_project_ids}},
                {
                    "project_id": 1,
                    "project_name": 1,
                    "winner": 1,
                    "dept_name": 1,
                    "transaction_date": 1,
                    "sum_price_agree": 1,
                    "price_build": 1
                }
            ))

            logger.info(f"Retrieved {len(projects)} projects from database")

            if projects:
                # Convert to DataFrame
                df = pd.DataFrame(projects)
                
                # Log project counts by company
                for company in selected_companies:
                    company_projects = len(df[df['winner'] == company])
                    logger.info(
                        f"Projects found for {company}: {company_projects}"
                    )
                
                # Use the ProjectsTable component
                from components.tables.ProjectsTable import ProjectsTable
                ProjectsTable(
                    df=df,
                    show_search=True,
                    key_prefix="company_comparison_"
                )

                # Add download button for raw data
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Download Project List",
                    csv,
                    "company_projects_comparison.csv",
                    "text/csv",
                    key='download-csv'
                )
            else:
                logger.warning(
                    f"No projects found for IDs: {all_project_ids}"
                )
                st.info("No project details available for these companies.")

if __name__ == "__main__":
    CompanySearch()