# src/components/filters/AdvancedFilters.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)

class AdvancedFilters:
    """Enhanced filter component for in-memory filtering of DataFrame search results"""
    
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
        
        # Convert date columns to datetime if needed
        if 'transaction_date' in self.data.columns:
            if not pd.api.types.is_datetime64_any_dtype(self.data['transaction_date']):
                self.data['transaction_date'] = pd.to_datetime(self.data['transaction_date'])
        
        # Get date range from data
        self.min_date = self.data['transaction_date'].min().date() if not self.data.empty else datetime.now().date()
        self.max_date = self.data['transaction_date'].max().date() if not self.data.empty else datetime.now().date()
        
        # Get unique values from data
        self.unique_companies = sorted(self.data['winner'].unique()) if 'winner' in self.data.columns else []
        self.unique_departments = sorted(self.data['dept_name'].unique()) if 'dept_name' in self.data.columns else []
        self.unique_subdepartments = sorted(self.data['dept_sub_name'].unique()) if 'dept_sub_name' in self.data.columns else []
        self.unique_project_types = sorted(self.data['project_type_name'].unique()) if 'project_type_name' in self.data.columns else []
        self.unique_procurement_methods = sorted(self.data['purchase_method_name'].unique()) if 'purchase_method_name' in self.data.columns else []
        self.unique_provinces = sorted(self.data['province'].unique()) if 'province' in self.data.columns else []
            
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
            'companies': [],
            'provinces': []  # Added provinces field
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
            'show_provinces': True,  # Added province filter option
            'max_selections': 10,
            'value_column': 'sum_price_agree',
            'value_unit': 1e6  # Convert to millions
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
            if self.config['show_value_range'] and self.config['value_column'] in self.data.columns:
                with col1:
                    st.write("Value Range (Million Baht)")
                    range_option = st.selectbox(
                        "Quick Select",
                        options=[r['label'] for r in self.VALUE_RANGES],
                        index=[r['label'] for r in self.VALUE_RANGES].index(filters['value_range']),
                        key=f"{self.key_prefix}_value_range"
                    )
                    
                    # Update min/max based on selection
                    selected_range = next(r for r in self.VALUE_RANGES if r['label'] == range_option)
                    filters['value_min'] = selected_range['min']
                    filters['value_max'] = selected_range['max']
                    filters['value_range'] = range_option
                    
                    # Custom range slider
                    min_val = float(self.data[self.config['value_column']].min()) / self.config['value_unit']
                    max_val = float(self.data[self.config['value_column']].max()) / self.config['value_unit']
                    
                    # Only show slider if 'All Values' is selected
                    if range_option == 'All Values':
                        custom_range = st.slider(
                            "Custom Range (Million Baht)",
                            min_value=min_val,
                            max_value=max_val+0.001,
                            value=(min_val, max_val),
                            key=f"{self.key_prefix}_custom_value_range"
                        )
                        filters['value_min'] = custom_range[0]
                        filters['value_max'] = custom_range[1]
            
            # Date Range Filter
            if self.config['show_date_range'] and 'transaction_date' in self.data.columns:
                with col2:
                    st.write("Date Range")
                    date_option = st.selectbox(
                        "Quick Select",
                        options=[r['label'] for r in self.DATE_RANGES],
                        index=[r['label'] for r in self.DATE_RANGES].index(filters['date_range']),
                        key=f"{self.key_prefix}_date_range"
                    )
                    
                    # Update date range based on selection
                    selected_date_range = next(r for r in self.DATE_RANGES if r['label'] == date_option)
                    if selected_date_range['days'] is None:
                        filters['date_start'] = self.min_date
                        filters['date_end'] = self.max_date
                    else:
                        filters['date_end'] = self.max_date
                        filters['date_start'] = self.max_date - timedelta(days=selected_date_range['days'])
                    filters['date_range'] = date_option
                    
                    # Custom date input
                    if date_option == 'All Time':
                        start_date = st.date_input(
                            "Start Date",
                            value=filters['date_start'],
                            min_value=self.min_date,
                            max_value=self.max_date,
                            key=f"{self.key_prefix}_custom_start_date"
                        )
                        
                        end_date = st.date_input(
                            "End Date",
                            value=filters['date_end'],
                            min_value=start_date,
                            max_value=self.max_date,
                            key=f"{self.key_prefix}_custom_end_date"
                        )
                        
                        filters['date_start'] = start_date
                        filters['date_end'] = end_date
            
            col3, col4 = st.columns(2)
            
            # Department Filter
            if self.config['show_departments'] and 'dept_name' in self.data.columns:
                with col3:
                    filters['departments'] = st.multiselect(
                        "Select Departments",
                        options=self.unique_departments,
                        default=filters['departments'],
                        key=f"{self.key_prefix}_departments"
                    )
            
            # Subdepartment Filter
            if self.config['show_subdepartments'] and 'dept_sub_name' in self.data.columns:
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
            if self.config['show_project_types'] and 'project_type_name' in self.data.columns:
                with col5:
                    filters['project_types'] = st.multiselect(
                        "Select Project Types",
                        options=self.unique_project_types,
                        default=filters['project_types'],
                        key=f"{self.key_prefix}_project_types"
                    )
            
            # Procurement Method Filter
            if self.config['show_procurement_methods'] and 'purchase_method_name' in self.data.columns:
                with col6:
                    filters['procurement_methods'] = st.multiselect(
                        "Select Procurement Methods",
                        options=self.unique_procurement_methods,
                        default=filters['procurement_methods'],
                        key=f"{self.key_prefix}_procurement_methods"
                    )
            
            # Company Filter
            if self.config['show_companies'] and 'winner' in self.data.columns:
                filters['companies'] = st.multiselect(
                    "Select Companies",
                    options=self.unique_companies,
                    default=filters['companies'],
                    key=f"{self.key_prefix}_companies"
                )
                
            # Province Filter
            if self.config['show_provinces'] and 'province' in self.data.columns:
                # Add a new row for province filter
                filters['provinces'] = st.multiselect(
                    "Select Provinces",
                    options=self.unique_provinces,
                    default=filters['provinces'],
                    key=f"{self.key_prefix}_provinces",
                    help="Select one or more provinces to filter projects by location"
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
                        'companies': [],
                        'provinces': []
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
    
    def apply_filters(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Apply filters to the DataFrame
        
        Returns:
            Tuple of (filtered DataFrame, filter summary)
        """
        # Get current filter state
        filters = st.session_state[f"{self.key_prefix}_advanced_filters"]
        filtered_df = self.data.copy()
        
        # Track active filters for summary
        active_filters = {}
        
        # Apply value range filter
        if self.config['show_value_range'] and self.config['value_column'] in filtered_df.columns:
            value_min = filters['value_min']
            value_max = filters['value_max']
            
            if value_min is not None:
                filtered_df = filtered_df[
                    filtered_df[self.config['value_column']] >= value_min * self.config['value_unit']
                ]
                active_filters['value_min'] = value_min
            
            if value_max is not None:
                filtered_df = filtered_df[
                    filtered_df[self.config['value_column']] <= value_max * self.config['value_unit']
                ]
                active_filters['value_max'] = value_max
        
        # Apply date range filter
        if self.config['show_date_range'] and 'transaction_date' in filtered_df.columns:
            date_start = filters['date_start']
            date_end = filters['date_end']
            
            if date_start and date_end:
                # Convert dates to datetime for filtering
                start_datetime = pd.Timestamp(date_start)
                end_datetime = pd.Timestamp(date_end) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
                
                filtered_df = filtered_df[
                    (filtered_df['transaction_date'] >= start_datetime) &
                    (filtered_df['transaction_date'] <= end_datetime)
                ]
                
                active_filters['date_start'] = date_start
                active_filters['date_end'] = date_end
        
        # Apply department filter
        if self.config['show_departments'] and filters['departments'] and 'dept_name' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['dept_name'].isin(filters['departments'])]
            active_filters['departments'] = filters['departments']
        
        # Apply subdepartment filter
        if self.config['show_subdepartments'] and filters['subdepartments'] and 'dept_sub_name' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['dept_sub_name'].isin(filters['subdepartments'])]
            active_filters['subdepartments'] = filters['subdepartments']
        
        # Apply project type filter
        if self.config['show_project_types'] and filters['project_types'] and 'project_type_name' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['project_type_name'].isin(filters['project_types'])]
            active_filters['project_types'] = filters['project_types']
        
        # Apply procurement method filter
        if self.config['show_procurement_methods'] and filters['procurement_methods'] and 'purchase_method_name' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['purchase_method_name'].isin(filters['procurement_methods'])]
            active_filters['procurement_methods'] = filters['procurement_methods']
        
        # Apply company filter
        if self.config['show_companies'] and filters['companies'] and 'winner' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['winner'].isin(filters['companies'])]
            active_filters['companies'] = filters['companies']
        
        return filtered_df, active_filters
    
    def get_filter_summary(self, active_filters: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of active filters
        
        Args:
            active_filters: Dictionary of active filters
            
        Returns:
            String summary of active filters
        """
        summary_parts = []
        
        # Value range
        if 'value_min' in active_filters or 'value_max' in active_filters:
            min_val = active_filters.get('value_min', 0)
            max_val = active_filters.get('value_max', '∞')
            value_text = f"Value: {min_val} - {max_val}M฿"
            summary_parts.append(value_text)
        
        # Date range
        if 'date_start' in active_filters and 'date_end' in active_filters:
            date_text = f"Date: {active_filters['date_start'].strftime('%Y-%m-%d')} to {active_filters['date_end'].strftime('%Y-%m-%d')}"
            summary_parts.append(date_text)
        
        # Departments
        if 'departments' in active_filters and active_filters['departments']:
            if len(active_filters['departments']) <= 2:
                dept_text = f"Departments: {', '.join(active_filters['departments'])}"
            else:
                dept_text = f"Departments: {len(active_filters['departments'])} selected"
            summary_parts.append(dept_text)
        
        # Subdepartments
        if 'subdepartments' in active_filters and active_filters['subdepartments']:
            if len(active_filters['subdepartments']) <= 2:
                subdept_text = f"Subdepartments: {', '.join(active_filters['subdepartments'])}"
            else:
                subdept_text = f"Subdepartments: {len(active_filters['subdepartments'])} selected"
            summary_parts.append(subdept_text)
        
        # Project types
        if 'project_types' in active_filters and active_filters['project_types']:
            if len(active_filters['project_types']) <= 2:
                type_text = f"Types: {', '.join(active_filters['project_types'])}"
            else:
                type_text = f"Types: {len(active_filters['project_types'])} selected"
            summary_parts.append(type_text)
        
        # Procurement methods
        if 'procurement_methods' in active_filters and active_filters['procurement_methods']:
            if len(active_filters['procurement_methods']) <= 2:
                method_text = f"Methods: {', '.join(active_filters['procurement_methods'])}"
            else:
                method_text = f"Methods: {len(active_filters['procurement_methods'])} selected"
            summary_parts.append(method_text)
        
        # Companies
        if 'companies' in active_filters and active_filters['companies']:
            if len(active_filters['companies']) <= 2:
                company_text = f"Companies: {', '.join(active_filters['companies'])}"
            else:
                company_text = f"Companies: {len(active_filters['companies'])} selected"
            summary_parts.append(company_text)
            
        # Provinces
        if 'provinces' in active_filters and active_filters['provinces']:
            if len(active_filters['provinces']) <= 2:
                province_text = f"Provinces: {', '.join(active_filters['provinces'])}"
            else:
                province_text = f"Provinces: {len(active_filters['provinces'])} selected"
            summary_parts.append(province_text)
        
        if summary_parts:
            return " | ".join(summary_parts)
        else:
            return "No filters applied"

def filter_projects(
    df: pd.DataFrame,
    key_prefix: str = "",
    config: Optional[Dict[str, Any]] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Convenience function to filter a DataFrame of projects
    
    Args:
        df: DataFrame to filter
        key_prefix: Prefix for session state keys
        config: Optional configuration dictionary
        
    Returns:
        Tuple of (filtered DataFrame, filter summary)
    """
    # Initialize filter component
    filter_component = AdvancedFilters(df, key_prefix, config)
    
    # Render filters
    filter_component.render()
    
    # Apply filters to the DataFrame
    filtered_df, active_filters = filter_component.apply_filters()
    
    # Get filter summary
    filter_summary = filter_component.get_filter_summary(active_filters)
    
    # Display filter summary if filters are active
    if filter_summary != "No filters applied":
        st.markdown(f"**Active Filters:** {filter_summary}")
        
        # Show filter stats
        st.markdown(f"**Filtered {len(filtered_df):,} out of {len(df):,} projects**")
        
        # Add reset button
        if st.button("🔄 Reset All Filters", key=f"{key_prefix}_reset_all"):
            st.session_state[f"{key_prefix}_advanced_filters"] = {
                'value_min': None,
                'value_max': None,
                'value_range': 'All Values',
                'date_start': filter_component.min_date,
                'date_end': filter_component.max_date,
                'date_range': 'All Time',
                'departments': [],
                'subdepartments': [],
                'project_types': [],
                'procurement_methods': [],
                'companies': []
            }
            st.rerun()
    
    return filtered_df, filter_summary