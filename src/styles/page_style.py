# src/styles/hide_navigation.py

import streamlit as st

def hide_default_pages():
    """Hide the default Streamlit navigation menu"""
    st.markdown("""
        <style>
            /* Hide default Streamlit navigation */
            header[data-testid="stHeader"] {
                display: none !important;
            }
            
            /* Hide top pages section */
            section[data-testid="stSidebarNav"] {
                display: none !important;
            }
            
            /* Hide navigation buttons */
            button[kind="header"] {
                display: none !important;
            }
            
            /* Hide navigation menu items */
            .stApp > header {
                display: none !important;
            }
            
            /* Ensure the sidebar starts at the top */
            .main .block-container {
                padding-top: 1rem !important;
            }
            
            /* Hide the hamburger menu */
            [data-testid="collapsedControl"] {
                display: none !important;
            }
        </style>
    """, unsafe_allow_html=True)