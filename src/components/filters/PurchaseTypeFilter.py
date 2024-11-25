# src/components/filters/PurchaseTypeFilter.py

import streamlit as st
from typing import Tuple, Optional, List

def PurchaseTypeFilter(
    purchase_methods: List[str],
    project_types: List[str],
    current_method: Optional[str] = None,
    current_type: Optional[str] = None,
    key_prefix: str = ""
) -> Tuple[str, str]:
    """
    A component for purchase method and project type selection.
    
    Args:
        purchase_methods (List[str]): List of available purchase methods
        project_types (List[str]): List of available project types
        current_method (Optional[str]): Currently selected purchase method
        current_type (Optional[str]): Currently selected project type
        key_prefix (str): Prefix for component keys to avoid conflicts
        
    Returns:
        Tuple[str, str]: Selected purchase method and project type
    """
    # Purchase method selection
    method_options = [""] + purchase_methods
    current_method_index = method_options.index(current_method) if current_method in method_options else 0
    
    selected_method = st.selectbox(
        "Purchase Method",
        options=method_options,
        index=current_method_index,
        key=f"{key_prefix}purchase_method"
    )
    
    # Project type selection
    type_options = [""] + project_types
    current_type_index = type_options.index(current_type) if current_type in type_options else 0
    
    selected_type = st.selectbox(
        "Project Type",
        options=type_options,
        index=current_type_index,
        key=f"{key_prefix}project_type"
    )
    
    return selected_method, selected_type