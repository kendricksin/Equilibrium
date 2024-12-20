# src/components/layout/Sidebar.py

import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd
from components.filters.DeptFilter import DepartmentFilter
from components.filters.DatePriceFilter import DatePriceFilter
from components.filters.PurchaseTypeFilter import PurchaseTypeFilter
from services.cache.department_cache import get_departments, get_sub_departments
from services.cache.purchase_type_cache import get_purchase_methods, get_project_types
from state.session import SessionState

def Sidebar(
    filters: Optional[Dict[str, Any]] = None,
    selected_companies: Optional[list] = None,
    on_filter_change: Optional[callable] = None
) -> Dict[str, Any]:
    """Sidebar component with enhanced filters and home redirection"""
    with st.sidebar:
        st.markdown("### 🔍 Filters")
        
        # Initialize default filters
        if filters is None:
            filters = {
                'dept_name': '',
                'dept_sub_name': '',
                'purchase_method_name': '',
                'project_type_name': '',
                'date_start': datetime(2022, 1, 1).date(),
                'date_end': datetime(2023, 12, 31).date(),
                'price_start': 0.0,
                'price_end': 200.0
            }
        
        # Department filter
        dept, sub_dept = DepartmentFilter(
            departments=get_departments(),
            current_dept=filters['dept_name'],
            current_sub_dept=filters['dept_sub_name'],
            get_sub_departments_fn=get_sub_departments,
            key_prefix="sidebar_"
        )
        
        # Purchase method and project type filter
        purchase_method, project_type = PurchaseTypeFilter(
            purchase_methods=get_purchase_methods(),
            project_types=get_project_types(),
            current_method=filters['purchase_method_name'],
            current_type=filters['project_type_name'],
            key_prefix="sidebar_"
        )
        
        # Date and price filter
        date_start, date_end, price_start, price_end = DatePriceFilter(
            current_date_start=filters['date_start'],
            current_date_end=filters['date_end'],
            current_price_start=filters['price_start'],
            current_price_end=filters['price_end'],
            key_prefix="sidebar_"
        )
        
        # Create new filters dictionary
        new_filters = {
            'dept_name': dept,
            'dept_sub_name': sub_dept,
            'purchase_method_name': purchase_method,
            'project_type_name': project_type,
            'date_start': date_start,
            'date_end': date_end,
            'price_start': price_start,
            'price_end': price_end
        }
        
        # Apply Filters button
        if st.button("🔄 Apply Filters", type="primary", use_container_width=True):
            # Update filters
            SessionState.update_filters(new_filters)
            st.session_state.filters_applied = True
            
            # Set navigation target
            st.session_state.next_page = 'Home'
            
            # Call filter change callback if provided
            if on_filter_change:
                on_filter_change(new_filters)
            
            # Use streamlit's native navigation
            st.switch_page("pages/Home.py")
            
        # Clear Filters button
        if st.button("❌ Clear Filters", use_container_width=True):
            SessionState.clear_filters()
            # Set navigation target
            st.session_state.next_page = 'Home'
            # Use streamlit's native navigation
            st.switch_page("pages/Home.py")
        
        # Selection summary
        if selected_companies:
            st.markdown("---")
            st.markdown("### 📊 Selection Summary")
            st.markdown(f"**Selected Companies:** {len(selected_companies)}")
            
            if st.button("✏️ Modify Selection", use_container_width=True):
                st.session_state.next_page = 'CompanySelection'
                st.switch_page("pages/CompanySelection.py")
        
        return filters