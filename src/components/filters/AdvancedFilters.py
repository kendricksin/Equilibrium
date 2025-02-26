# src/components/filters/AdvancedFilters.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class AdvancedFilters:
    """Enhanced filter component with quick selectors"""
    
    VALUE_RANGES = [
        {'label': 'All Values', 'min': None, 'max': None},
        {'label': '1-10M', 'min': 1, 'max': 10},
        {'label': '10-50M', 'min': 10, 'max': 50},
        {'label': '50-100M', 'min': 50, 'max': 100},
        {'label': '100-300M', 'min': 100, 'max': 300},
        {'label': '>300M', 'min': 300, 'max': None}
    ]
    
    DATE_RANGES = [
        {'label': 'All Time', 'days': None},
        {'label': '3 Years', 'days': 1095},
        {'label': '1 Year', 'days': 365},
        {'label': '6 Months', 'days': 180}
    ]
    
    def __init__(
        self,
        data: pd.DataFrame,
        key_prefix: str = "",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize AdvancedFilters
        
        Args:
            data: DataFrame containing the search results to filter
            key_prefix: Prefix for session state keys
            config: Optional configuration dictionary
        """
        self.data = data
        self.key_prefix = key_prefix
        self.config = self._get_default_config()
        if config:
            self.config.update(config)
        
        # Get date range from data
        self.min_date = pd.to_datetime(data['transaction_date']).min()
        self.max_date = pd.to_datetime(data['transaction_date']).max()
        
        # Get unique values from data
        self.unique_companies = sorted(data['winner'].unique())
        self.unique_departments = sorted(data['dept_name'].unique())
        self.unique_subdepartments = sorted(data['dept_sub_name'].unique())
        self.unique_project_types = sorted(data['project_type_name'].unique())
        self.unique_procurement_methods = sorted(data['purchase_method_name'].unique())
            
        # Initialize session state with default values
        default_state = {
            'value_min': None,
            'value_max': None,
            'value_range': 'All Values',
            'date_start': self.min_date,
            'date_end': self.max_date,
            'date_range': 'All Time',
            'departments': [],
            'subdepartments': [],
            'project_types': [],
            'procurement_methods': [],
            'companies': []
        }
        
        # Create or update session state
        if f"{key_prefix}_advanced_filters" not in st.session_state:
            st.session_state[f"{key_prefix}_advanced_filters"] = default_state
        else:
            # Update any missing keys while preserving existing values
            current_state = st.session_state[f"{key_prefix}_advanced_filters"]
            for key, value in default_state.items():
                if key not in current_state:
                    current_state[key] = value
            st.session_state[f"{key_prefix}_advanced_filters"] = current_state
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'show_value_range': True,
            'show_date_range': True,
            'show_departments': True,
            'show_subdepartments': True,
            'show_project_types': True,
            'show_procurement_methods': True,
            'show_companies': True,
            'max_selections': 10
        }
    
    def render(self) -> Dict[str, Any]:
        """
        Render advanced filters
        
        Returns:
            Dictionary of filter values
        """
        filters = st.session_state[f"{self.key_prefix}_advanced_filters"].copy()
        
        with st.expander("Advanced Filters", expanded=True):
            col1, col2 = st.columns(2)
            
            # Value Range Filter
            if self.config['show_value_range']:
                with col1:
                    st.write("Value Range (Million Baht)")
                    range_option = st.selectbox(
                        "Quick Select",
                        options=[r['label'] for r in self.VALUE_RANGES],
                        index=0,
                        key=f"{self.key_prefix}_value_range"
                    )
                    
                    # Update min/max based on selection
                    selected_range = next(r for r in self.VALUE_RANGES if r['label'] == range_option)
                    filters['value_min'] = selected_range['min']
                    filters['value_max'] = selected_range['max']
                    filters['value_range'] = range_option
            
            # Date Range Filter
            if self.config['show_date_range']:
                with col2:
                    st.write("Date Range")
                    date_option = st.selectbox(
                        "Quick Select",
                        options=[r['label'] for r in self.DATE_RANGES],
                        index=0,
                        key=f"{self.key_prefix}_date_range"
                    )
                    
                    # Update date range based on selection
                    selected_date_range = next(r for r in self.DATE_RANGES if r['label'] == date_option)
                    if selected_date_range['days'] is None:
                        filters['date_start'] = self.min_date
                        filters['date_end'] = self.max_date
                    else:
                        filters['date_end'] = self.max_date
                        filters['date_start'] = filters['date_end'] - pd.Timedelta(days=selected_date_range['days'])
                    filters['date_range'] = date_option
            
            col3, col4 = st.columns(2)
            
            # Department Filter
            if self.config['show_departments']:
                with col3:
                    filters['departments'] = st.multiselect(
                        "Select Departments",
                        options=self.unique_departments,
                        default=filters['departments'],
                        key=f"{self.key_prefix}_departments"
                    )
            
            # Subdepartment Filter
            if self.config['show_subdepartments']:
                with col4:
                    available_subdepts = self.unique_subdepartments
                    if filters['departments']:
                        available_subdepts = sorted(
                            self.data[self.data['dept_name'].isin(filters['departments'])]
                            ['dept_sub_name'].unique()
                        )
                    
                    filters['subdepartments'] = st.multiselect(
                        "Select Subdepartments",
                        options=available_subdepts,
                        default=[s for s in filters['subdepartments'] if s in available_subdepts],
                        key=f"{self.key_prefix}_subdepartments"
                    )
            
            col5, col6 = st.columns(2)
            
            # Project Type Filter
            if self.config['show_project_types']:
                with col5:
                    filters['project_types'] = st.multiselect(
                        "Select Project Types",
                        options=self.unique_project_types,
                        default=filters['project_types'],
                        key=f"{self.key_prefix}_project_types"
                    )
            
            # Procurement Method Filter
            if self.config['show_procurement_methods']:
                with col6:
                    filters['procurement_methods'] = st.multiselect(
                        "Select Procurement Methods",
                        options=self.unique_procurement_methods,
                        default=filters['procurement_methods'],
                        key=f"{self.key_prefix}_procurement_methods"
                    )
            
            # Company Filter
            if self.config['show_companies']:
                filters['companies'] = st.multiselect(
                    "Select Companies",
                    options=self.unique_companies,
                    default=filters['companies'],
                    key=f"{self.key_prefix}_companies"
                )
            
            # Apply/Clear buttons
            col7, col8 = st.columns([4, 1])
            with col8:
                if st.button("Clear Filters", key=f"{self.key_prefix}_clear"):
                    st.session_state[f"{self.key_prefix}_advanced_filters"] = {
                        'value_min': None,
                        'value_max': None,
                        'value_range': 'All Values',
                        'date_start': self.min_date,
                        'date_end': self.max_date,
                        'date_range': 'All Time',
                        'departments': [],
                        'subdepartments': [],
                        'project_types': [],
                        'procurement_methods': [],
                        'companies': []
                    }
                    st.rerun()
            
            with col7:
                apply_clicked = st.button(
                    "Apply Filters",
                    key=f"{self.key_prefix}_apply",
                    type="primary"
                )
        
        if apply_clicked:
            st.session_state[f"{self.key_prefix}_advanced_filters"] = filters
            return filters
        
        return st.session_state[f"{self.key_prefix}_advanced_filters"] 