# src/components/layout/Header.py

import streamlit as st
from typing import Optional

def Header(
    current_page: str = "Home",
    show_navigation: bool = True,
    user_name: Optional[str] = None
):
    """
    A component that displays the header with navigation and user info.
    
    Args:
        current_page (str): Current active page name
        show_navigation (bool): Whether to show navigation menu
        user_name (Optional[str]): User name to display if logged in
    """
    with st.container():
        # Header Style
        st.markdown("""
            <style>
            .header-container {
                padding: 1rem 0;
                margin-bottom: 2rem;
                border-bottom: 1px solid #eee;
            }
            </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="header-container">', unsafe_allow_html=True)
        
        # Header Content
        col1, col2, col3 = st.columns([2, 6, 2])
        
        with col1:
            st.markdown("### 📊 ProjectDB")
        
        # Navigation Menu
        if show_navigation:
            with col2:
                st.markdown("""
                    <style>
                    .nav-link {
                        margin-right: 1rem;
                        text-decoration: none;
                    }
                    .nav-active {
                        font-weight: bold;
                    }
                    </style>
                """, unsafe_allow_html=True)
                
                col_nav1, col_nav2, col_nav3 = st.columns(3)
                
                with col_nav1:
                    if st.button(
                        "🏠 Home",
                        key="nav_home",
                        use_container_width=True,
                        type="primary" if current_page == "Home" else "secondary"
                    ):
                        st.session_state.current_page = "home"
                        st.rerun()
                
                with col_nav2:
                    if st.button(
                        "🎯 Analysis",
                        key="nav_analysis",
                        use_container_width=True,
                        type="primary" if current_page == "Analysis" else "secondary"
                    ):
                        st.session_state.current_page = "analysis"
                        st.rerun()
                
                with col_nav3:
                    if st.button(
                        "🔍 Search",
                        key="nav_search",
                        use_container_width=True,
                        type="primary" if current_page == "Search" else "secondary"
                    ):
                        st.session_state.current_page = "search"
                        st.rerun()
        
        # User Info or Actions
        with col3:
            if user_name:
                st.markdown(f"👤 {user_name}")
        
        st.markdown('</div>', unsafe_allow_html=True)