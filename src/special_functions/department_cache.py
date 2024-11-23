import os
import json
from typing import List, Optional
from pymongo import MongoClient
import streamlit as st
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

CACHE_DIR = "./dept_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def get_departments() -> List[str]:
    """
    Retrieve departments, using file-based persistent caching
    """
    mongo_uri = os.environ.get('MONGO_URI')
    cache_file = os.path.join(CACHE_DIR, "departments.json")
    
    # Check if cached file exists
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading department cache: {e}")
    
    # If no cache, fetch from MongoDB
    try:
        client = MongoClient(mongo_uri)
        db = client["projects"]
        collection = db["projects"]
        
        unique_depts = sorted(collection.distinct("dept_name"))
        client.close()
        
        # Write to cache file
        with open(cache_file, 'w') as f:
            json.dump(unique_depts, f)
        
        logger.info(f"Cached {len(unique_depts)} departments")
        return unique_depts
    
    except Exception as e:
        logger.error(f"Error retrieving departments: {e}")
        return []

def get_sub_department(dept_name: Optional[str] = None) -> List[str]:
    """
    Retrieve sub-departments with file-based persistent caching
    """
    # Generate a unique filename based on department (or use 'all' if no specific dept)
    cache_filename = f"sub_departments_{dept_name or 'all'}.json"
    cache_file = os.path.join(CACHE_DIR, cache_filename)
    
    # Check if cached file exists
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading sub-department cache: {e}")
    
    # If no cache, fetch from MongoDB
    try:
        mongo_uri = "mongodb://root:Password1@dds-gs5de2b9f9cba8b41646-pub.mongodb.singapore.rds.aliyuncs.com:3717,dds-gs5de2b9f9cba8b42352-pub.mongodb.singapore.rds.aliyuncs.com:3717/admin?replicaSet=mgset-311013160"
        client = MongoClient(mongo_uri)
        db = client["projects"]
        collection = db["projects"]
        
        # Prepare query
        query = {}
        if dept_name:
            query["dept_name"] = dept_name
        
        unique_sub_depts = sorted(collection.distinct("dept_sub_name", query))
        client.close()
        
        # Write to cache file
        with open(cache_file, 'w') as f:
            json.dump(unique_sub_depts, f)
        
        logger.info(f"Cached {len(unique_sub_depts)} sub-departments for {dept_name or 'all'}")
        return unique_sub_depts
    
    except Exception as e:
        logger.error(f"Error retrieving sub-departments: {e}")
        return []

def render_sidebar_filters():
    """Render sidebar filters and return filter values"""
    # Initialize filters
    filters = {
        'dept_name': st.session_state.get('dept_name', ''),
        'dept_sub_name': st.session_state.get('dept_sub_name', ''),
        'date_start': st.session_state.get('date_start', datetime(2022, 1, 1).date()),
        'date_end': st.session_state.get('date_end', datetime(2023, 12, 31).date()),
        'price_start': st.session_state.get('price_start', 0.0),
        'price_end': st.session_state.get('price_end', 200.0)
    }
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    unique_depts = get_departments()
    logger.info(f"Found {len(unique_depts)} unique departments")

    # Department filter - using session state
    dept_options = [""] + unique_depts
    filters['dept_name'] = st.sidebar.selectbox(
        "Department",
        options=dept_options,
        key="dept_name"  # This maintains state across pages
    )

    # Sub-department filter - using session state
    if filters['dept_name']:
        unique_sub_depts = get_sub_department(filters['dept_name'])
        logger.info(f"Found {len(unique_sub_depts)} sub-departments")
        
        sub_dept_options = [""] + unique_sub_depts
        filters['dept_sub_name'] = st.sidebar.selectbox(
            "Sub-Department",
            options=sub_dept_options,
            key="dept_sub_name"  # This maintains state across pages
        )
            
    # Date filters - using session state
    filters['date_start'] = st.sidebar.date_input(
        "Start Date",
        value=filters['date_start'],
        key="date_start"  # This maintains state across pages
    )
    filters['date_end'] = st.sidebar.date_input(
        "End Date",
        value=filters['date_end'],
        key="date_end"  # This maintains state across pages
    )
    
    # Price range filter with numeric inputs and default values
    st.sidebar.subheader("Price Range (Million Baht)")
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        filters['price_start'] = st.number_input(
            "From", 
            min_value=0.0,
            max_value=10000.0,
            value=0.0,
            step=10.0,
            format="%.1f",
            key="price_start"  # This maintains state across pages
        )
            
    with col2:
        filters['price_end'] = st.number_input(
            "To",
            min_value=0.0,
            max_value=20000.0,
            value=200.0,
            step=10.0,
            format="%.1f",
            key="price_end"  # This maintains state across pages
        )
    
    return filters