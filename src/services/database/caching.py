# src/services/database/caching.py

from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime, timedelta
import logging
from .mongodb import MongoDBService, retry_on_connection_error

logger = logging.getLogger(__name__)

class CachingService:
    """Service for caching frequently accessed analytics data"""
    
    def __init__(self):
        self.mongo = MongoDBService()
        self.cache_collection = "analytics_cache"
        self.cache_duration = timedelta(hours=24)
    
    @retry_on_connection_error()
    def get_cached_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached data if available and not expired"""
        try:
            collection = self.mongo.get_collection(self.cache_collection)
            cache_doc = collection.find_one({
                "key": cache_key,
                "expiry": {"$gt": datetime.utcnow()}
            })
            return cache_doc.get("data") if cache_doc else None
            
        except Exception as e:
            logger.error(f"Error getting cached data: {e}")
            return None
    
    @retry_on_connection_error()
    def set_cached_data(
        self,
        cache_key: str,
        data: Dict[str, Any],
        duration: Optional[timedelta] = None
    ) -> bool:
        """Cache data with expiration"""
        try:
            collection = self.mongo.get_collection(self.cache_collection)
            
            # Remove existing cache entry
            collection.delete_many({"key": cache_key})
            
            # Insert new cache entry
            collection.insert_one({
                "key": cache_key,
                "data": data,
                "expiry": datetime.utcnow() + (duration or self.cache_duration),
                "created_at": datetime.utcnow()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting cached data: {e}")
            return False
    
    @retry_on_connection_error()
    def clear_cache(self, cache_key: Optional[str] = None) -> bool:
        """Clear specific or all cached data"""
        try:
            collection = self.mongo.get_collection(self.cache_collection)
            
            if cache_key:
                collection.delete_many({"key": cache_key})
            else:
                collection.delete_many({})
            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False 