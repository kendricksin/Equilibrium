# src/state/data_state.py

import pandas as pd
from typing import Optional, Dict, Any, List
import streamlit as st
import logging
from services.cache.cache_manager import CacheManager
from services.database.mongodb import MongoDBService

logger = logging.getLogger(__name__)

class DataState:
    """Manages application data state and caching"""
    
    def __init__(self):
        self.cache = CacheManager()
        self.db = MongoDBService()
    
    def get_filtered_data(
        self,
        filters: Dict[str, Any],
        force_refresh: bool = False
    ) -> Optional[pd.DataFrame]:
        """
        Get filtered data, using cache when possible
        
        Args:
            filters (Dict[str, Any]): Filter parameters
            force_refresh (bool): Force data refresh
            
        Returns:
            Optional[pd.DataFrame]: Filtered DataFrame
        """
        try:
            # Generate cache key from filters
            cache_key = f"filtered_data_{hash(str(filters))}"
            
            # Check cache first
            if not force_refresh:
                cached_data = self.cache.get(cache_key)
                if cached_data is not None:
                    return cached_data
            
            # Get fresh data
            query = self._build_query(filters)
            with self.db as db:
                df = db.get_projects(query)
            
            if df is not None and not df.empty:
                # Cache the results
                self.cache.set(cache_key, df, ttl=3600)  # Cache for 1 hour
                return df
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting filtered data: {e}")
            return None
    
    def get_analysis_results(
        self,
        key: str,
        force_refresh: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached analysis results
        
        Args:
            key (str): Analysis key
            force_refresh (bool): Force refresh
            
        Returns:
            Optional[Dict[str, Any]]: Analysis results
        """
        try:
            cache_key = f"analysis_{key}"
            
            if not force_refresh:
                cached_results = self.cache.get(cache_key)
                if cached_results is not None:
                    return cached_results
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting analysis results: {e}")
            return None
    
    def save_analysis_results(
        self,
        key: str,
        results: Dict[str, Any],
        ttl: Optional[int] = None
    ):
        """
        Cache analysis results
        
        Args:
            key (str): Analysis key
            results (Dict[str, Any]): Analysis results
            ttl (Optional[int]): Cache TTL in seconds
        """
        try:
            cache_key = f"analysis_{key}"
            self.cache.set(cache_key, results, ttl=ttl)
            
        except Exception as e:
            logger.error(f"Error saving analysis results: {e}")
    
    def clear_cache(self, pattern: Optional[str] = None):
        """
        Clear cache entries
        
        Args:
            pattern (Optional[str]): Pattern to match cache keys
        """
        try:
            if pattern:
                # Clear specific cache entries
                self.cache.invalidate_pattern(pattern)
            else:
                # Clear all cache
                self.cache.clear_all()
                
            logger.info(f"Cache cleared: {pattern or 'all'}")
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    @staticmethod
    def _build_query(filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build MongoDB query from filters"""
        from state.filters import FilterManager
        return FilterManager.build_mongo_query(filters)