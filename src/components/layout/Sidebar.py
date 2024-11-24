# src/components/layout/Sidebar.py

import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
from services.department_service import get_departments, get_sub_departments

logger = logging.getLogger(__name__)

def Sidebar(
    filters: Optional[Dict[str, Any]] = None,
    selected_companies: Optional[list] = None,
    on_filter_change: Optional[callable] = None
) -> Dict[str, Any]:
    """Sidebar component with filters"""
    with st.sidebar:
        st.markdown("### 🔍 Filters")
        
        # Initialize default filters if none provided
        if filters is None:
            filters = {
                'dept_name': '',
                'dept_sub_name': '',
                'date_start': datetime(2022, 1, 1).date(),
                'date_end': datetime(2023, 12, 31).date(),
                'price_start': 0.0,
                'price_end': 200.0
            }
        
        # Department Filters
        departments = [""] + get_departments()
        
        # Find the correct index for the current department
        current_dept = filters.get('dept_name', '')
        try:
            dept_index = departments.index(current_dept)
        except ValueError:
            logger.warning(f"Saved department '{current_dept}' not found in current list")
            dept_index = 0
        
        new_dept = st.selectbox(
            "Department",
            options=departments,
            index=dept_index,
            key="sidebar_dept"
        )
        
        # Sub-department filter
        new_sub_dept = ""
        if new_dept:
            sub_departments = [""] + get_sub_departments(new_dept)
            
            # Find the correct index for the current sub-department
            current_sub_dept = filters.get('dept_sub_name', '')
            try:
                sub_dept_index = sub_departments.index(current_sub_dept)
            except ValueError:
                logger.warning(f"Saved sub-department '{current_sub_dept}' not found in current list")
                sub_dept_index = 0
            
            new_sub_dept = st.selectbox(
                "Sub-Department",
                options=sub_departments,
                index=sub_dept_index,
                key="sidebar_sub_dept"
            )
        
        # Date Range
        st.markdown("#### Date Range")
        new_date_start = st.date_input(
            "Start Date",
            value=filters['date_start'],
            key="sidebar_date_start"
        )
        new_date_end = st.date_input(
            "End Date",
            value=filters['date_end'],
            key="sidebar_date_end"
        )
        
        # Price Range
        st.markdown("#### Price Range (Million Baht)")
        price_col1, price_col2 = st.columns(2)
        
        with price_col1:
            new_price_start = st.number_input(
                "From",
                min_value=0.0,
                max_value=10000.0,
                value=float(filters['price_start']),
                step=10.0,
                format="%.1f",
                key="sidebar_price_start"
            )
        
        with price_col2:
            new_price_end = st.number_input(
                "To",
                min_value=0.0,
                max_value=20000.0,
                value=float(filters['price_end']),
                step=10.0,
                format="%.1f",
                key="sidebar_price_end"
            )
        
        # Create new filters dictionary
        new_filters = {
            'dept_name': new_dept,
            'dept_sub_name': new_sub_dept,
            'date_start': new_date_start,
            'date_end': new_date_end,
            'price_start': new_price_start,
            'price_end': new_price_end
        }
        
        # Apply Filters button
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Apply", type="primary", use_container_width=True):
                if on_filter_change:
                    on_filter_change(new_filters)
                st.session_state.filters_applied = True
                return new_filters
        
        # with col2:
        #     if st.button("❌ Clear", use_container_width=True):
        #         if on_filter_change:
        #             on_filter_change(FilterManager.get_default_filters())
        #         st.session_state.filters_applied = False
        #         st.rerun()
        
        # Show selection summary if companies are selected
        if selected_companies:
            st.markdown("---")
            st.markdown("### 📊 Selection Summary")
            st.markdown(f"**Selected Companies:** {len(selected_companies)}")
            
            # Add button to modify selection
            if st.button("✏️ Modify Selection", use_container_width=True):
                st.session_state.current_page = 'company_selection'
                st.rerun()
        
        return new_filters