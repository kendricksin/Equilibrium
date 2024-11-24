# src/services/cache/department_cache.py

import logging
from typing import List, Optional
from services.database.mongodb import MongoDBService
from services.cache.cache_manager import CacheManager

logger = logging.getLogger(__name__)
cache = CacheManager()

def get_departments(force_refresh: bool = False) -> List[str]:
    """
    Get departments with caching
    
    Args:
        force_refresh (bool): Force refresh cache
        
    Returns:
        List[str]: List of department names
    """
    cache_key = "departments"
    
    if not force_refresh:
        cached_depts = cache.get(cache_key)
        if cached_depts is not None:
            return cached_depts
    
    try:
        with MongoDBService() as db:
            departments = db.get_departments()
            cache.set(cache_key, departments, ttl=24*3600)  # Cache for 24 hours
            return departments
    except Exception as e:
        logger.error(f"Error fetching departments: {e}")
        return []

def get_sub_departments(
    dept_name: Optional[str] = None,
    force_refresh: bool = False
) -> List[str]:
    """
    Get sub-departments with caching
    
    Args:
        dept_name (Optional[str]): Department name to filter by
        force_refresh (bool): Force refresh cache
        
    Returns:
        List[str]: List of sub-department names
    """
    cache_key = f"sub_departments_{dept_name or 'all'}"
    
    if not force_refresh:
        cached_sub_depts = cache.get(cache_key)
        if cached_sub_depts is not None:
            return cached_sub_depts
    
    try:
        with MongoDBService() as db:
            sub_departments = db.get_sub_departments(dept_name)
            cache.set(cache_key, sub_departments, ttl=24*3600)  # Cache for 24 hours
            return sub_departments
    except Exception as e:
        logger.error(f"Error fetching sub-departments: {e}")
        return []