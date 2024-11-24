# src/state/session.py

import streamlit as st
from datetime import datetime, date
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class SessionState:
    """Manages application session state"""
    
    @staticmethod
    def initialize_state():
        """Initialize all session state variables"""
        if 'initialized' not in st.session_state:
            # Page state
            st.session_state.current_page = 'home'
            st.session_state.previous_page = None
            
            # Filter state
            st.session_state.filters = {
                'dept_name': '',
                'dept_sub_name': '',
                'date_start': datetime(2022, 1, 1).date(),
                'date_end': datetime(2023, 12, 31).date(),
                'price_start': 0.0,
                'price_end': 200.0
            }
            
            # Data state
            st.session_state.filtered_df = None
            st.session_state.filters_applied = False
            
            # Selection state
            st.session_state.selected_companies = []
            st.session_state.selected_companies_set = set()
            
            # Analysis state
            st.session_state.analysis_results = {}
            
            # UI state
            st.session_state.show_filters = True
            st.session_state.show_insights = True
            st.session_state.edit_mode = False
            
            # Cache state
            st.session_state.cache_timestamp = {}
            
            st.session_state.initialized = True
            logger.info("Session state initialized")
    
    @staticmethod
    def get_current_page() -> str:
        """Get current page name"""
        return st.session_state.current_page
    
    @staticmethod
    def set_current_page(page: str):
        """Set current page and update navigation history"""
        st.session_state.previous_page = st.session_state.current_page
        st.session_state.current_page = page
    
    @staticmethod
    def get_filters() -> Dict[str, Any]:
        """Get current filter values"""
        return st.session_state.filters
    
    @staticmethod
    def update_filters(new_filters: Dict[str, Any]):
        """Update filter values and mark as applied"""
        st.session_state.filters.update(new_filters)
        st.session_state.filters_applied = True
        st.session_state.filtered_df = None  # Clear cached data
        logger.info("Filters updated")
    
    @staticmethod
    def clear_filters():
        """Reset filters to default values"""
        st.session_state.filters = {
            'dept_name': '',
            'dept_sub_name': '',
            'date_start': datetime(2022, 1, 1).date(),
            'date_end': datetime(2023, 12, 31).date(),
            'price_start': 0.0,
            'price_end': 200.0
        }
        st.session_state.filters_applied = False
        st.session_state.filtered_df = None
        logger.info("Filters cleared")
    
    @staticmethod
    def get_selected_companies() -> List[str]:
        """Get list of selected companies"""
        return st.session_state.selected_companies
    
    @staticmethod
    def update_selected_companies(companies: List[str]):
        """Update selected companies list and set"""
        st.session_state.selected_companies = companies
        st.session_state.selected_companies_set = set(companies)
        logger.info(f"Selected companies updated: {len(companies)} companies")
    
    @staticmethod
    def clear_selections():
        """Clear all selected companies"""
        st.session_state.selected_companies = []
        st.session_state.selected_companies_set = set()
        logger.info("Company selections cleared")
    
    @staticmethod
    def get_filtered_data() -> Optional[Any]:
        """Get cached filtered DataFrame"""
        return st.session_state.filtered_df
    
    @staticmethod
    def set_filtered_data(df: Any):
        """Cache filtered DataFrame"""
        st.session_state.filtered_df = df
        logger.info("Filtered data cached in session state")
    
    @staticmethod
    def clear_cached_data():
        """Clear cached DataFrame"""
        st.session_state.filtered_df = None
        logger.info("Cached data cleared")
    
    @staticmethod
    def toggle_edit_mode():
        """Toggle edit mode for company selection"""
        st.session_state.edit_mode = not st.session_state.edit_mode
    
    @staticmethod
    def is_edit_mode() -> bool:
        """Check if edit mode is active"""
        return st.session_state.edit_mode
    
    @staticmethod
    def update_cache_timestamp(key: str):
        """Update cache timestamp for a specific key"""
        st.session_state.cache_timestamp[key] = datetime.now()
    
    @staticmethod
    def get_cache_timestamp(key: str) -> Optional[datetime]:
        """Get cache timestamp for a specific key"""
        return st.session_state.cache_timestamp.get(key)