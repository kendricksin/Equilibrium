# src/components/filters/TableFilter.py

import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any, List
from datetime import datetime
import numpy as np

class TableFilter:
    """Generic table filter utility for project data"""
    
    DEFAULT_CONFIG = {
        'value_column': 'sum_price_agree',
        'value_unit': 1e6,  # Convert to millions
        'value_label': 'Million Baht',
        'date_column': 'transaction_date',
        'company_column': 'winner',
        'department_column': 'dept_name',
        'show_value_filter': True,
        'show_date_filter': True,
        'show_company_filter': True,
        'show_department_filter': True,
        'expander_default': False,
        'min_companies_for_search': 10  # Show search box if more companies than this
    }
    
    def __init__(
        self,
        df: pd.DataFrame,
        key_prefix: str = "",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize TableFilter
        
        Args:
            df (pd.DataFrame): Input DataFrame
            key_prefix (str): Prefix for component keys
            config (Optional[Dict]): Filter configuration
        """
        self.df = df
        self.key_prefix = key_prefix
        self.config = self._validate_config(config or {})
    
    def _validate_config(self, user_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge and validate user config with defaults"""
        config = self.DEFAULT_CONFIG.copy()
        config.update(user_config)
        return config
    
    def _add_value_filter(self, col) -> Optional[tuple]:
        """Add value range filter"""
        if not self.config['show_value_filter']:
            return None
            
        value_col = self.config['value_column']
        if value_col not in self.df.columns:
            return None
            
        min_value = float(self.df[value_col].min()) / self.config['value_unit']
        max_value = float(self.df[value_col].max()) / self.config['value_unit']
        
        col.markdown(f"**Value Range ({self.config['value_label']})**")
        value_range = col.slider(
            "Project Value",
            min_value=min_value,
            max_value=max_value,
            value=(min_value, max_value),
            key=f"{self.key_prefix}value_range"
        )
        
        return value_range
    
    def _add_company_filter(self, col) -> Optional[List[str]]:
        """Add company filter"""
        if not self.config['show_company_filter']:
            return None
            
        company_col = self.config['company_column']
        if company_col not in self.df.columns:
            return None
        
        # Get company counts and sort by frequency
        company_counts = self.df[company_col].value_counts()
        company_options = [
            {'name': company, 'count': count} 
            for company, count in company_counts.items()
        ]
        
        col.markdown("**Company Filter**")
        
        # Add search box for companies if there are many
        if len(company_options) >= self.config['min_companies_for_search']:
            search_term = col.text_input(
                "Search companies",
                key=f"{self.key_prefix}company_search"
            ).lower()
            
            if search_term:
                company_options = [
                    opt for opt in company_options 
                    if search_term in str(opt['name']).lower()
                ]
        
        # Create formatted options for display
        formatted_options = {
            f"{opt['name']} ({opt['count']} projects)": opt['name']
            for opt in company_options
        }
        
        selected_labels = col.multiselect(
            "Select Companies",
            options=list(formatted_options.keys()),
            key=f"{self.key_prefix}companies"
        )
        
        # Convert selected labels back to company names
        selected_companies = [
            formatted_options[label]
            for label in selected_labels
        ]
        
        return selected_companies
    
    def _add_department_filter(self, col) -> Optional[List[str]]:
        """Add department filter"""
        if not self.config['show_department_filter']:
            return None
            
        dept_col = self.config['department_column']
        if dept_col not in self.df.columns:
            return None
        
        # Get department counts and sort by frequency
        dept_counts = self.df[dept_col].value_counts()
        dept_options = [
            {'name': dept, 'count': count} 
            for dept, count in dept_counts.items()
        ]
        
        col.markdown("**Department Filter**")
        
        # Create formatted options for display
        formatted_options = {
            f"{opt['name']} ({opt['count']} projects)": opt['name']
            for opt in dept_options
        }
        
        selected_labels = col.multiselect(
            "Select Departments",
            options=list(formatted_options.keys()),
            key=f"{self.key_prefix}departments"
        )
        
        # Convert selected labels back to department names
        selected_depts = [
            formatted_options[label]
            for label in selected_labels
        ]
        
        return selected_depts
    
    def _add_date_filter(self, col) -> Optional[tuple]:
        """Add date range filter"""
        if not self.config['show_date_filter']:
            return None
            
        date_col = self.config['date_column']
        if date_col not in self.df.columns:
            return None
            
        min_date = self.df[date_col].min()
        max_date = self.df[date_col].max()
        
        col.markdown("**Date Range**")
        start_date = col.date_input(
            "Start Date",
            value=min_date,
            min_value=min_date,
            max_value=max_date,
            key=f"{self.key_prefix}start_date"
        )
        
        end_date = col.date_input(
            "End Date",
            value=max_date,
            min_value=min_date,
            max_value=max_date,
            key=f"{self.key_prefix}end_date"
        )
        
        return start_date, end_date
    
    def filter_dataframe(self) -> pd.DataFrame:
        """Apply filters to the DataFrame"""
        st.markdown("### 🎯 Refine Results")
        
        with st.expander("Advanced Filters", expanded=self.config['expander_default']):
            col1, col2 = st.columns(2)
            filtered_df = self.df.copy()
            active_filters = []
            
            # Add filters to columns
            with col1:
                # Value range filter
                value_range = self._add_value_filter(col1)
                if value_range:
                    filtered_df = filtered_df[
                        (filtered_df[self.config['value_column']] >= value_range[0] * self.config['value_unit']) &
                        (filtered_df[self.config['value_column']] <= value_range[1] * self.config['value_unit'])
                    ]
                    min_val = float(self.df[self.config['value_column']].min()) / self.config['value_unit']
                    max_val = float(self.df[self.config['value_column']].max()) / self.config['value_unit']
                    if value_range != (min_val, max_val):
                        active_filters.append(
                            f"Value: {value_range[0]:.1f} - {value_range[1]:.1f} {self.config['value_label']}"
                        )
                
                # Company filter
                selected_companies = self._add_company_filter(col1)
                if selected_companies:
                    filtered_df = filtered_df[
                        filtered_df[self.config['company_column']].isin(selected_companies)
                    ]
                    active_filters.append(f"Companies: {len(selected_companies)} selected")
            
            with col2:
                # Department filter
                selected_depts = self._add_department_filter(col2)
                if selected_depts:
                    filtered_df = filtered_df[
                        filtered_df[self.config['department_column']].isin(selected_depts)
                    ]
                    active_filters.append(f"Departments: {len(selected_depts)} selected")
                
                # Date range filter
                date_range = self._add_date_filter(col2)
                if date_range:
                    start_date, end_date = date_range
                    filtered_df = filtered_df[
                        (filtered_df[self.config['date_column']].dt.date >= start_date) &
                        (filtered_df[self.config['date_column']].dt.date <= end_date)
                    ]
                    min_date = self.df[self.config['date_column']].min().date()
                    max_date = self.df[self.config['date_column']].max().date()
                    if start_date != min_date or end_date != max_date:
                        active_filters.append(f"Date: {start_date} to {end_date}")
            
        # Show filter summary and clear button
        if len(filtered_df) != len(self.df):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Filtered {len(filtered_df):,} out of {len(self.df):,} projects**")
                if active_filters:
                    st.markdown("**Active Filters:** " + " | ".join(active_filters))
            
            with col2:
                if st.button("🔄 Clear Secondary Filters", 
                            key=f"{self.key_prefix}clear_filters",
                            use_container_width=True):
                    # Reset all session state keys used by this filter instance
                    for key in st.session_state:
                        if key.startswith(self.key_prefix):
                            del st.session_state[key]
                    st.rerun()
        
        return filtered_df

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
    filter_util = TableFilter(df, key_prefix, config)
    return filter_util.filter_dataframe()