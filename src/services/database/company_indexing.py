import logging
from typing import Dict, Any, List, Set
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING, UpdateOne
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import BulkWriteError

logger = logging.getLogger(__name__)

class CompanyIndexingService:
    """Service for creating and managing company indexes with TIN normalization"""
    
    def __init__(self, db: Database):
        self.db = db
        self.companies_collection = "companies"
        self._setup_collection()
    
    def _setup_collection(self):
        """Setup companies collection with appropriate indexes"""
        try:
            # Drop the entire collection to start fresh
            if self.companies_collection in self.db.list_collection_names():
                self.db[self.companies_collection].drop()
            
            # Create new collection
            self.db.create_collection(self.companies_collection)
            
            # Create indexes
            self.db[self.companies_collection].create_index([("winner", ASCENDING)])
            self.db[self.companies_collection].create_index([("winner_tin", ASCENDING)], unique=True)
            self.db[self.companies_collection].create_index([("total_value", DESCENDING)])
            self.db[self.companies_collection].create_index([("project_count", DESCENDING)])
            
            logger.info("Company collection and indexes setup complete")
            
        except Exception as e:
            logger.error(f"Error setting up company collection: {e}")
            raise

    def _normalize_tin(self, tin: Any) -> str:
        """Normalize TIN to 13-digit string format"""
        if tin is None:
            return None
            
        # Convert to string
        tin_str = str(tin).strip()
        
        # Remove any non-digit characters
        tin_str = ''.join(filter(str.isdigit, tin_str))
        
        # Add leading zero if 12 digits
        if len(tin_str) == 12:
            tin_str = '0' + tin_str
            
        return tin_str if len(tin_str) == 13 else None

    def _find_related_tins(self, tin: str) -> Set[str]:
        """Find all related TINs (12 and 13 digit versions)"""
        related_tins = {tin}
        
        if len(tin) == 13 and tin.startswith('0'):
            # Add 12-digit version
            related_tins.add(tin[1:])
        elif len(tin) == 12:
            # Add 13-digit version
            related_tins.add('0' + tin)
            
        return related_tins

    def _repair_project_tins(self) -> Dict[str, int]:
        """Repair all project TINs to 13-digit format with detailed progress logging"""
        stats = {
            'total_tins': 0,
            'checked': 0,
            'updated': 0,
            'docs_updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        try:
            # Find all distinct TINs
            all_tins = list(self.db.projects.distinct('winner_tin'))
            stats['total_tins'] = len(all_tins)
            logger.info(f"Found {stats['total_tins']} distinct TINs to process")
            
            # Process each TIN
            last_log_time = datetime.now()
            log_interval = 5  # seconds
            
            for idx, tin in enumerate(all_tins, 1):
                try:
                    stats['checked'] += 1
                    current_time = datetime.now()
                    
                    # Log progress every few seconds
                    if (current_time - last_log_time).total_seconds() >= log_interval:
                        progress = (idx / stats['total_tins']) * 100
                        logger.info(f"Progress: {progress:.1f}% ({idx}/{stats['total_tins']} TINs)")
                        logger.info(f"Stats so far - Updated: {stats['updated']}, Docs Updated: {stats['docs_updated']}, Skipped: {stats['skipped']}, Errors: {stats['errors']}")
                        last_log_time = current_time
                    
                    # Skip None values
                    if tin is None:
                        stats['skipped'] += 1
                        continue
                        
                    normalized_tin = self._normalize_tin(tin)
                    
                    # Log the normalization for debugging
                    logger.debug(f"TIN: {tin} -> Normalized: {normalized_tin}")
                    
                    if normalized_tin and normalized_tin != str(tin):
                        # Count documents before update
                        doc_count = self.db.projects.count_documents({'winner_tin': tin})
                        logger.debug(f"Found {doc_count} documents with TIN: {tin}")
                        
                        # Update all documents with this TIN
                        result = self.db.projects.update_many(
                            {'winner_tin': tin},
                            {'$set': {'winner_tin': normalized_tin}}
                        )
                        
                        modified_count = result.modified_count
                        stats['updated'] += 1
                        stats['docs_updated'] += modified_count
                        
                        logger.debug(f"Updated {modified_count} documents for TIN {tin} -> {normalized_tin}")
                    else:
                        stats['skipped'] += 1
                        
                except Exception as e:
                    logger.error(f"Error processing TIN {tin}: {e}")
                    stats['errors'] += 1
            
            # Final progress report
            logger.info("TIN repair completed!")
            logger.info(f"Final Stats:")
            logger.info(f"- Total TINs processed: {stats['checked']}/{stats['total_tins']}")
            logger.info(f"- TINs updated: {stats['updated']}")
            logger.info(f"- Documents updated: {stats['docs_updated']}")
            logger.info(f"- TINs skipped: {stats['skipped']}")
            logger.info(f"- Errors encountered: {stats['errors']}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Error repairing project TINs: {e}")
            return stats

    def build_company_index(self) -> bool:
        """Build the company index with TIN normalization"""
        try:
            # First repair all project TINs
            logger.info("Repairing project TINs...")
            repair_stats = self._repair_project_tins()
            logger.info(f"TIN repair stats: {repair_stats}")
            
            # Now build the aggregation pipeline
            pipeline = [
                # Group by normalized winner_tin
                {
                    "$group": {
                        "_id": {
                            "winner_tin": "$winner_tin",
                            "winner": "$winner"
                        },
                        "project_ids": {"$push": "$project_id"},
                        "total_value": {"$sum": "$sum_price_agree"},
                        "project_count": {"$sum": 1},
                        "first_project": {"$min": "$transaction_date"},
                        "latest_project": {"$max": "$transaction_date"},
                        "departments": {"$addToSet": "$dept_name"},
                        "yearly_stats": {
                            "$push": {
                                "year": {"$year": "$transaction_date"},
                                "value": "$sum_price_agree",
                                "project_id": "$project_id"
                            }
                        }
                    }
                },
                # Process yearly statistics
                {
                    "$addFields": {
                        "yearly_stats": {
                            "$map": {
                                "input": {
                                    "$setUnion": [
                                        {"$map": {
                                            "input": "$yearly_stats",
                                            "as": "stat",
                                            "in": "$$stat.year"
                                        }}
                                    ]
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
                        "project_count": 1,
                        "avg_project_value": {"$divide": ["$total_value", "$project_count"]},
                        "first_project": 1,
                        "latest_project": 1,
                        "active_years": {
                            "$size": {
                                "$setUnion": [
                                    {"$map": {
                                        "input": "$yearly_stats",
                                        "as": "stat",
                                        "in": "$$stat.year"
                                    }}
                                ]
                            }
                        },
                        "departments": 1,
                        "yearly_stats": 1,
                        "last_updated": {"$literal": datetime.now()}
                    }
                }
            ]
            
            # Execute aggregation pipeline
            company_data = list(self.db.projects.aggregate(pipeline))
            
            if not company_data:
                logger.warning("No company data found")
                return False
            
            # Create bulk write operations
            operations = []
            for company in company_data:
                operations.append(
                    UpdateOne(
                        {"winner_tin": company["winner_tin"]},
                        {"$set": company},
                        upsert=True
                    )
                )
            
            # Execute bulk write
            result = self.db[self.companies_collection].bulk_write(operations)
            
            logger.info(f"Successfully indexed {len(company_data)} companies")
            logger.info(f"Modified: {result.modified_count}, Upserted: {result.upserted_count}")
            return True
            
        except BulkWriteError as bwe:
            logger.error(f"Bulk write error: {bwe.details}")
            return False
        except Exception as e:
            logger.error(f"Error building company index: {e}")
            return False

def main():
    """Main function for executing the company indexing process"""
    import os
    from dotenv import load_dotenv
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
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
        
        # Initialize and run company indexing
        indexing_service = CompanyIndexingService(db)
        success = indexing_service.build_company_index()
        
        if success:
            logger.info("Company indexing completed successfully")
        else:
            logger.error("Company indexing failed")
            
    except Exception as e:
        logger.error(f"Error in company indexing process: {e}")
        raise
    finally:
        if 'client' in locals():
            client.close()
            logger.info("MongoDB connection closed")

if __name__ == "__main__":
    main()