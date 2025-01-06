# src/services/database/mongodb.py

import os
import logging
from typing import Optional, Dict, Any, List
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, AutoReconnect, ServerSelectionTimeoutError, InvalidOperation
import pandas as pd
from functools import wraps
from dotenv import load_dotenv
import threading

logger = logging.getLogger(__name__)

def retry_on_connection_error(max_retries: int = 3, delay: float = 1.0):
    """Decorator for retrying on MongoDB connection errors"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (ConnectionFailure, AutoReconnect, ServerSelectionTimeoutError, InvalidOperation) as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(delay)
                        logger.warning(f"Retrying connection (attempt {attempt + 2}/{max_retries})")
                        # Try to reconnect if connection was lost
                        if isinstance(args[0], MongoDBService):
                            args[0].ensure_connection()
            raise last_error
        return wrapper
    return decorator

class MongoDBService:
    """Service class for MongoDB operations with thread-safe connection management"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.initialize()
            return cls._instance

    def initialize(self):
        """Initialize the service (called only once)"""
        load_dotenv(override=True)
        self.mongo_uri = os.getenv('MONGO_URI')
        self.db_name = 'projects'
        self._client = None
        self._database = None
        self._local = threading.local()
    
    def ensure_connection(self):
        """Ensure connection is active and reconnect if necessary"""
        try:
            if not hasattr(self._local, 'client') or self._local.client is None:
                self.connect()
            else:
                # Test connection
                self._local.client.admin.command('ping')
        except Exception:
            self.connect()
    
    @retry_on_connection_error()
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            self._local.client = MongoClient(
                self.mongo_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                maxPoolSize=50,
                minPoolSize=10,
                maxIdleTimeMS=45000,
                waitQueueTimeoutMS=5000
            )
            self._local.database = self._local.client[self.db_name]
            # Test connection
            self._local.client.admin.command('ping')
            logger.info(f"Successfully connected to MongoDB database: {self.db_name}")
            
            # Verify collections
            collections = self._local.database.list_collection_names()
            logger.info(f"Available collections: {collections}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            if hasattr(self._local, 'client') and self._local.client:
                self._local.client.close()
            self._local.client = None
            self._local.database = None
            raise
    
    def disconnect(self):
        """Close MongoDB connection"""
        try:
            if hasattr(self._local, 'client') and self._local.client:
                self._local.client.close()
                self._local.client = None
                self._local.database = None
                logger.info("Disconnected from MongoDB")
        except Exception as e:
            logger.error(f"Error disconnecting from MongoDB: {e}")
    
    @retry_on_connection_error()
    def get_collection(self, collection_name: str = 'projects') -> Collection:
        """Get MongoDB collection"""
        self.ensure_connection()
        
        if not hasattr(self._local, 'database') or self._local.database is None:
            raise ValueError("Database connection not established")
        
        collections = self._local.database.list_collection_names()
        if collection_name not in collections:
            raise ValueError(f"Collection '{collection_name}' not found. Available: {collections}")
        
        return self._local.database[collection_name]

    @retry_on_connection_error()
    def get_departments(self) -> List[str]:
        """Get unique departments"""
        try:
            collection = self.get_collection('projects')
            return sorted(collection.distinct("dept_name"))
        except Exception as e:
            logger.error(f"Error fetching departments: {e}")
            raise

    @retry_on_connection_error()
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
        max_documents: int = 10000,
        include_flagged: bool = False
    ) -> pd.DataFrame:
        """Fetch projects based on query parameters"""
        try:
            collection = self.get_collection('projects')
            
            # Handle data quality filter
            if not include_flagged:
                if "$and" in query:
                    query["$and"].append({"data_quality": {"$exists": False}})
                else:
                    query = {"$and": [query, {"data_quality": {"$exists": False}}]} if query else {"data_quality": {"$exists": False}}
            
            # Get total count
            total_count = collection.count_documents(query)
            logger.info(f"Total matching documents: {total_count}")
            
            # Fetch documents with limit
            cursor = collection.find(query, projection).limit(max_documents)
            documents = list(cursor)
            
            if not documents:
                return pd.DataFrame()
            
            df = pd.DataFrame(documents)
            
            # Convert date columns
            for col in ['announce_date', 'transaction_date', 'contract_date']:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col])
            
            # Convert numeric columns
            for col in ['sum_price_agree', 'price_build', 'project_money']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching projects: {e}")
            raise
    
    @retry_on_connection_error()
    def get_department_summary(self, view_by: str = "count", limit: Optional[int] = None) -> List[Dict]:
        """Get department summary with metrics"""
        try:
            collection = self.get_collection("department_distribution")
            
            pipeline = [
                {"$match": {"_id": {"$ne": "totals"}}},
                {"$group": {
                    "_id": "$_id.dept",
                    "count": {"$sum": "$count"},
                    "total_value": {"$sum": "$total_value"},
                    "count_percentage": {"$sum": "$count_percentage"},
                    "value_percentage": {"$sum": "$value_percentage"},
                    "unique_companies": {"$max": "$unique_companies"}
                }},
                {"$project": {
                    "department": "$_id",
                    "count": 1,
                    "total_value": 1,
                    "count_percentage": 1,
                    "value_percentage": 1,
                    "unique_companies": 1,
                    "total_value_millions": {"$divide": ["$total_value", 1000000]}
                }},
                {"$sort": {view_by: -1}}
            ]
            
            if limit:
                pipeline.append({"$limit": limit})
            
            return list(collection.aggregate(pipeline))
            
        except Exception as e:
            logger.error(f"Error getting department summary: {e}")
            raise
    
    @retry_on_connection_error()
    def get_subdepartment_data(self, department: str, limit: Optional[int] = None) -> List[Dict]:
        """Get sub-department data for a department"""
        try:
            collection = self.get_collection("department_distribution")
            
            pipeline = [
                {"$match": {"_id.dept": department, "_id": {"$ne": "totals"}}},
                {"$group": {
                    "_id": None,
                    "documents": {"$push": "$$ROOT"},
                    "dept_total_count": {"$sum": "$count"},
                    "dept_total_value": {"$sum": "$total_value"}
                }},
                {"$unwind": "$documents"},
                {"$project": {
                    "subdepartment": "$documents._id.subdept",
                    "count": "$documents.count",
                    "total_value": "$documents.total_value",
                    "unique_companies": "$documents.unique_companies",
                    "total_value_millions": {"$divide": ["$documents.total_value", 1000000]},
                    "count_percentage": {
                        "$multiply": [{"$divide": ["$documents.count", "$dept_total_count"]}, 100]
                    },
                    "value_percentage": {
                        "$multiply": [{"$divide": ["$documents.total_value", "$dept_total_value"]}, 100]
                    }
                }},
                {"$sort": {"count": -1}}
            ]
            
            if limit:
                pipeline.append({"$limit": limit})
            
            return list(collection.aggregate(pipeline))
            
        except Exception as e:
            logger.error(f"Error getting subdepartment data: {e}")
            raise

    def __enter__(self):
        self.ensure_connection()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False