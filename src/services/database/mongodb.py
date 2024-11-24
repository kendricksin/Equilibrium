# src/services/database/mongodb.py

import os
import logging
from typing import Optional, Dict, Any, List
from pymongo import MongoClient
from pymongo.collection import Collection
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

class MongoDBService:
    """Service class for MongoDB operations"""
    
    def __init__(self):
        self.mongo_uri = os.environ.get('MONGO_URI')
        if not self.mongo_uri:
            logger.error("MONGO_URI environment variable not set")
            raise ValueError("MongoDB URI not configured")
        
        self.client: Optional[MongoClient] = None
        self.db_name = "projects"
        self.collection_name = "projects"
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
    
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(self.mongo_uri)
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
    
    def get_collection(self) -> Collection:
        """Get MongoDB collection"""
        if not self.client:
            self.connect()
        return self.client[self.db_name][self.collection_name]
    
    def get_projects(self, query: Dict[str, Any]) -> pd.DataFrame:
        """
        Fetch projects based on query parameters
        
        Args:
            query (Dict[str, Any]): MongoDB query parameters
            
        Returns:
            pd.DataFrame: DataFrame containing project data
        """
        try:
            collection = self.get_collection()
            data = list(collection.find(query))
            
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
            numeric_columns = ['sum_price_agree', 'price_build']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching projects: {e}")
            raise
    
    def get_departments(self) -> List[str]:
        """Get unique departments"""
        try:
            collection = self.get_collection()
            return sorted(collection.distinct("dept_name"))
        except Exception as e:
            logger.error(f"Error fetching departments: {e}")
            raise
    
    def get_sub_departments(self, dept_name: str) -> List[str]:
        """
        Get sub-departments for a given department
        
        Args:
            dept_name (str): Department name
            
        Returns:
            List[str]: List of sub-departments
        """
        try:
            collection = self.get_collection()
            query = {"dept_name": dept_name} if dept_name else {}
            return sorted(collection.distinct("dept_sub_name", query))
        except Exception as e:
            logger.error(f"Error fetching sub-departments: {e}")
            raise