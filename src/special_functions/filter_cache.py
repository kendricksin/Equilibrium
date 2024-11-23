from typing import Dict, Any
import pandas as pd
import streamlit as st
from datetime import datetime
import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@st.cache_data(ttl=24*3600)  # Cache for 24 hours
def get_filtered_data(filters: Dict[str, Any]) -> pd.DataFrame:
    """
    Cached version of get_filtered_data using Streamlit's native caching
    """
    # Import MongoClient and other necessary imports here to avoid circular imports
    from pymongo import MongoClient
    
    try:
        # Connect to MongoDB
        mongo_uri = os.environ.get('MONGO_URI')        
        client = MongoClient(mongo_uri)
        if client is None:
            st.error("Failed to connect to database. Check the logs for details.")
            return

        db = client["projects"]
        collection = db["projects"]
        
        # Prepare query (same logic as in original get_filtered_data)
        query = {}
        
        # Department filter
        if filters.get('dept_name'):
            query['dept_name'] = filters['dept_name']
            
        # Sub-department filter
        if filters.get('dept_sub_name'):
            query['dept_sub_name'] = filters['dept_sub_name']

        # Date range filter
        if filters.get('date_start') and filters.get('date_end'):
            start_date = datetime.combine(filters['date_start'], datetime.min.time())
            end_date = datetime.combine(filters['date_end'], datetime.max.time())
            query['transaction_date'] = {
                "$gte": start_date,
                "$lte": end_date
            }

        # Price range filter
        if filters.get('price_start') is not None or filters.get('price_end') is not None:
            price_query = {}
            
            if filters.get('price_start') is not None:
                price_query["$gte"] = filters['price_start'] * 1e6
                
            if filters.get('price_end') is not None:
                price_query["$lte"] = filters['price_end'] * 1e6
                
            if price_query:
                query["sum_price_agree"] = price_query

        # Log query details
        logger.info(f"MongoDB Query: {query}")

        # Create a cursor and track the transferred data
        class SizeTrackingCursor:
            def __init__(self, cursor):
                self.cursor = cursor
                self.bytes_transferred = 0

            def __iter__(self):
                return self

            def __next__(self):
                item = next(self.cursor)
                # Estimate item size (crude approximation)
                item_size = sys.getsizeof(item)
                self.bytes_transferred += item_size
                return item

        # Fetch data with size tracking
        tracked_cursor = SizeTrackingCursor(collection.find(query))
        data = list(tracked_cursor)
        
        # Log bytes transferred from MongoDB
        logger.info(f"Bytes transferred from MongoDB: {tracked_cursor.bytes_transferred:,} bytes")

        if not data:
            logger.warning("No data found for the given query")
            return pd.DataFrame()
            
        df = pd.DataFrame(data)
        
        # Log DataFrame size
        df_size_bytes = df.memory_usage(deep=True).sum()
        logger.info(f"DataFrame total size: {df_size_bytes:,} bytes")
        logger.info(f"DataFrame row count: {len(df)}")

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
        st.error(f"Error fetching data: {str(e)}")
        return pd.DataFrame()
    finally:
        client.close()