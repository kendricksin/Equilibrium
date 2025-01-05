# src/services/database/company_indexing.py

import logging
from typing import Dict, Any, List
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING, UpdateOne
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import BulkWriteError

logger = logging.getLogger(__name__)

class CompanyIndexingService:
    """Service for creating and managing company indexes"""
    
    def __init__(self, db: Database):
        self.db = db
        self.companies_collection = "companies"
        self._setup_collection()
    
    def _setup_collection(self):
        """Setup companies collection with appropriate indexes"""
        try:
            # Create collection if it doesn't exist
            if self.companies_collection not in self.db.list_collection_names():
                self.db.create_collection(self.companies_collection)
            
            # Drop existing indexes
            self.db[self.companies_collection].drop_indexes()
            
            # Create compound unique index on winner_tin and winner
            # This ensures we can't have duplicates even if TIN is missing
            self.db[self.companies_collection].create_index(
                [
                    ("winner_tin", ASCENDING),
                    ("winner", ASCENDING)
                ],
                unique=True,
                sparse=True  # Allow documents where winner_tin might be missing
            )
            
            # Additional indexes for performance
            self.db[self.companies_collection].create_index([("total_value", DESCENDING)])
            self.db[self.companies_collection].create_index([("project_count", DESCENDING)])
            
            logger.info("Company collection and indexes setup complete")
            
        except Exception as e:
            logger.error(f"Error setting up company collection: {e}")
            raise

    def get_top_companies(
        self,
        sort_by: str = "total_value",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top companies by specified metric"""
        try:
            return list(
                self.db[self.companies_collection]
                .find({}, {"_id": 0})
                .sort(sort_by, DESCENDING)
                .limit(limit)
            )
        except Exception as e:
            logger.error(f"Error getting top companies: {e}")
            return []

    def _normalize_tin(self, tin: Any) -> str:
        """Normalize TIN format to string, stripping leading zeros"""
        if tin is None:
            return None
        # Convert to string and remove leading zeros
        return str(tin).lstrip("0") if str(tin).strip() else None
    
    def build_company_index(self, force_refresh: bool = False) -> bool:
        """Build or update the company index"""
        try:
            if force_refresh:
                self.db[self.companies_collection].drop()
                self._setup_collection()
            
            # Initial grouping pipeline
            pipeline = [
                # Clean and normalize winner_tin
                {
                    "$addFields": {
                        "normalized_tin": {
                            "$cond": [
                                {"$eq": [{"$type": "$winner_tin"}, "string"]},
                                {"$ltrim": {"input": "$winner_tin", "chars": "0"}},
                                {"$toString": "$winner_tin"}
                            ]
                        }
                    }
                },
                # Group by winner and normalized TIN
                {
                    "$group": {
                        "_id": {
                            "winner": "$winner",
                            "winner_tin": "$normalized_tin"
                        },
                        "project_ids": {"$addToSet": "$project_id"},
                        "total_value": {"$sum": "$sum_price_agree"},
                        "first_project": {"$min": "$transaction_date"},
                        "latest_project": {"$max": "$transaction_date"},
                        "departments": {"$addToSet": "$dept_name"},
                        "yearly_stats": {
                            "$push": {
                                "year": {"$year": "$transaction_date"},
                                "value": "$sum_price_agree"
                            }
                        }
                    }
                },
                # Calculate yearly summaries
                {
                    "$addFields": {
                        "yearly_stats": {
                            "$map": {
                                "input": {
                                    "$setUnion": {
                                        "$map": {
                                            "input": "$yearly_stats",
                                            "as": "stat",
                                            "in": "$$stat.year"
                                        }
                                    }
                                },
                                "as": "year",
                                "in": {
                                    "year": "$$year",
                                    "value": {
                                        "$reduce": {
                                            "input": {
                                                "$filter": {
                                                    "input": "$yearly_stats",
                                                    "cond": {"$eq": ["$$this.year", "$$year"]}
                                                }
                                            },
                                            "initialValue": 0,
                                            "in": {"$add": ["$$value", "$$this.value"]}
                                        }
                                    },
                                    "projects": {
                                        "$size": {
                                            "$filter": {
                                                "input": "$yearly_stats",
                                                "cond": {"$eq": ["$$this.year", "$$year"]}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                # Final document structure
                {
                    "$project": {
                        "_id": 0,
                        "winner": "$_id.winner",
                        "winner_tin": "$_id.winner_tin",
                        "project_ids": 1,
                        "total_value": 1,
                        "project_count": {"$size": "$project_ids"},
                        "avg_project_value": {"$divide": ["$total_value", {"$size": "$project_ids"}]},
                        "first_project": 1,
                        "latest_project": 1,
                        "active_years": {"$size": {"$setUnion": {"$map": {"input": "$yearly_stats", "in": "$$this.year"}}}},
                        "departments": 1,
                        "yearly_stats": 1,
                        "last_updated": {"$literal": datetime.now()}
                    }
                }
            ]

            # Execute aggregation
            company_data = list(self.db.projects.aggregate(pipeline))
            
            if not company_data:
                logger.warning("No company data found")
                return False
            
            # Create bulk operations
            operations = []
            for company in company_data:
                operations.append(
                    UpdateOne(
                        {
                            "winner": company["winner"],
                            "winner_tin": company["winner_tin"]
                        },
                        {"$set": company},
                        upsert=True
                    )
                )
            
            # Execute in batches
            batch_size = 500
            for i in range(0, len(operations), batch_size):
                batch = operations[i:i + batch_size]
                self.db[self.companies_collection].bulk_write(batch)
                logger.info(f"Processed batch of {len(batch)} companies")
            
            logger.info(f"Successfully indexed {len(company_data)} companies")
            return True
            
        except BulkWriteError as bwe:
            logger.error(f"Bulk write error: {bwe.details}")
            return False
        except Exception as e:
            logger.error(f"Error building company index: {e}")
            return False

def main():
    """Main function for direct script execution"""
    import os
    from dotenv import load_dotenv
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
        
        # Connect to MongoDB
        client = MongoClient(mongo_uri)
        db = client[db_name]
        
        # Create indexing service
        indexing_service = CompanyIndexingService(db)
        
        # Build company index with force refresh
        logger.info("Starting company indexing...")
        success = indexing_service.build_company_index(force_refresh=True)
        
        if success:
            # Verify results
            top_companies = indexing_service.get_top_companies(limit=5)
            logger.info("\nTop 5 companies by total value:")
            for company in top_companies:
                logger.info(
                    f"- {company['winner']}: "
                    f"฿{company['total_value']/1e6:.2f}M "
                    f"({company['project_count']} projects)"
                )
        else:
            logger.error("Failed to build company index")
        
    except Exception as e:
        logger.error(f"Error in indexing process: {e}")
        raise
    finally:
        if 'client' in locals():
            client.close()
            logger.info("MongoDB connection closed")

if __name__ == "__main__":
    main()