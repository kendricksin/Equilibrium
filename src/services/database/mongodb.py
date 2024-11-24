# src/services/database/mongodb.py

import os
import logging
from typing import Optional, Dict, Any, List, Union
from pymongo import MongoClient, errors
from pymongo.collection import Collection
from datetime import datetime
import pandas as pd
from functools import wraps
import json
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()
def __init__(self):
    load_dotenv(override=True)  # Force override of system variables
    self.mongo_uri = os.getenv('MONGO_URI')
    self.db_name = os.getenv('MONGO_DB')

class DatabaseConfig:
    """Database configuration management"""
    
    DEFAULT_CONFIG = {
        "mongo_uri": os.getenv("MONGO_URI"),
        "db_name": os.getenv("MONGO_DB"),
        "collections": {
            "projects": "projects",
            "departments": "departments",
            # Add other collections as needed
        }
    }
    
    @classmethod
    def load_config(cls, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load database configuration from file or environment
        
        Args:
            config_path (Optional[str]): Path to config file
            
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        config = cls.DEFAULT_CONFIG.copy()
        
        # Try loading from config file
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                config.update(file_config)
            except Exception as e:
                logger.error(f"Error loading config file: {e}")
        
        # Override with environment variables if present
        env_vars = {
            "MONGO_URI": "mongo_uri",
            "MONGO_DB": "db_name",
        }
        
        for env_var, config_key in env_vars.items():
            if value := os.environ.get(env_var):
                if '.' in config_key:
                    parent, child = config_key.split('.')
                    config[parent][child] = value
                else:
                    config[config_key] = value
        
        return config

def retry_on_connection_error(max_retries: int = 3, delay: float = 1.0):
    """Decorator for retrying on MongoDB connection errors"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except errors.ConnectionError as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(delay)
                        logger.warning(f"Retrying connection (attempt {attempt + 2}/{max_retries})")
            raise last_error
        return wrapper
    return decorator

class MongoDBService:
    """Service class for MongoDB operations"""
    
    _instance = None
    _config = None
    
    def __new__(cls, config_path: Optional[str] = None):
        """Singleton pattern to ensure single database connection"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._config = DatabaseConfig.load_config(config_path)
        return cls._instance
    
    def __init__(self, config_path: Optional[str] = None):
        # Initialize only once
        if not hasattr(self, 'client'):
            self.client: Optional[MongoClient] = None
            self.db_name = self._config['db_name']
            self.collections = self._config['collections']
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
    
    @retry_on_connection_error()
    def connect(self):
        """Establish connection to MongoDB with retry logic"""
        if not self.client:
            try:
                self.client = MongoClient(self._config['mongo_uri'])
                # Test connection
                self.client.admin.command('ismaster')
                logger.info("Successfully connected to MongoDB")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise
    
    def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self.client = None
            logger.info("Disconnected from MongoDB")
    
    def get_collection(self, collection_name: str = 'projects') -> Collection:
        """
        Get MongoDB collection
        
        Args:
            collection_name (str): Name of the collection
            
        Returns:
            Collection: MongoDB collection
        """
        if not self.client:
            self.connect()
        
        if collection_name not in self.collections:
            raise ValueError(f"Unknown collection: {collection_name}")
            
        return self.client[self.db_name][self.collections[collection_name]]
    
    @retry_on_connection_error()
    def get_projects(
        self,
        query: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Fetch projects based on query parameters
        
        Args:
            query (Dict[str, Any]): MongoDB query parameters
            projection (Optional[Dict[str, Any]]): Fields to include/exclude
            limit (Optional[int]): Maximum number of documents to return
            
        Returns:
            pd.DataFrame: DataFrame containing project data
        """
        try:
            collection = self.get_collection('projects')
            cursor = collection.find(query, projection)
            
            if limit:
                cursor = cursor.limit(limit)
            
            data = list(cursor)
            
            if not data:
                logger.warning("No data found for the given query")
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            
            # Convert date columns
            date_columns = ['announce_date', 'transaction_date', 'contract_date', 'contract_finish_date']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col])
            
            # Convert numeric columns
            numeric_columns = ['sum_price_agree', 'price_build', 'project_money']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching projects: {e}")
            raise
    
    def get_departments(self, cached: bool = True) -> List[str]:
        """Get unique departments"""
        try:
            collection = self.get_collection('projects')
            return sorted(collection.distinct("dept_name"))
        except Exception as e:
            logger.error(f"Error fetching departments: {e}")
            raise
    
    def get_sub_departments(self, dept_name: str) -> List[str]:
        """Get sub-departments for a given department"""
        try:
            collection = self.get_collection('projects')
            query = {"dept_name": dept_name} if dept_name else {}
            return sorted(collection.distinct("dept_sub_name", query))
        except Exception as e:
            logger.error(f"Error fetching sub-departments: {e}")
            raise

    @staticmethod
    def get_instance(config_path: Optional[str] = None) -> 'MongoDBService':
        """Get singleton instance of MongoDBService"""
        return MongoDBService(config_path)