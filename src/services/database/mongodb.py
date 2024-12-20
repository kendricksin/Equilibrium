# src/services/database/mongodb.py

import os
import logging
from typing import Optional, Dict, Any, List, Generator
from pymongo import MongoClient, errors
from pymongo.collection import Collection
from pymongo.database import Database
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

    def __init__(self):
        load_dotenv(override=True)
        self.mongo_uri = os.getenv('MONGO_URI')
        self.db_name = 'projects'  # Explicitly set database name
        self._client: Optional[MongoClient] = None
        self._database: Optional[Database] = None
        
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self):
        self.disconnect()
    
    @retry_on_connection_error()
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            if self._client is None:
                self._client = MongoClient(self.mongo_uri)
                self._database = self._client[self.db_name]
                # Test connection
                self._client.admin.command('ismaster')
                logger.info(f"Successfully connected to MongoDB database: {self.db_name}")
                
                # Verify collections
                collections = self._database.list_collection_names()
                logger.info(f"Available collections: {collections}")
                
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def disconnect(self):
        """Close MongoDB connection"""
        try:
            if self._client is not None:
                self._client.close()
                self._client = None
                self._database = None
                logger.info("Disconnected from MongoDB")
        except Exception as e:
            logger.error(f"Error disconnecting from MongoDB: {e}")
    
    def get_collection(self, collection_name: str = 'projects') -> Collection:
        """Get MongoDB collection"""
        try:
            if self._database is None:
                self.connect()
            
            if self._database is None:
                raise ValueError("Database connection not established")
            
            # Verify collection exists
            collections = self._database.list_collection_names()
            if collection_name not in collections:
                raise ValueError(f"Collection '{collection_name}' not found in database '{self.db_name}'. Available collections: {collections}")
            
            return self._database[collection_name]
            
        except Exception as e:
            logger.error(f"Error accessing collection {collection_name}: {e}")
            raise

    def get_department_summary(self, view_by: str = "count", limit: int = 20) -> List[Dict]:
        """Get department summary with sorting and pre-calculated metrics"""
        try:
            if self._database is None:
                self.connect()
                
            sort_field = "count" if view_by == "count" else "total_value"
            collection = self.get_collection("department_distribution")
            
            pipeline = [
                # Match non-totals documents
                {"$match": {"_id": {"$ne": "totals"}}},
                
                # Group by department
                {
                    "$group": {
                        "_id": "$_id.dept",
                        "count": {"$sum": "$count"},
                        "total_value": {"$sum": "$total_value"},
                        "count_percentage": {"$sum": "$count_percentage"},
                        "value_percentage": {"$sum": "$value_percentage"},
                        "unique_companies": {"$max": "$unique_companies"}
                    }
                },
                
                # Format for output
                {
                    "$project": {
                        "department": "$_id",
                        "count": 1,
                        "total_value": 1,
                        "count_percentage": 1,
                        "value_percentage": 1,
                        "unique_companies": 1,
                        "total_value_millions": {"$divide": ["$total_value", 1000000]}
                    }
                },
                
                # Sort by selected field
                {"$sort": {sort_field: -1}},
                
                # Limit results
                {"$limit": limit}
            ]
            
            return list(collection.aggregate(pipeline))
            
        except Exception as e:
            logger.error(f"Error getting department summary: {e}")
            raise

    def get_subdepartment_data(self, department: str) -> List[Dict]:
        """Get sub-department data for a specific department"""
        try:
            if self._database is None:
                self.connect()
                
            collection = self.get_collection("department_distribution")
            
            pipeline = [
                # Match specific department
                {
                    "$match": {
                        "_id.dept": department,
                        "_id": {"$ne": "totals"}
                    }
                },
                
                # Calculate department totals for percentages
                {
                    "$group": {
                        "_id": None,
                        "documents": {"$push": "$$ROOT"},
                        "dept_total_count": {"$sum": "$count"},
                        "dept_total_value": {"$sum": "$total_value"}
                    }
                },
                
                # Unwind back to individual documents
                {"$unwind": "$documents"},
                
                # Calculate subdepartment percentages
                {
                    "$project": {
                        "subdepartment": "$documents._id.subdept",
                        "count": "$documents.count",
                        "total_value": "$documents.total_value",
                        "unique_companies": "$documents.unique_companies",
                        "total_value_millions": {"$divide": ["$documents.total_value", 1000000]},
                        "count_percentage": {
                            "$multiply": [
                                {"$divide": ["$documents.count", "$dept_total_count"]},
                                100
                            ]
                        },
                        "value_percentage": {
                            "$multiply": [
                                {"$divide": ["$documents.total_value", "$dept_total_value"]},
                                100
                            ]
                        }
                    }
                },
                
                # Sort by count
                {"$sort": {"count": -1}}
            ]
            
            return list(collection.aggregate(pipeline))
            
        except Exception as e:
            logger.error(f"Error getting subdepartment data: {e}")
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

    @retry_on_connection_error()
    def get_projects(
        self,
        query: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None,
        chunk_size: int = 1000,
        max_documents: int = 10000,
        include_flagged: bool = False
    ) -> pd.DataFrame:
        """
        Fetch projects based on query parameters with chunking and limits
        
        Args:
            query (Dict[str, Any]): MongoDB query parameters
            projection (Optional[Dict[str, Any]]): Fields to include/exclude
            chunk_size (int): Number of documents per chunk
            max_documents (int): Maximum total documents to return
            include_flagged (bool): Whether to include documents with data quality issues
                
        Returns:
            pd.DataFrame: DataFrame containing project data
        """
        try:
            collection = self.get_collection('projects')
            
            # Add data quality filter to query unless explicitly including flagged documents
            if not include_flagged:
                # Modify query to exclude documents with data quality tags
                if "$and" in query:
                    query["$and"].append({"data_quality": {"$exists": False}})
                elif query:
                    query = {
                        "$and": [
                            query,
                            {"data_quality": {"$exists": False}}
                        ]
                    }
                else:
                    query = {"data_quality": {"$exists": False}}
                
                logger.info("Excluding documents with data quality issues")
            
            # First get total count
            total_count = collection.count_documents(query)
            logger.info(f"Total matching documents: {total_count}")
            
            if total_count > max_documents:
                logger.warning(f"Query would return {total_count} documents, limiting to {max_documents}")
                
            # Process in chunks
            all_data = []
            processed_count = 0
            
            for chunk in self._get_documents_in_chunks(
                collection, query, projection, chunk_size, max_documents
            ):
                all_data.extend(chunk)
                processed_count += len(chunk)
                logger.info(f"Processed {processed_count} documents")
                
                if processed_count >= max_documents:
                    logger.warning("Reached maximum document limit")
                    break
            
            if not all_data:
                logger.warning("No data found for the given query")
                return pd.DataFrame()
            
            df = pd.DataFrame(all_data)
            
            # Convert date columns
            date_columns = ['announce_date', 'transaction_date', 'contract_date']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col])
            
            # Convert numeric columns
            numeric_columns = ['sum_price_agree', 'price_build', 'project_money']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Add flag column if including flagged documents
            if include_flagged and not df.empty:
                df['is_flagged'] = df['data_quality'].notna()
                if 'data_quality' in df.columns:
                    df['flag_type'] = df['data_quality'].apply(
                        lambda x: x.get('issue_type') if pd.notna(x) else None
                    )
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching projects: {e}")
            raise
    
    def _get_documents_in_chunks(
        self,
        collection,
        query: Dict[str, Any],
        projection: Optional[Dict[str, Any]],
        chunk_size: int,
        max_documents: int
    ) -> Generator[List[Dict], None, None]:
        """
        Generator function to fetch documents in chunks
        """
        try:
            processed = 0
            cursor = collection.find(query, projection).sort('_id', 1)
            
            while True:
                chunk = []
                for _ in range(chunk_size):
                    try:
                        doc = next(cursor)
                        chunk.append(doc)
                        processed += 1
                        
                        if processed >= max_documents:
                            break
                    except StopIteration:
                        break
                
                if not chunk:
                    break
                    
                yield chunk
                
                if processed >= max_documents:
                    break
                    
        except Exception as e:
            logger.error(f"Error in chunk processing: {e}")
            raise

    @staticmethod
    def get_instance(config_path: Optional[str] = None) -> 'MongoDBService':
        """Get singleton instance of MongoDBService"""
        return MongoDBService(config_path)
