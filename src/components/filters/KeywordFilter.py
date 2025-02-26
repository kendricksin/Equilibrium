# src/components/filters/KeywordFilter.py

import streamlit as st
from typing import List, Tuple, Dict
import re

def KeywordFilter(
    current_include_all: List[str] = None,
    current_include_any: List[str] = None,
    current_exclude: List[str] = None,
    key_prefix: str = ""
) -> Tuple[List[str], List[str], List[str]]:
    """
    Enhanced component for keyword-based search with include-all/include-any/exclude functionality.
    
    Args:
        current_include_all (List[str]): Currently included keywords (must have all)
        current_include_any (List[str]): Currently included keywords (must have any)
        current_exclude (List[str]): Currently excluded keywords
        key_prefix (str): Prefix for component keys
        
    Returns:
        Tuple[List[str], List[str], List[str]]: Lists of included-all, included-any, and excluded keywords
    """
    if current_include_all is None:
        current_include_all = []
    if current_include_any is None:
        current_include_any = []
    if current_exclude is None:
        current_exclude = []
        
    st.markdown("### 🔍 Keyword Search")
    
    # Include ALL keywords
    include_all_input = st.text_area(
        "Must include ALL these keywords (one per line)",
        value="\n".join(current_include_all),
        height=80,
        help="Enter keywords that MUST ALL be present. Projects must contain ALL these keywords.",
        key=f"{key_prefix}include_all_keywords"
    )
    
    # Include ANY keywords
    include_any_input = st.text_area(
        "Must include ANY of these keywords (one per line)",
        value="\n".join(current_include_any),
        height=80,
        help="Enter keywords where at least ONE must be present. Projects must contain AT LEAST ONE of these keywords.",
        key=f"{key_prefix}include_any_keywords"
    )
    
    # Exclude keywords
    exclude_input = st.text_area(
        "Exclude keywords (one per line)",
        value="\n".join(current_exclude),
        height=80,
        help="Enter keywords to exclude. Projects containing ANY of these keywords will be excluded.",
        key=f"{key_prefix}exclude_keywords"
    )
    
    # Process inputs
    include_all_keywords = [
        keyword.strip() 
        for keyword in include_all_input.split("\n") 
        if keyword.strip()
    ]
    
    include_any_keywords = [
        keyword.strip() 
        for keyword in include_any_input.split("\n") 
        if keyword.strip()
    ]
    
    exclude_keywords = [
        keyword.strip() 
        for keyword in exclude_input.split("\n") 
        if keyword.strip()
    ]
    
    return include_all_keywords, include_any_keywords, exclude_keywords

def build_keyword_query(include_all_keywords: List[str], include_any_keywords: List[str], exclude_keywords: List[str]) -> Dict:
    """
    Build MongoDB query for keyword search with include-all/include-any/exclude functionality
    
    Args:
        include_all_keywords (List[str]): Keywords that must ALL be present
        include_any_keywords (List[str]): Keywords where at least one must be present
        exclude_keywords (List[str]): Keywords to exclude
        
    Returns:
        Dict: MongoDB query
    """
    query = {}
    conditions = []
    
    # Build include ALL conditions
    if include_all_keywords:
        for keyword in include_all_keywords:
            pattern = re.compile(f".*{re.escape(keyword)}.*", re.IGNORECASE)
            conditions.append({
                "$or": [
                    {"project_name": pattern},
                    {"project_detail": pattern},
                    {"winner": pattern}
                ]
            })
    
    # Build include ANY conditions
    if include_any_keywords:
        any_conditions = []
        for keyword in include_any_keywords:
            pattern = re.compile(f".*{re.escape(keyword)}.*", re.IGNORECASE)
            any_conditions.append({
                "$or": [
                    {"project_name": pattern},
                    {"project_detail": pattern},
                    {"winner": pattern}
                ]
            })
        
        if any_conditions:
            conditions.append({"$or": any_conditions})
    
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