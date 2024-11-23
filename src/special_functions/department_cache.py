import os
import json
from typing import List, Optional
from pymongo import MongoClient
import streamlit as st
import logging

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
    
    Args:
        mongo_uri: MongoDB connection string
        dept_name: Optional department to filter sub-departments
    
    Returns:
        List of unique sub-department names
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