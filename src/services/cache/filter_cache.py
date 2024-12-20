# src/services/cache/filter_cache.py

import logging
from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime
from services.database.mongodb import MongoDBService
from services.cache.cache_manager import CacheManager
from state.filters import FilterManager

logger = logging.getLogger(__name__)

class FilterCache:
    """Service for handling filtered data caching"""
    
    def __init__(self):
        self.cache = CacheManager()
        self.filter_manager = FilterManager()
        self.db = MongoDBService()  # Keep a single instance
    
    def get_filtered_data(
        self,
        filters: Dict[str, Any],
        force_refresh: bool = False,
        chunk_size: int = 1000,
        max_documents: int = 10000
    ) -> Optional[pd.DataFrame]:
        """Get filtered data with caching"""
        try:
            # Validate filters
            if not self.filter_manager.validate_filters(filters):
                logger.error("Invalid filter parameters")
                return None
            
            # Generate cache key
            cache_key = self._generate_cache_key(filters)
            
            # Check cache first
            if not force_refresh:
                cached_data = self.cache.get(cache_key)
                if cached_data is not None:
                    logger.info(f"Retrieved cached data for key: {cache_key}")
                    return cached_data
            
            # Get fresh data from database
            query = self.filter_manager.build_mongo_query(filters)
            df = self.db.get_projects(
                query,
                chunk_size=chunk_size,
                max_documents=max_documents
            )
            
            if df is not None and not df.empty:
                # Cache the results
                self.cache.set(cache_key, df, ttl=3600)
                logger.info(f"Cached new data for key: {cache_key}")
                return df
            
            logger.warning("No data found for the given filters")
            return None
            
        except Exception as e:
            logger.error(f"Error getting filtered data: {e}", exc_info=True)
            return None

    def _generate_cache_key(self, filters: Dict[str, Any]) -> str:
        """Generate cache key from filters"""
        try:
            key_parts = []
            
            # Department filters
            if filters.get('dept_name'):
                key_parts.append(f"dept_{filters['dept_name']}")
            
            if filters.get('dept_sub_name'):
                key_parts.append(f"subdept_{filters['dept_sub_name']}")
            
            # Purchase method and project type filters
            if filters.get('purchase_method_name'):
                key_parts.append(f"method_{filters['purchase_method_name']}")
                
            if filters.get('project_type_name'):
                key_parts.append(f"type_{filters['project_type_name']}")
            
            # Date filters
            if filters.get('date_start'):
                key_parts.append(f"start_{filters['date_start'].strftime('%Y%m%d')}")
            
            if filters.get('date_end'):
                key_parts.append(f"end_{filters['date_end'].strftime('%Y%m%d')}")
            
            # Price filters
            if filters.get('price_start') is not None:
                key_parts.append(f"price_start_{filters['price_start']}")
            
            if filters.get('price_end') is not None:
                key_parts.append(f"price_end_{filters['price_end']}")
            
            return "filter_" + "_".join(key_parts)
            
        except Exception as e:
            logger.error(f"Error generating cache key: {e}", exc_info=True)
            return f"filter_error_{datetime.now().timestamp()}"
    
    def invalidate_cache(self, pattern: Optional[str] = None):
        """
        Invalidate cache entries
        
        Args:
            pattern (Optional[str]): Pattern to match cache keys
        """
        try:
            if pattern:
                self.cache.invalidate_pattern(pattern)
                logger.info(f"Invalidated cache entries matching: {pattern}")
            else:
                self.cache.invalidate("filter_*")
                logger.info("Invalidated all filter cache entries")
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}", exc_info=True)

# Create a singleton instance of FilterCache
_filter_cache = FilterCache()

def get_filtered_data(
    filters: Dict[str, Any], 
    force_refresh: bool = False
) -> Optional[pd.DataFrame]:
    """
    Get filtered data with caching (helper function)
    
    Args:
        filters (Dict[str, Any]): Filter parameters
        force_refresh (bool): Force data refresh
        
    Returns:
        Optional[pd.DataFrame]: Filtered DataFrame
    """
    return _filter_cache.get_filtered_data(filters, force_refresh)