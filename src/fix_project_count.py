# src/scripts/fix_company_counts.py

import logging
from services.database.mongodb import MongoDBService

logger = logging.getLogger(__name__)

def fix_company_project_counts():
    """Update company collection with accurate project counts"""
    mongo = MongoDBService()
    
    try:
        # Get actual project counts from projects collection
        projects_collection = mongo.get_collection("projects")
        companies_collection = mongo.get_collection("companies")
        
        # Get actual counts using aggregation
        actual_counts = list(projects_collection.aggregate([
            {
                "$group": {
                    "_id": "$winner",
                    "count": {"$sum": 1},
                    "project_ids": {"$push": "$project_id"}
                }
            }
        ]))
        
        logger.info(f"Processing {len(actual_counts)} companies")
        
        # Update each company document
        for company_data in actual_counts:
            company_name = company_data["_id"]
            actual_count = company_data["count"]
            project_ids = company_data["project_ids"]
            
            # Update company document
            result = companies_collection.update_one(
                {"winner": company_name},
                {
                    "$set": {
                        "project_count": actual_count,
                        "project_ids": project_ids
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(
                    f"Updated {company_name}: set count to {actual_count} "
                    f"with {len(project_ids)} project IDs"
                )
            
        logger.info("Company project count cleanup completed")
        
    except Exception as e:
        logger.error(f"Error fixing company counts: {e}")
        raise
    finally:
        mongo.disconnect()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fix_company_project_counts()