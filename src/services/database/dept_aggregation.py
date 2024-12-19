# src/services/database/dept_aggregation.py

import logging
from typing import Dict, Any
from pymongo.database import Database
from datetime import datetime

logger = logging.getLogger(__name__)

class DepartmentAggregationService:
    """Service for creating and managing department distribution aggregation"""
    
    def __init__(self, db: Database):
        self.db = db
        self.collection_name = "department_distribution"
    
    def create_aggregation(self, force_refresh: bool = False) -> bool:
        """Create or update the department distribution aggregation"""
        try:
            if not force_refresh and self.collection_name in self.db.list_collection_names():
                logger.info("Aggregation collection already exists")
                return True
            
            logger.info("Creating enhanced department aggregation...")
            
            # Drop existing collection if forcing refresh
            if force_refresh and self.collection_name in self.db.list_collection_names():
                self.db[self.collection_name].drop()
            
            # Calculate total project value and count
            totals_pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_value": {"$sum": "$price_build"},
                        "total_count": {"$sum": 1},
                        "unique_departments": {"$addToSet": "$dept_name"},
                        "unique_companies": {"$addToSet": "$winner"}
                    }
                }
            ]
            
            totals = self.db.projects.aggregate(totals_pipeline).next()
            
            # Create annual totals pipeline
            annual_totals_pipeline = [
                {
                    "$group": {
                        "_id": {"$year": "$transaction_date"},
                        "annual_value": {"$sum": "$price_build"},
                        "annual_count": {"$sum": 1}
                    }
                }
            ]
            
            annual_totals = {
                str(doc["_id"]): {
                    "value": doc["annual_value"],
                    "count": doc["annual_count"]
                }
                for doc in self.db.projects.aggregate(annual_totals_pipeline)
            }
            
            # Save totals document
            self.db[self.collection_name].insert_one({
                "_id": "totals",
                "total_value": totals["total_value"],
                "total_count": totals["total_count"],
                "unique_departments": len(totals["unique_departments"]),
                "unique_companies": len(totals["unique_companies"]),
                "annual_totals": annual_totals,
                "last_updated": datetime.now()
            })
            
            # Main aggregation pipeline
            pipeline = [
                # First group to get department level stats
                {
                    "$group": {
                        "_id": {
                            "dept": "$dept_name",
                            "subdept": "$dept_sub_name",
                            "year": {"$year": "$transaction_date"}
                        },
                        "year_count": {"$sum": 1},
                        "year_value": {"$sum": "$price_build"},
                        "companies": {"$addToSet": "$winner"}
                    }
                },
                # Second group to consolidate yearly stats
                {
                    "$group": {
                        "_id": {
                            "dept": "$_id.dept",
                            "subdept": "$_id.subdept"
                        },
                        "total_count": {"$sum": "$year_count"},
                        "total_value": {"$sum": "$year_value"},
                        "yearly_stats": {
                            "$push": {
                                "year": "$_id.year",
                                "count": "$year_count",
                                "value": "$year_value"
                            }
                        },
                        "all_companies": {"$addToSet": "$companies"}
                    }
                },
                # Project final format
                {
                    "$project": {
                        "_id": 1,
                        "count": "$total_count",
                        "total_value": "$total_value",
                        "count_percentage": {
                            "$multiply": [
                                {"$divide": ["$total_count", totals["total_count"]]},
                                100
                            ]
                        },
                        "value_percentage": {
                            "$multiply": [
                                {"$divide": ["$total_value", totals["total_value"]]},
                                100
                            ]
                        },
                        "unique_companies": {"$size": {"$reduce": {
                            "input": "$all_companies",
                            "initialValue": [],
                            "in": {"$setUnion": ["$$value", "$$this"]}
                        }}},
                        "yearly_stats": 1
                    }
                }
            ]
            
            # Execute aggregation with $merge stage
            pipeline.append({
                "$merge": {
                    "into": self.collection_name,
                    "whenMatched": "replace",
                    "whenNotMatched": "insert"
                }
            })
            
            self.db.projects.aggregate(pipeline)
            
            logger.info("Successfully created department aggregation")
            return True
            
        except Exception as e:
            logger.error(f"Error creating department aggregation: {e}")
            raise
    
    def get_totals(self) -> Dict[str, Any]:
        """Get aggregated totals"""
        try:
            return self.db[self.collection_name].find_one({"_id": "totals"})
        except Exception as e:
            logger.error(f"Error getting totals: {e}")
            raise
    
    def get_department_stats(self, dept_name: str = None) -> Dict[str, Any]:
        """Get statistics for a specific department or all departments"""
        try:
            query = {}
            if dept_name:
                query = {"_id.dept": dept_name}
            
            stats = list(self.db[self.collection_name].find(
                query,
                {"_id": 0, "yearly_stats": 0}  # Exclude yearly stats unless needed
            ))
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting department stats: {e}")
            raise
    
    def get_annual_trends(self, dept_name: str = None) -> Dict[str, Any]:
        """Get annual trends for a department or overall"""
        try:
            if dept_name:
                return self.db[self.collection_name].find_one(
                    {"_id.dept": dept_name},
                    {"_id": 0, "yearly_stats": 1}
                )
            else:
                return self.db[self.collection_name].find_one(
                    {"_id": "totals"},
                    {"_id": 0, "annual_totals": 1}
                )
        except Exception as e:
            logger.error(f"Error getting annual trends: {e}")
            raise

def main():
    """Main function for direct script execution"""
    import os
    from dotenv import load_dotenv
    from pymongo import MongoClient
    import logging
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        # Load environment variables
        load_dotenv()
        mongo_uri = os.getenv('MONGO_URI')
        if not mongo_uri:
            raise ValueError("MONGO_URI environment variable not set")
            
        db_name = os.getenv('MONGO_DB', 'projects')
        
        logger.info(f"Connecting to database: {db_name}")
        
        # Connect to MongoDB
        client = MongoClient(mongo_uri)
        db = client[db_name]
        
        # Create aggregation service
        aggregation_service = DepartmentAggregationService(db)
        
        # Run aggregation with force refresh
        logger.info("Starting department aggregation...")
        aggregation_service.create_aggregation(force_refresh=True)
        
        # Verify results
        totals = aggregation_service.get_totals()
        logger.info(f"Aggregation completed successfully:")
        logger.info(f"Total projects: {totals['total_count']:,}")
        logger.info(f"Total value: ฿{totals['total_value']/1e6:,.2f}M")
        logger.info(f"Unique departments: {totals['unique_departments']:,}")
        logger.info(f"Unique companies: {totals['unique_companies']:,}")
        logger.info(f"Last updated: {totals['last_updated']}")
        
    except Exception as e:
        logger.error(f"Error in aggregation process: {e}")
        raise
    finally:
        if 'client' in locals():
            client.close()
            logger.info("MongoDB connection closed")

if __name__ == "__main__":
    main()