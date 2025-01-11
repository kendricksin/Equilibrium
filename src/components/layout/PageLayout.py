# src/components/layout/PageLayout.py

import streamlit as st
from typing import Callable
from components.layout.Navigation import render_navigation
from styles.page_style import hide_default_pages

def PageLayout(page_function: Callable):
    """
    Wrapper for page content that handles common layout elements
    
    Args:
        page_function: The main function containing page content
    """
    
    # Hide default navigation
    hide_default_pages()
    
    # Render navigation sidebar
    render_navigation()
    
    # Execute the page content
    page_function()