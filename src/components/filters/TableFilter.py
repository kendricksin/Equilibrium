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
        'subdepartment_column': 'dept_sub_name',
        'project_type_column': 'project_type_name',
        'procurement_method_column': 'purchase_method_name',
        'show_value_filter': True,
        'show_date_filter': True,
        'show_company_filter': True,
        'show_department_filter': True,
        'show_type_filter': True,
        'show_procurement_filter': True,
        'expander_default': False
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
    
    def _add_department_filters(self, col) -> tuple[Optional[List[str]], Optional[List[str]]]:
        """Add department and sub-department filters"""
        if not self.config['show_department_filter']:
            return None, None
            
        dept_col = self.config['department_column']
        subdept_col = self.config['subdepartment_column']
        
        if dept_col not in self.df.columns:
            return None, None
        
        # Get department counts and sort by frequency
        dept_counts = self.df[dept_col].value_counts()
        dept_options = [
            {'name': dept, 'count': count} 
            for dept, count in dept_counts.items()
        ]
        
        col.markdown("**Department Filters**")
        
        # Create formatted options for display
        formatted_options = {
            f"{opt['name']} ({opt['count']} projects)": opt['name']
            for opt in dept_options
        }
        
        selected_dept_labels = col.multiselect(
            "Select Departments",
            options=list(formatted_options.keys()),
            key=f"{self.key_prefix}departments"
        )
        
        # Convert selected labels back to department names
        selected_depts = [
            formatted_options[label]
            for label in selected_dept_labels
        ]
        
        # Sub-department filter (only if departments are selected)
        selected_subdepts = []
        # Get sub-departments for selected departments
        subdept_df = self.df[self.df[dept_col].isin(selected_depts)]
        subdept_counts = subdept_df[subdept_col].value_counts()
        
        subdept_options = [
            {'name': subdept, 'count': count} 
            for subdept, count in subdept_counts.items()
            if pd.notna(subdept)  # Filter out NaN/None values
        ]
        
        if subdept_options:
            formatted_subdept_options = {
                f"{opt['name']} ({opt['count']} projects)": opt['name']
                for opt in subdept_options
            }
            
            selected_subdept_labels = col.multiselect(
                "Select Sub-departments",
                options=list(formatted_subdept_options.keys()),
                key=f"{self.key_prefix}subdepartments"
            )
            
            selected_subdepts = [
                formatted_subdept_options[label]
                for label in selected_subdept_labels
            ]
        
        return selected_depts, selected_subdepts
    
    def _add_project_type_filter(self, col) -> Optional[List[str]]:
        """Add project type filter"""
        if not self.config['show_type_filter']:
            return None
            
        type_col = self.config['project_type_column']
        if type_col not in self.df.columns:
            return None
        
        # Get type counts and sort by frequency
        type_counts = self.df[type_col].value_counts()
        type_options = [
            {'name': ptype, 'count': count} 
            for ptype, count in type_counts.items()
            if pd.notna(ptype)
        ]
        
        col.markdown("**Project Type Filter**")
        
        # Create formatted options for display
        formatted_options = {
            f"{opt['name']} ({opt['count']} projects)": opt['name']
            for opt in type_options
        }
        
        selected_labels = col.multiselect(
            "Select Project Types",
            options=list(formatted_options.keys()),
            key=f"{self.key_prefix}project_types"
        )
        
        # Convert selected labels back to type names
        selected_types = [
            formatted_options[label]
            for label in selected_labels
        ]
        
        return selected_types
    
    def _add_procurement_method_filter(self, col) -> Optional[List[str]]:
        """Add procurement method filter"""
        if not self.config['show_procurement_filter']:
            return None
            
        method_col = self.config['procurement_method_column']
        if method_col not in self.df.columns:
            return None
        
        # Get method counts and sort by frequency
        method_counts = self.df[method_col].value_counts()
        method_options = [
            {'name': method, 'count': count} 
            for method, count in method_counts.items()
            if pd.notna(method)
        ]
        
        col.markdown("**Procurement Method Filter**")
        
        # Create formatted options for display
        formatted_options = {
            f"{opt['name']} ({opt['count']} projects)": opt['name']
            for opt in method_options
        }
        
        selected_labels = col.multiselect(
            "Select Procurement Methods",
            options=list(formatted_options.keys()),
            key=f"{self.key_prefix}procurement_methods"
        )
        
        # Convert selected labels back to method names
        selected_methods = [
            formatted_options[label]
            for label in selected_labels
        ]
        
        return selected_methods

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
            
            # Create three columns for better organization
            col1, col2, col3 = st.columns(3)
            
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
                
                # Department and sub-department filters
                selected_depts, selected_subdepts = self._add_department_filters(col1)
                if selected_depts:
                    filtered_df = filtered_df[
                        filtered_df[self.config['department_column']].isin(selected_depts)
                    ]
                    active_filters.append(f"Departments: {len(selected_depts)} selected")
                
                if selected_subdepts:
                    filtered_df = filtered_df[
                        filtered_df[self.config['subdepartment_column']].isin(selected_subdepts)
                    ]
                    active_filters.append(f"Sub-departments: {len(selected_subdepts)} selected")
            
            with col2:
                # Project type filter
                selected_types = self._add_project_type_filter(col2)
                if selected_types:
                    filtered_df = filtered_df[
                        filtered_df[self.config['project_type_column']].isin(selected_types)
                    ]
                    active_filters.append(f"Project Types: {len(selected_types)} selected")
                
                # Procurement method filter
                selected_methods = self._add_procurement_method_filter(col2)
                if selected_methods:
                    filtered_df = filtered_df[
                        filtered_df[self.config['procurement_method_column']].isin(selected_methods)
                    ]
                    active_filters.append(f"Procurement Methods: {len(selected_methods)} selected")
            
            with col3:
                # Company filter
                selected_companies = self._add_company_filter(col3)
                if selected_companies:
                    filtered_df = filtered_df[
                        filtered_df[self.config['company_column']].isin(selected_companies)
                    ]
                    active_filters.append(f"Companies: {len(selected_companies)} selected")
                
                # Date range filter
                date_range = self._add_date_filter(col3)
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
                    if st.button("🔄 Clear Filters", 
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