# src/components/filters/TableFilter.py

import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import numpy as np
from utils.validators import Validators
from utils.formatters import Formatters
import logging

logger = logging.getLogger(__name__)

class TableFilter:
    """Enhanced table filter component with validation and formatting"""
    
    def __init__(
        self,
        key_prefix: str = "",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize TableFilter
        
        Args:
            key_prefix: Prefix for component keys
            config: Filter configuration options
        """
        self.key_prefix = key_prefix
        self.config = self._get_default_config()
        if config:
            self.config.update(config)
        self.validators = Validators()
        self.formatters = Formatters()
        
        # Initialize session state for filters
        if f"{key_prefix}_filters" not in st.session_state:
            st.session_state[f"{key_prefix}_filters"] = {
                'date_start': datetime(2019, 1, 1),
                'date_end': datetime(2024, 12, 31),
                'min_value': None,
                'max_value': 300,
                'dept_name': None,
                'companies': []
            }
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default filter configuration"""
        return {
            'show_date_filter': True,
            'show_value_filter': True,
            'show_department_filter': True,
            'show_company_filter': True,
            'max_companies': 10,
            'date_format': '%Y-%m-%d',
            'currency_code': 'THB',
            'value_unit': 1e6  # Convert to millions
        }
    
    def render(
        self,
        departments: Optional[List[str]] = None,
        companies: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Render filter controls
        
        Args:
            departments: List of available departments
            companies: List of available companies
            
        Returns:
            Dictionary of filter values
        """
        current_filters = st.session_state[f"{self.key_prefix}_filters"]
        new_filters = {}
        
        with st.expander("🔍 Filter Options", expanded=False):
            col1, col2 = st.columns(2)
            
            # Date Range Filter
            if self.config['show_date_filter']:
                with col1:
                    new_filters['date_start'] = st.date_input(
                        "Start Date",
                        value=current_filters['date_start'],
                        key=f"{self.key_prefix}_start_date_input"
                    )
                with col2:
                    new_filters['date_end'] = st.date_input(
                        "End Date",
                        value=current_filters['date_end'],
                        key=f"{self.key_prefix}_end_date_input"
                    )
            
            # Value Range Filter
            if self.config['show_value_filter']:
                col3, col4 = st.columns(2)
                with col3:
                    # Convert current value to float for display
                    current_min = (
                        float(current_filters['min_value'] / self.config['value_unit'])
                        if current_filters['min_value'] is not None
                        else 0.0
                    )
                    min_value = st.number_input(
                        "Min Value (Million THB)",
                        value=current_min,
                        min_value=0.0,
                        step=1.0,
                        format="%.1f",
                        key=f"{self.key_prefix}_min_value_input"
                    )
                    new_filters['min_value'] = float(min_value * self.config['value_unit'])
                
                with col4:
                    # Convert current value to float for display
                    current_max = (
                        float(current_filters['max_value'] / self.config['value_unit'])
                        if current_filters['max_value'] is not None
                        else 0.0
                    )
                    max_value = st.number_input(
                        "Max Value (Million THB)",
                        value=current_max,
                        min_value=0.0,
                        step=1.0,
                        format="%.1f",
                        key=f"{self.key_prefix}_max_value_input"
                    )
                    new_filters['max_value'] = (
                        float(max_value * self.config['value_unit'])
                        if max_value > 0
                        else None
                    )
            
            # Department Filter
            if self.config['show_department_filter'] and departments:
                new_filters['dept_name'] = st.selectbox(
                    "Department",
                    options=['All Departments'] + departments,
                    index=0,
                    key=f"{self.key_prefix}_dept_input"
                )
                if new_filters['dept_name'] == 'All Departments':
                    new_filters['dept_name'] = None
            
            # Company Filter
            if self.config['show_company_filter'] and companies:
                new_filters['companies'] = st.multiselect(
                    "Companies",
                    options=companies,
                    default=current_filters['companies'],
                    key=f"{self.key_prefix}_companies_input",
                    max_selections=self.config['max_companies']
                )
            
            # Apply button
            col5, col6 = st.columns([4, 1])
            with col6:
                apply_clicked = st.button(
                    "Apply Filters",
                    key=f"{self.key_prefix}_apply",
                    type="primary"
                )
            with col5:
                if st.button("Clear Filters", key=f"{self.key_prefix}_clear"):
                    st.session_state[f"{self.key_prefix}_filters"] = {
                        'date_start': datetime(2019, 1, 1),
                        'date_end': datetime(2024, 12, 31),
                        'min_value': None,
                        'max_value': None,
                        'dept_name': None,
                        'companies': []
                    }
                    st.rerun()
        
        if apply_clicked:
            st.session_state[f"{self.key_prefix}_filters"] = new_filters
            return new_filters
        
        return current_filters
    
    def apply_filters(
        self,
        df: pd.DataFrame,
        filters: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        Apply filters to DataFrame
        
        Args:
            df: Input DataFrame
            filters: Dictionary of filter values
            
        Returns:
            Filtered DataFrame
        """
        try:
            filtered_df = df.copy()
            
            # Validate filters
            validation_errors = self.validators.validate_filters(filters)
            if validation_errors:
                for error in validation_errors.values():
                    st.warning(error)
                return filtered_df
            
            # Apply date filter
            if 'date_start' in filters and 'date_end' in filters:
                filtered_df = filtered_df[
                    (filtered_df['transaction_date'].dt.date >= filters['date_start']) &
                    (filtered_df['transaction_date'].dt.date <= filters['date_end'])
                ]
            
            # Apply value filter
            if 'min_value' in filters:
                filtered_df = filtered_df[
                    filtered_df['sum_price_agree'] >= filters['min_value']
                ]
            if 'max_value' in filters:
                filtered_df = filtered_df[
                    filtered_df['sum_price_agree'] <= filters['max_value']
                ]
            
            # Apply department filter
            if 'dept_name' in filters:
                filtered_df = filtered_df[
                    filtered_df['dept_name'] == filters['dept_name']
                ]
            
            # Apply company filter
            if 'companies' in filters:
                filtered_df = filtered_df[
                    filtered_df['winner'].isin(filters['companies'])
                ]
            
            return filtered_df
            
        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            st.error("Error applying filters")
            return df

def filter_projects(
    df: pd.DataFrame,
    key_prefix: str = "",
    config: Optional[Dict[str, Any]] = None
) -> pd.DataFrame:
    """
    Convenience function to filter project DataFrame
    
    Args:
        df (pd.DataFrame): Input DataFrame
        key_prefix (str): Prefix for component keys
        config (Optional[Dict]): Filter configuration
        
    Returns:
        pd.DataFrame: Filtered DataFrame
    """
    filter_util = TableFilter(key_prefix, config)
    return filter_util.apply_filters(df, filter_util.render())
