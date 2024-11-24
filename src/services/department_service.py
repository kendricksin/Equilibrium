# src/services/department_service.py

import logging
from typing import List
from services.database.mongodb import MongoDBService
from services.cache.cache_manager import CacheManager

logger = logging.getLogger(__name__)
cache = CacheManager()

def get_departments() -> List[str]:
    """Get unique departments with caching"""
    cache_key = "departments"
    cached_depts = cache.get(cache_key)
    
    if cached_depts is not None:
        return cached_depts
    
    try:
        with MongoDBService() as db:
            departments = db.get_departments()
            cache.set(cache_key, departments, ttl=3600)  # Cache for 1 hour
            return departments
    except Exception as e:
        logger.error(f"Error fetching departments: {e}")
        return []

def get_sub_departments(dept_name: str) -> List[str]:
    """Get sub-departments for a given department with caching"""
    cache_key = f"sub_departments_{dept_name}"
    cached_sub_depts = cache.get(cache_key)
    
    if cached_sub_depts is not None:
        return cached_sub_depts
    
    try:
        with MongoDBService() as db:
            sub_departments = db.get_sub_departments(dept_name)
            cache.set(cache_key, sub_departments, ttl=3600)  # Cache for 1 hour
            return sub_departments
    except Exception as e:
        logger.error(f"Error fetching sub-departments: {e}")
        return []