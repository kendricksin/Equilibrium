# src/components/filters/TableFilter.py

import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import numpy as np

class TableFilter:
    """Enhanced table filter utility for project data with smart defaults and quick selectors"""
    
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

    DATE_RANGES = {
        "3 Months": pd.DateOffset(months=3),
        "6 Months": pd.DateOffset(months=6),
        "1 Year": pd.DateOffset(years=1),
        "3 Years": pd.DateOffset(years=3),
        "All Time": None
    }
    
    def __init__(
        self,
        df: pd.DataFrame,
        key_prefix: str = "",
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize TableFilter with DataFrame and configuration"""
        self.df = df
        self.key_prefix = key_prefix
        self.config = self._validate_config(config or {})
    
    def _validate_config(self, user_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge and validate user config with defaults"""
        config = self.DEFAULT_CONFIG.copy()
        config.update(user_config)
        return config
    
    def _format_display_option(self, name: str, count: int) -> str:
        """Format display option with count"""
        return f"{name} ({count:,} projects)"
    
    def _add_value_filter(self, col) -> Optional[Tuple[float, float]]:
        """Add value range filter"""
        if not self.config['show_value_filter']:
            return None
            
        value_col = self.config['value_column']
        if value_col not in self.df.columns:
            return None
            
        min_value = float(self.df[value_col].min()) / self.config['value_unit']
        max_value = float(self.df[value_col].max()) / self.config['value_unit'] + 0.01
        
        col.markdown(f"**Value Range ({self.config['value_label']})**")
        value_range = col.slider(
            "Project Value",
            min_value=min_value,
            max_value=max_value,
            value=(min_value, max_value),
            key=f"{self.key_prefix}value_range"
        )
        
        return value_range
    
    def _add_date_filter(self, col) -> Optional[Tuple[datetime.date, datetime.date]]:
        """Add date range filter with quick selectors"""
        if not self.config['show_date_filter']:
            return None
            
        date_col = self.config['date_column']
        if date_col not in self.df.columns:
            return None
            
        min_date = self.df[date_col].min()
        max_date = self.df[date_col].max()
        
        # Calculate default dates
        default_start = max(min_date, max_date - pd.DateOffset(years=3))
        
        # Quick range selector
        col.markdown("**Date Range**")
        selected_range = col.selectbox(
            "Quick Select",
            options=list(self.DATE_RANGES.keys()),
            index=3,  # Default to 3 Years
            key=f"{self.key_prefix}quick_date_range"
        )
        
        # Update dates based on quick selection
        if selected_range in self.DATE_RANGES:
            if self.DATE_RANGES[selected_range] is None:
                start_value = min_date
            else:
                start_value = max(min_date, max_date - self.DATE_RANGES[selected_range])
        else:
            start_value = default_start
        
        # Date inputs
        start_date = col.date_input(
            "Start Date",
            value=start_value,
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
    
    def _add_company_filter(self, col) -> Optional[List[str]]:
        """Add company filter"""
        if not self.config['show_company_filter']:
            return None
            
        company_col = self.config['company_column']
        if company_col not in self.df.columns:
            return None
        
        # Get company counts and sort by frequency
        company_counts = self.df[company_col].value_counts()
        company_options = {
            self._format_display_option(company, count): company
            for company, count in company_counts.items()
        }
        
        col.markdown("**Company Filter**")
        selected_labels = col.multiselect(
            "Select Companies",
            options=list(company_options.keys()),
            key=f"{self.key_prefix}companies"
        )
        
        return [company_options[label] for label in selected_labels]
    
    def _add_department_filters(self, col) -> Tuple[Optional[List[str]], Optional[List[str]]]:
        """Add department and sub-department filters"""
        if not self.config['show_department_filter']:
            return None, None
            
        dept_col = self.config['department_column']
        subdept_col = self.config['subdepartment_column']
        
        if dept_col not in self.df.columns:
            return None, None
        
        # Department filter
        dept_counts = self.df[dept_col].value_counts()
        dept_options = {
            self._format_display_option(dept, count): dept
            for dept, count in dept_counts.items()
        }
        
        col.markdown("**Department Filters**")
        selected_dept_labels = col.multiselect(
            "Select Departments",
            options=list(dept_options.keys()),
            key=f"{self.key_prefix}departments"
        )
        
        selected_depts = [dept_options[label] for label in selected_dept_labels]
        
        # Sub-department filter (only if departments are selected)
        selected_subdepts = []
        if selected_depts:
            subdept_df = self.df[self.df[dept_col].isin(selected_depts)]
            subdept_counts = subdept_df[subdept_col].value_counts()
            
            subdept_options = {
                self._format_display_option(subdept, count): subdept
                for subdept, count in subdept_counts.items()
                if pd.notna(subdept)
            }
            
            if subdept_options:
                selected_subdept_labels = col.multiselect(
                    "Select Sub-departments",
                    options=list(subdept_options.keys()),
                    key=f"{self.key_prefix}subdepartments"
                )
                selected_subdepts = [subdept_options[label] for label in selected_subdept_labels]
        
        return selected_depts, selected_subdepts
    
    def _add_project_type_filter(self, col) -> Optional[List[str]]:
        """Add project type filter"""
        if not self.config['show_type_filter']:
            return None
            
        type_col = self.config['project_type_column']
        if type_col not in self.df.columns:
            return None
        
        # Get type counts
        type_counts = self.df[type_col].value_counts()
        type_options = {
            self._format_display_option(ptype, count): ptype
            for ptype, count in type_counts.items()
            if pd.notna(ptype)
        }
        
        col.markdown("**Project Type Filter**")
        selected_labels = col.multiselect(
            "Select Project Types",
            options=list(type_options.keys()),
            key=f"{self.key_prefix}project_types"
        )
        
        return [type_options[label] for label in selected_labels]
    
    def _add_procurement_method_filter(self, col) -> Optional[List[str]]:
        """Add procurement method filter with default e-bidding selection"""
        if not self.config['show_procurement_filter']:
            return None
            
        method_col = self.config['procurement_method_column']
        if method_col not in self.df.columns:
            return None
        
        # Get method counts
        method_counts = self.df[method_col].value_counts()
        method_options = {
            self._format_display_option(method, count): method
            for method, count in method_counts.items()
            if pd.notna(method)
        }
        
        col.markdown("**Procurement Method Filter**")
        
        # Find e-bidding option if it exists
        ebidding_key = next(
            (key for key in method_options.keys() 
             if "e-bidding" in key.lower() or "ประกวดราคาอิเล็กทรอนิกส์" in key),
            None
        )
        
        # Set default selection
        if f"{self.key_prefix}procurement_methods" not in st.session_state:
            if ebidding_key:
                st.session_state[f"{self.key_prefix}procurement_methods"] = [ebidding_key]
            elif method_options:
                st.session_state[f"{self.key_prefix}procurement_methods"] = [list(method_options.keys())[0]]
        
        selected_labels = col.multiselect(
            "Select Procurement Methods",
            options=list(method_options.keys()),
            key=f"{self.key_prefix}procurement_methods"
        )
        
        return [method_options[label] for label in selected_labels]
    
    def filter_dataframe(self) -> pd.DataFrame:
        """Apply all filters to the DataFrame"""
        st.markdown("### 🎯 Refine Results")
        
        with st.expander("Advanced Filters", expanded=self.config['expander_default']):
            filtered_df = self.df.copy()
            active_filters = []
            
            # Create three columns for filter layout
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
                
                # Department filters
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