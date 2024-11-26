# src/services/cache/purchase_type_cache.py

import logging
from typing import List
from services.database.mongodb import MongoDBService
from services.cache.cache_manager import CacheManager

logger = logging.getLogger(__name__)
cache = CacheManager()

def get_purchase_methods(force_refresh: bool = False) -> List[str]:
    """
    Get purchase methods with caching
    
    Args:
        force_refresh (bool): Force refresh cache
        
    Returns:
        List[str]: List of purchase method names
    """
    cache_key = "purchase_methods"
    
    if not force_refresh:
        cached_methods = cache.get(cache_key)
        if cached_methods is not None:
            return cached_methods
    
    try:
        with MongoDBService() as db:
            methods = sorted(db.get_collection().distinct("purchase_method_name"))
            cache.set(cache_key, methods, ttl=24*3600)  # Cache for 24 hours
            return methods
    except Exception as e:
        logger.error(f"Error fetching purchase methods: {e}")
        return []

def get_project_types(force_refresh: bool = False) -> List[str]:
    """
    Get project types with caching
    
    Args:
        force_refresh (bool): Force refresh cache
        
    Returns:
        List[str]: List of project type names
    """
    cache_key = "project_types"
    
    if not force_refresh:
        cached_types = cache.get(cache_key)
        if cached_types is not None:
            return cached_types
    
    try:
        with MongoDBService() as db:
            types = sorted(db.get_collection().distinct("project_type_name"))
            cache.set(cache_key, types, ttl=24*3600)  # Cache for 24 hours
            return types
    except Exception as e:
        logger.error(f"Error fetching project types: {e}")
        return []
