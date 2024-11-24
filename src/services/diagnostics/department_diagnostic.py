# src/services/diagnostics/department_diagnostic.py

import logging
from typing import Dict, Any, List
import pandas as pd
from services.database.mongodb import MongoDBService
from services.cache.department_cache import get_departments, get_sub_departments

logger = logging.getLogger(__name__)

class DepartmentDiagnostic:
    """Diagnostic tool for department-related services"""
    
    @staticmethod
    def run_diagnostics() -> Dict[str, Any]:
        """
        Run comprehensive diagnostics on department services
        
        Returns:
            Dict[str, Any]: Diagnostic results
        """
        results = {
            'mongo_connection': False,
            'departments_count': 0,
            'cache_status': False,
            'errors': []
        }
        
        # Test MongoDB Connection
        try:
            with MongoDBService() as db:
                # Test basic connection
                db.client.admin.command('ismaster')
                results['mongo_connection'] = True
                
                # Test collection access
                collection = db.get_collection('projects')
                
                # Get raw department count
                dept_count = len(collection.distinct("dept_name"))
                results['departments_count'] = dept_count
                
                if dept_count == 0:
                    results['errors'].append("No departments found in database")
                
                # Sample data check
                sample = list(collection.find().limit(1))
                if not sample:
                    results['errors'].append("No documents found in projects collection")
                else:
                    # Check department field existence
                    if 'dept_name' not in sample[0]:
                        results['errors'].append("dept_name field missing in documents")
                
        except Exception as e:
            results['errors'].append(f"MongoDB Error: {str(e)}")
        
        # Test Cache Service
        try:
            # Try to get departments through cache
            cached_depts = get_departments(force_refresh=True)
            if cached_depts:
                results['cache_status'] = True
                
                # Verify data consistency
                if len(cached_depts) != results['departments_count']:
                    results['errors'].append(
                        f"Cache-DB mismatch: Cache has {len(cached_depts)} departments, "
                        f"DB has {results['departments_count']}"
                    )
            else:
                results['errors'].append("Cache returned empty department list")
                
        except Exception as e:
            results['errors'].append(f"Cache Error: {str(e)}")
        
        return results

    @staticmethod
    def verify_department_data() -> Dict[str, Any]:
        """
        Verify department data integrity
        
        Returns:
            Dict[str, Any]: Verification results
        """
        try:
            with MongoDBService() as db:
                collection = db.get_collection('projects')
                
                # Get all documents with department info
                pipeline = [
                    {
                        "$group": {
                            "_id": "$dept_name",
                            "count": {"$sum": 1},
                            "sub_departments": {"$addToSet": "$dept_sub_name"}
                        }
                    }
                ]
                
                dept_stats = list(collection.aggregate(pipeline))
                
                return {
                    "total_departments": len(dept_stats),
                    "department_details": [
                        {
                            "name": stat["_id"],
                            "project_count": stat["count"],
                            "sub_department_count": len(stat["sub_departments"]),
                            "has_empty_values": None in stat["sub_departments"]
                        }
                        for stat in dept_stats
                    ],
                    "departments_with_data": sum(1 for stat in dept_stats if stat["_id"] is not None),
                    "empty_department_count": sum(1 for stat in dept_stats if stat["_id"] is None)
                }
                
        except Exception as e:
            logger.error(f"Error verifying department data: {e}")
            return {"error": str(e)}

# Utility function for quick diagnostics
def run_quick_diagnostic() -> None:
    """Run and print quick diagnostic results"""
    try:
        print("\n=== Department Service Diagnostic Results ===\n")
        
        results = DepartmentDiagnostic.run_diagnostics()
        
        print(f"MongoDB Connection: {'✅' if results['mongo_connection'] else '❌'}")
        print(f"Departments Found: {results['departments_count']}")
        print(f"Cache Service: {'✅' if results['cache_status'] else '❌'}")
        
        if results['errors']:
            print("\nErrors Found:")
            for error in results['errors']:
                print(f"❌ {error}")
        else:
            print("\n✅ No errors found")
            
        # Run data verification
        print("\n=== Department Data Verification ===\n")
        verification = DepartmentDiagnostic.verify_department_data()
        
        if "error" not in verification:
            print(f"Total Departments: {verification['total_departments']}")
            print(f"Departments with Data: {verification['departments_with_data']}")
            print(f"Empty Department Records: {verification['empty_department_count']}")
            
            print("\nDepartment Details:")
            for dept in verification['department_details']:
                print(f"\n{dept['name'] or 'EMPTY'}")
                print(f"  Projects: {dept['project_count']}")
                print(f"  Sub-departments: {dept['sub_department_count']}")
                if dept['has_empty_values']:
                    print("  ⚠️ Contains empty sub-department values")
        else:
            print(f"❌ Verification Error: {verification['error']}")
        
    except Exception as e:
        print(f"\n❌ Diagnostic Error: {e}")

if __name__ == "__main__":
    run_quick_diagnostic()