# src/app.py

import streamlit as st
import logging
from state.session import SessionState
from components.layout.Navigation import render_navigation
from pages.Home import Home
from pages import (
    ProjectSearch,
    DepartmentSearch,
    CompanySearch,
    StackedCompany,
    ContextManager
)
from styles.page_style import hide_default_pages

st.set_page_config(layout="wide")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    hide_default_pages()

    try:
        # Initialize session state
        SessionState.initialize_state()
        
        # Render navigation and get selected page
        selected_page = render_navigation()
        
        # Route to appropriate page
        if selected_page == "Home":
            Home()
        elif selected_page == "Project Search":
            ProjectSearch.ProjectSearch()
        elif selected_page == "Department Search":
            DepartmentSearch.DepartmentSearch()
        elif selected_page == "Company Search":
            CompanySearch.CompanySearch()
        elif selected_page == "Stacked Company Analysis":
            StackedCompany.StackedCompany()
        elif selected_page == "Context Manager":
            ContextManager.ContextManager()
            
    except Exception as e:
        logger.error(f"Error in application: {e}")
        st.error("An unexpected error occurred. Please try again later.")

if __name__ == "__main__":
    main()