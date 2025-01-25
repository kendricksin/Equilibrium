# src/utils/url_params.py

import streamlit as st
from urllib.parse import urlencode
from typing import Dict, Any

class URLParamsHandler:
    """Handles URL parameters for filtering and sharing"""
    
    @staticmethod
    def get_query_params() -> Dict[str, Any]:
        """Get current query parameters from URL"""
        query_params = st.query_params
        params = {}
        
        # Handle department parameters
        if 'dept' in query_params:
            params['departments'] = query_params['dept'].split(',')
            
        if 'subdept' in query_params:
            params['subdepartments'] = query_params['subdept'].split(',')
            
        # Handle date parameters
        if 'date_start' in query_params:
            params['date_start'] = query_params['date_start']
        if 'date_end' in query_params:
            params['date_end'] = query_params['date_end']
            
        # Handle price parameters
        if 'price_min' in query_params:
            try:
                params['price_start'] = float(query_params['price_min'])
            except (ValueError, TypeError):
                pass
        if 'price_max' in query_params:
            try:
                params['price_end'] = float(query_params['price_max'])
            except (ValueError, TypeError):
                pass
            
        # Handle procurement method
        if 'proc_method' in query_params:
            params['procurement_methods'] = query_params['proc_method'].split(',')
            
        # Handle project type
        if 'proj_type' in query_params:
            params['project_types'] = query_params['proj_type'].split(',')
        
        return params
    
    @staticmethod
    def update_query_params(params: Dict[str, Any]):
        """Update URL query parameters"""
        query_params = {}
        
        # Update department parameters
        if 'departments' in params and params['departments']:
            query_params['dept'] = ','.join(params['departments'])
            
        if 'subdepartments' in params and params['subdepartments']:
            query_params['subdept'] = ','.join(params['subdepartments'])
        
        # Update date parameters
        if 'date_start' in params:
            query_params['date_start'] = params['date_start']
        if 'date_end' in params:
            query_params['date_end'] = params['date_end']
            
        # Update price parameters
        if 'price_start' in params:
            query_params['price_min'] = str(params['price_start'])
        if 'price_end' in params:
            query_params['price_max'] = str(params['price_end'])
            
        # Update procurement method
        if 'procurement_methods' in params and params['procurement_methods']:
            query_params['proc_method'] = ','.join(params['procurement_methods'])
            
        # Update project type
        if 'project_types' in params and params['project_types']:
            query_params['proj_type'] = ','.join(params['project_types'])
        
        # Update Streamlit's query parameters
        st.query_params.update(query_params)
    
    @staticmethod
    def clear_query_params():
        """Clear all query parameters"""
        st.query_params.clear()
    
    @staticmethod
    def get_shareable_link() -> str:
        """Generate shareable query parameter string"""
        params = dict(st.query_params)
        return urlencode(params, doseq=True)