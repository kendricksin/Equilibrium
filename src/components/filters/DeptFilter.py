# src/components/filters/DeptFilter.py

import streamlit as st
from typing import Tuple, Optional, List

def DepartmentFilter(
    departments: List[str],
    current_dept: Optional[str] = None,
    current_sub_dept: Optional[str] = None,
    get_sub_departments_fn: Optional[callable] = None,
    key_prefix: str = ""
) -> Tuple[str, str]:
    """
    A component for department and sub-department selection.
    
    Args:
        departments (List[str]): List of available departments
        current_dept (Optional[str]): Currently selected department
        current_sub_dept (Optional[str]): Currently selected sub-department
        get_sub_departments_fn (Optional[callable]): Function to fetch sub-departments
        key_prefix (str): Prefix for component keys to avoid conflicts
        
    Returns:
        Tuple[str, str]: Selected department and sub-department
    """
    # Add empty option to departments
    dept_options = [""] + departments
    current_dept_index = dept_options.index(current_dept) if current_dept in dept_options else 0
    
    # Department selection
    selected_dept = st.selectbox(
        "Department",
        options=dept_options,
        index=current_dept_index,
        key=f"{key_prefix}department"
    )
    
    # Sub-department selection
    selected_sub_dept = ""
    if selected_dept and get_sub_departments_fn:
        sub_departments = [""] + get_sub_departments_fn(selected_dept)
        current_sub_dept_index = (
            sub_departments.index(current_sub_dept)
            if current_sub_dept in sub_departments
            else 0
        )
        
        selected_sub_dept = st.selectbox(
            "Sub-Department",
            options=sub_departments,
            index=current_sub_dept_index,
            key=f"{key_prefix}sub_department"
        )
    
    return selected_dept, selected_sub_dept