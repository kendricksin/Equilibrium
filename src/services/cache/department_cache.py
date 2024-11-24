# src/services/cache/department_cache.py

import logging
from typing import List, Optional, Set
import time
from services.database.mongodb import MongoDBService
from services.cache.cache_manager import CacheManager

logger = logging.getLogger(__name__)

class DepartmentCache:
    """Enhanced department caching service"""
    
    def __init__(self):
        self.cache = CacheManager()
        self._last_refresh: float = 0
        self._refresh_interval: int = 3600  # 1 hour
        self._department_set: Set[str] = set()
    
    def get_departments(self, force_refresh: bool = False) -> List[str]:
        """
        Get departments with enhanced caching and validation
        
        Args:
            force_refresh (bool): Force refresh cache
            
        Returns:
            List[str]: List of department names
        """
        cache_key = "departments"
        current_time = time.time()
        
        try:
            # Check if cache refresh is needed
            if (
                force_refresh or
                current_time - self._last_refresh > self._refresh_interval
            ):
                logger.info("Refreshing departments cache")
                
                with MongoDBService() as db:
                    departments = db.get_departments()
                    
                    if not departments:
                        logger.error("No departments returned from database")
                        # Return cached data if available
                        cached = self.cache.get(cache_key)
                        return cached if cached else []
                    
                    # Validate and clean department names
                    departments = [
                        dept for dept in departments
                        if dept and isinstance(dept, str)
                    ]
                    
                    # Update cache
                    self.cache.set(cache_key, sorted(departments), ttl=self._refresh_interval)
                    self._department_set = set(departments)
                    self._last_refresh = current_time
                    
                    return departments
            
            # Try to get from cache first
            cached_depts = self.cache.get(cache_key)
            if cached_depts:
                return cached_depts
            
            # If cache miss, get fresh data
            return self.get_departments(force_refresh=True)
            
        except Exception as e:
            logger.error(f"Error getting departments: {e}")
            # Try to return cached data in case of error
            cached = self.cache.get(cache_key)
            return cached if cached else []
    
    def get_sub_departments(
        self,
        dept_name: str,
        force_refresh: bool = False
    ) -> List[str]:
        """
        Get sub-departments with enhanced caching and validation
        
        Args:
            dept_name (str): Department name
            force_refresh (bool): Force refresh cache
            
        Returns:
            List[str]: List of sub-department names
        """
        if not dept_name:
            return []
            
        cache_key = f"sub_departments_{dept_name}"
        
        try:
            # Validate department exists
            if dept_name not in self._department_set:
                depts = self.get_departments(force_refresh=True)
                if dept_name not in set(depts):
                    logger.error(f"Invalid department name: {dept_name}")
                    return []
            
            if force_refresh:
                with MongoDBService() as db:
                    sub_departments = db.get_sub_departments(dept_name)
                    
                    if sub_departments:
                        # Clean and validate sub-department names
                        sub_departments = [
                            sub for sub in sub_departments
                            if sub and isinstance(sub, str)
                        ]
                        self.cache.set(cache_key, sorted(sub_departments), ttl=self._refresh_interval)
                        return sub_departments
            
            # Try cache first
            cached_subs = self.cache.get(cache_key)
            if cached_subs is not None:
                return cached_subs
            
            # Cache miss, get fresh data
            return self.get_sub_departments(dept_name, force_refresh=True)
            
        except Exception as e:
            logger.error(f"Error getting sub-departments for {dept_name}: {e}")
            cached = self.cache.get(cache_key)
            return cached if cached else []

# Create singleton instance
_department_cache = DepartmentCache()

# Export convenience functions
def get_departments(force_refresh: bool = False) -> List[str]:
    """Get departments with caching"""
    return _department_cache.get_departments(force_refresh)

def get_sub_departments(dept_name: str, force_refresh: bool = False) -> List[str]:
    """Get sub-departments with caching"""
    return _department_cache.get_sub_departments(dept_name, force_refresh)