# src/services/database/collections.py

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from services.cache.cache_manager import CacheManager
import json

logger = logging.getLogger(__name__)

class CollectionService:
    """Service for managing saved collections using local storage"""
    
    COLLECTION_INDEX_KEY = "collection_index"
    COLLECTION_TTL = 30 * 24 * 3600  # 30 days in seconds
    
    def __init__(self):
        self.cache = CacheManager()
        self._ensure_index()
    
    def _ensure_index(self):
        """Ensure collection index exists"""
        index = self.cache.get(self.COLLECTION_INDEX_KEY)
        if index is None:
            self.cache.set(
                self.COLLECTION_INDEX_KEY,
                [],
                ttl=None  # Index doesn't expire
            )
    
    def save_collection(
        self,
        df: pd.DataFrame,
        name: str,
        description: str,
        tags: List[str],
        source: str
    ) -> bool:
        """
        Save a collection to local storage
        
        Args:
            df: DataFrame to save
            name: Collection name
            description: Collection description
            tags: List of tags
            source: Source of the data
            
        Returns:
            bool: Success status
        """
        try:
            # Check if name exists
            if self._collection_exists(name):
                logger.warning(f"Collection {name} already exists")
                return False
            
            # Create collection metadata
            metadata = {
                "name": name,
                "description": description,
                "tags": tags,
                "source": source,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": list(df.columns)
            }
            
            # Save metadata and data
            collection_key = f"collection_{name}"
            self.cache.set(
                collection_key,
                {
                    "metadata": metadata,
                    "data": df.to_dict('records')
                },
                ttl=self.COLLECTION_TTL
            )
            
            # Update index
            index = self.cache.get(self.COLLECTION_INDEX_KEY)
            index.append(metadata)
            self.cache.set(self.COLLECTION_INDEX_KEY, index)
            
            logger.info(f"Saved collection: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving collection: {e}")
            return False
    
    def get_collections(
        self,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        ascending: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all collections matching criteria
        
        Args:
            search: Optional search term
            sort_by: Field to sort by
            ascending: Sort direction
            
        Returns:
            List of collection metadata
        """
        try:
            # Get index
            index = self.cache.get(self.COLLECTION_INDEX_KEY) or []
            
            # Check expiry and clean up expired collections
            current_time = datetime.now()
            valid_collections = []
            
            for metadata in index:
                expires_at = datetime.fromisoformat(metadata['expires_at'])
                if expires_at > current_time:
                    valid_collections.append(metadata)
                else:
                    # Clean up expired collection
                    self._delete_collection(metadata['name'])
            
            # Update index if any collections were removed
            if len(valid_collections) != len(index):
                self.cache.set(self.COLLECTION_INDEX_KEY, valid_collections)
                index = valid_collections
            
            # Apply search filter
            if search:
                search_lower = search.lower()
                index = [
                    c for c in index
                    if (
                        search_lower in c['name'].lower() or
                        search_lower in c['description'].lower() or
                        any(search_lower in tag.lower() for tag in c['tags'])
                    )
                ]
            
            # Sort results
            if sort_by == "created_at":
                index.sort(
                    key=lambda x: datetime.fromisoformat(x['created_at']),
                    reverse=not ascending
                )
            elif sort_by in ["name", "row_count"]:
                index.sort(key=lambda x: x[sort_by], reverse=not ascending)
            
            return index
            
        except Exception as e:
            logger.error(f"Error getting collections: {e}")
            return []
    
    def get_collection(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific collection by name"""
        try:
            collection_key = f"collection_{name}"
            collection = self.cache.get(collection_key)
            
            if collection:
                # Check expiry
                metadata = collection['metadata']
                expires_at = datetime.fromisoformat(metadata['expires_at'])
                
                if expires_at > datetime.now():
                    return collection
                else:
                    # Clean up expired collection
                    self._delete_collection(name)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting collection {name}: {e}")
            return None
    
    def delete_collection(self, name: str) -> bool:
        """Delete a collection"""
        try:
            return self._delete_collection(name)
        except Exception as e:
            logger.error(f"Error deleting collection {name}: {e}")
            return False
    
    def _delete_collection(self, name: str) -> bool:
        """Internal method to delete a collection"""
        # Remove from cache
        collection_key = f"collection_{name}"
        self.cache.invalidate(collection_key)
        
        # Update index
        index = self.cache.get(self.COLLECTION_INDEX_KEY) or []
        index = [c for c in index if c['name'] != name]
        self.cache.set(self.COLLECTION_INDEX_KEY, index)
        
        return True
    
    def _collection_exists(self, name: str) -> bool:
        """Check if a collection exists"""
        index = self.cache.get(self.COLLECTION_INDEX_KEY) or []
        return any(c['name'] == name for c in index)
    
    def get_collection_df(self, name: str) -> Optional[pd.DataFrame]:
        """Get collection as DataFrame"""
        collection = self.get_collection(name)
        if collection:
            return pd.DataFrame(collection['data'])
        return None

# Create singleton instance
_collection_service = CollectionService()

# Export convenience functions
def save_collection(
    df: pd.DataFrame,
    name: str,
    description: str,
    tags: List[str],
    source: str
) -> bool:
    return _collection_service.save_collection(df, name, description, tags, source)

def get_collections(
    search: Optional[str] = None,
    sort_by: str = "created_at",
    ascending: bool = False
) -> List[Dict[str, Any]]:
    return _collection_service.get_collections(search, sort_by, ascending)

def get_collection(name: str) -> Optional[Dict[str, Any]]:
    return _collection_service.get_collection(name)

def get_collection_df(name: str) -> Optional[pd.DataFrame]:
    return _collection_service.get_collection_df(name)

def delete_collection(name: str) -> bool:
    return _collection_service.delete_collection(name)