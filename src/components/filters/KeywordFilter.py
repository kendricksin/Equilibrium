# src/components/filters/KeywordFilter.py

import streamlit as st
from typing import List, Tuple, Dict
import re

def KeywordFilter(
    current_include: List[str] = None,
    current_exclude: List[str] = None,
    key_prefix: str = ""
) -> Tuple[List[str], List[str]]:
    """
    A component for keyword-based search with include/exclude functionality.
    
    Args:
        current_include (List[str]): Currently included keywords
        current_exclude (List[str]): Currently excluded keywords
        key_prefix (str): Prefix for component keys
        
    Returns:
        Tuple[List[str], List[str]]: Lists of included and excluded keywords
    """
    if current_include is None:
        current_include = []
    if current_exclude is None:
        current_exclude = []
        
    st.markdown("### 🔍 Keyword Search")
    
    # Include keywords
    include_input = st.text_area(
        "Include keywords (one per line)",
        value="\n".join(current_include),
        height=100,
        help="Enter keywords to search for, one per line. Projects must contain ALL these keywords.",
        key=f"{key_prefix}include_keywords"
    )
    
    # Exclude keywords
    exclude_input = st.text_area(
        "Exclude keywords (one per line)",
        value="\n".join(current_exclude),
        height=100,
        help="Enter keywords to exclude, one per line. Projects containing ANY of these keywords will be excluded.",
        key=f"{key_prefix}exclude_keywords"
    )
    
    # Process inputs
    include_keywords = [
        keyword.strip() 
        for keyword in include_input.split("\n") 
        if keyword.strip()
    ]
    
    exclude_keywords = [
        keyword.strip() 
        for keyword in exclude_input.split("\n") 
        if keyword.strip()
    ]
    
    return include_keywords, exclude_keywords

def build_keyword_query(include_keywords: List[str], exclude_keywords: List[str]) -> Dict:
    """
    Build MongoDB query for keyword search
    
    Args:
        include_keywords (List[str]): Keywords to include
        exclude_keywords (List[str]): Keywords to exclude
        
    Returns:
        Dict: MongoDB query
    """
    query = {}
    conditions = []
    
    # Build include conditions
    if include_keywords:
        for keyword in include_keywords:
            pattern = re.compile(f".*{re.escape(keyword)}.*", re.IGNORECASE)
            conditions.append({
                "$or": [
                    {"project_name": pattern},
                    {"project_detail": pattern},
                    {"winner": pattern}
                ]
            })
    
    # Build exclude conditions
    if exclude_keywords:
        exclude_patterns = [
            re.compile(f".*{re.escape(keyword)}.*", re.IGNORECASE)
            for keyword in exclude_keywords
        ]
        conditions.append({
            "$nor": [
                {
                    "$or": [
                        {"project_name": pattern},
                        {"project_detail": pattern},
                        {"winner": pattern}
                    ]
                }
                for pattern in exclude_patterns
            ]
        })
    
    # Combine conditions
    if conditions:
        query["$and"] = conditions
        
    return query