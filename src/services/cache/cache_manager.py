# src/services/cache/cache_manager.py

import os
import json
import logging
from typing import Any, Optional
from datetime import datetime, timedelta
import pickle

logger = logging.getLogger(__name__)

class CacheManager:
    """Manages file-based caching for the application"""
    
    def __init__(self, cache_dir: str = "./cache"):
        self.cache_dir = cache_dir
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Ensure cache directory exists"""
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_cache_path(self, key: str) -> str:
        """Get full path for cache file"""
        return os.path.join(self.cache_dir, f"{key}.cache")
    
    def _get_metadata_path(self, key: str) -> str:
        """Get full path for cache metadata file"""
        return os.path.join(self.cache_dir, f"{key}.meta")
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None  # TTL in seconds
    ):
        """
        Store value in cache
        
        Args:
            key (str): Cache key
            value (Any): Value to cache
            ttl (Optional[int]): Time to live in seconds
        """
        try:
            # Save value
            cache_path = self._get_cache_path(key)
            with open(cache_path, 'wb') as f:
                pickle.dump(value, f)
            
            # Save metadata
            metadata = {
                'created_at': datetime.now().isoformat(),
                'ttl': ttl
            }
            
            meta_path = self._get_metadata_path(key)
            with open(meta_path, 'w') as f:
                json.dump(metadata, f)
                
            logger.info(f"Cached value for key: {key}")
            
        except Exception as e:
            logger.error(f"Error caching value for key {key}: {e}")
            raise
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache
        
        Args:
            key (str): Cache key
            
        Returns:
            Optional[Any]: Cached value if exists and valid, None otherwise
        """
        try:
            cache_path = self._get_cache_path(key)
            meta_path = self._get_metadata_path(key)
            
            # Check if cache exists
            if not (os.path.exists(cache_path) and os.path.exists(meta_path)):
                return None
            
            # Check TTL
            with open(meta_path, 'r') as f:
                metadata = json.load(f)
            
            created_at = datetime.fromisoformat(metadata['created_at'])
            ttl = metadata.get('ttl')
            
            if ttl is not None:
                if datetime.now() - created_at > timedelta(seconds=ttl):
                    logger.info(f"Cache expired for key: {key}")
                    self.invalidate(key)
                    return None
            
            # Load value
            with open(cache_path, 'rb') as f:
                value = pickle.load(f)
            
            logger.info(f"Retrieved cached value for key: {key}")
            return value
            
        except Exception as e:
            logger.error(f"Error retrieving cached value for key {key}: {e}")
            self.invalidate(key)
            return None
    
    def invalidate(self, key: str):
        """
        Remove item from cache
        
        Args:
            key (str): Cache key
        """
        try:
            cache_path = self._get_cache_path(key)
            meta_path = self._get_metadata_path(key)
            
            if os.path.exists(cache_path):
                os.remove(cache_path)
            if os.path.exists(meta_path):
                os.remove(meta_path)
                
            logger.info(f"Invalidated cache for key: {key}")
            
        except Exception as e:
            logger.error(f"Error invalidating cache for key {key}: {e}")