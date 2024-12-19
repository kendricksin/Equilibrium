# test_mongodb.py

import os
from pymongo import MongoClient
from dotenv import load_dotenv
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_mongodb_connection():
    """Test MongoDB connection and check collections"""
    try:
        # Load environment variables
        load_dotenv()
        mongo_uri = os.getenv("MONGO_URI")
        db_name = os.getenv("MONGO_DB")
        
        logger.info(f"Testing connection to database: {db_name}")
        
        # Connect to MongoDB
        client = MongoClient(mongo_uri)
        db = client[db_name]
        
        # Test connection
        client.admin.command('ismaster')
        logger.info("Successfully connected to MongoDB")
        
        # List all collections
        collections = db.list_collection_names()
        logger.info(f"Available collections: {collections}")
        
        # Check for department_distribution specifically
        if "department_distribution" in collections:
            logger.info("Found department_distribution collection")
            
            # Get collection stats
            count = db.department_distribution.count_documents({})
            logger.info(f"Total documents in department_distribution: {count}")
            
            # Check for metadata document
            metadata = db.department_distribution.find_one({"_id": "metadata"})
            if metadata:
                logger.info("Found metadata document:")
                logger.info(f"Last updated: {metadata.get('last_updated')}")
                logger.info(f"Total projects: {metadata.get('total_projects')}")
                logger.info(f"Total value: {metadata.get('total_value')}")
            else:
                logger.warning("No metadata document found in collection")
            
            # Sample some documents
            logger.info("\nSample documents from collection:")
            for doc in db.department_distribution.find().limit(3):
                logger.info(doc)
        else:
            logger.error("department_distribution collection not found!")
        
    except Exception as e:
        logger.error(f"Error testing MongoDB connection: {e}")
    finally:
        if 'client' in locals():
            client.close()
            logger.info("MongoDB connection closed")

if __name__ == "__main__":
    test_mongodb_connection()