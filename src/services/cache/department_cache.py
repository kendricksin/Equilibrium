# src/services/cache/department_cache.py

import logging
from typing import List, Dict, Any
import time
from services.database.mongodb import MongoDBService
from services.cache.cache_manager import CacheManager

logger = logging.getLogger(__name__)

class DepartmentCache:
    """Enhanced department caching service using aggregated data"""
    
    def __init__(self):
        self.cache = CacheManager()
        self._last_refresh: float = 0
        self._refresh_interval: int = 3600  # 1 hour
        self._department_stats: Dict[str, Dict] = {}
    
    def get_departments(self, force_refresh: bool = False) -> List[str]:
        """
        Get all departments ranked by project count using aggregation
        
        Args:
            force_refresh (bool): Force refresh cache
            
        Returns:
            List[str]: List of department names sorted by frequency
        """
        cache_key = "ranked_departments"
        current_time = time.time()
        
        try:
            # Check if cache refresh is needed
            if (
                force_refresh or
                current_time - self._last_refresh > self._refresh_interval or
                not self._department_stats
            ):
                logger.info("Refreshing departments cache from aggregation")
                
                with MongoDBService() as db:
                    # Get all departments without limit
                    dept_summary = db.get_department_summary(view_by="count", limit=None)
                    
                    if not dept_summary:
                        logger.error("No departments found in aggregation")
                        cached = self.cache.get(cache_key)
                        return cached if cached else []
                    
                    # Update department stats cache
                    self._department_stats = {
                        dept["department"]: {
                            "count": dept["count"],
                            "total_value": dept["total_value"],
                            "total_value_millions": dept["total_value_millions"],
                            "count_percentage": dept["count_percentage"],
                            "value_percentage": dept["value_percentage"],
                            "unique_companies": dept["unique_companies"]
                        }
                        for dept in dept_summary
                    }
                    
                    # Extract ordered department names
                    departments = [dept["department"] for dept in dept_summary]
                    
                    # Update cache
                    self.cache.set(cache_key, departments, ttl=self._refresh_interval)
                    self._last_refresh = current_time
                    
                    return departments
            
            # Try to get from cache first
            cached_depts = self.cache.get(cache_key)
            if cached_depts:
                return cached_depts
            
            # If cache miss, get fresh data
            return self.get_departments(force_refresh=True)
            
        except Exception as e:
            logger.error(f"Error getting ranked departments: {e}")
            cached = self.cache.get(cache_key)
            return cached if cached else []
    
    def get_sub_departments(
        self,
        dept_name: str,
        force_refresh: bool = False
    ) -> List[str]:
        """Get all sub-departments ranked by project count using aggregation"""
        if not dept_name:
            return []
            
        cache_key = f"ranked_sub_departments_{dept_name}"
        
        try:
            if force_refresh:
                with MongoDBService() as db:
                    # Get all subdepartments without limit
                    subdept_data = db.get_subdepartment_data(dept_name, limit=None)
                    
                    if not subdept_data:
                        return []
                    
                    # Extract ordered subdepartment names
                    sub_departments = [
                        sub["subdepartment"]
                        for sub in subdept_data
                        if sub["subdepartment"]  # Filter out None/empty
                    ]
                    
                    if sub_departments:
                        self.cache.set(cache_key, sub_departments, ttl=self._refresh_interval)
                        return sub_departments
            
            # Try cache first
            cached_subs = self.cache.get(cache_key)
            if cached_subs is not None:
                return cached_subs
            
            # Cache miss, get fresh data
            return self.get_sub_departments(dept_name, force_refresh=True)
            
        except Exception as e:
            logger.error(f"Error getting ranked sub-departments for {dept_name}: {e}")
            cached = self.cache.get(cache_key)
            return cached if cached else []
    
    def get_department_stats(self, dept_name: str) -> Dict[str, Any]:
        """
        Get statistics for a specific department
        
        Args:
            dept_name (str): Department name
            
        Returns:
            Dict[str, Any]: Department statistics including count, value, etc.
        """
        return self._department_stats.get(dept_name, {})
    
    def get_subdepartment_stats(self, dept_name: str) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all subdepartments of a department"""
        try:
            with MongoDBService() as db:
                # Get all subdepartments without limit
                subdept_data = db.get_subdepartment_data(dept_name, limit=None)
                return {
                    sub["subdepartment"]: {
                        "count": sub["count"],
                        "total_value": sub["total_value"],
                        "total_value_millions": sub["total_value_millions"],
                        "count_percentage": sub["count_percentage"],
                        "value_percentage": sub["value_percentage"],
                        "unique_companies": sub["unique_companies"]
                    }
                    for sub in subdept_data
                    if sub["subdepartment"]
                }
        except Exception as e:
            logger.error(f"Error getting subdepartment stats for {dept_name}: {e}")
            return {}

# Create singleton instance
_department_cache = DepartmentCache()

# Export convenience functions
def get_departments(force_refresh: bool = False) -> List[str]:
    """Get departments ranked by frequency"""
    return _department_cache.get_departments(force_refresh)

def get_sub_departments(dept_name: str, force_refresh: bool = False) -> List[str]:
    """Get sub-departments ranked by frequency"""
    return _department_cache.get_sub_departments(dept_name, force_refresh)

def get_department_stats(dept_name: str) -> Dict[str, Any]:
    """Get department statistics"""
    return _department_cache.get_department_stats(dept_name)

def get_subdepartment_stats(dept_name: str) -> Dict[str, Dict[str, Any]]:
    """Get subdepartment statistics"""
    return _department_cache.get_subdepartment_stats(dept_name)