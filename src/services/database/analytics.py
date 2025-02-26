# src/services/database/analytics.py

from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime
import logging
from .mongodb import MongoDBService, retry_on_connection_error

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service for analytics-specific database operations"""
    
    def __init__(self):
        self.mongo = MongoDBService()
    
    @retry_on_connection_error()
    def get_company_summary(self) -> pd.DataFrame:
        """Get company summary with analytics metrics"""
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": "$winner",
                        "project_count": {"$sum": 1},
                        "total_value": {"$sum": "$sum_price_agree"},
                        "departments": {"$addToSet": "$dept_name"},
                        "first_project": {"$min": "$transaction_date"},
                        "last_project": {"$max": "$transaction_date"}
                    }
                },
                {
                    "$project": {
                        "winner": "$_id",
                        "project_count": 1,
                        "total_value": 1,
                        "avg_project_value": {"$divide": ["$total_value", "$project_count"]},
                        "department_count": {"$size": "$departments"},
                        "active_years": {
                            "$dateDiff": {
                                "startDate": "$first_project",
                                "endDate": "$last_project",
                                "unit": "year"
                            }
                        }
                    }
                }
            ]
            
            collection = self.mongo.get_collection("projects")
            results = list(collection.aggregate(pipeline))
            return pd.DataFrame(results)
            
        except Exception as e:
            logger.error(f"Error getting company summary: {e}")
            return pd.DataFrame()
    
    @retry_on_connection_error()
    def get_department_metrics(self) -> pd.DataFrame:
        """Get department metrics for analytics"""
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": "$dept_name",
                        "project_count": {"$sum": 1},
                        "total_value": {"$sum": "$sum_price_agree"},
                        "companies": {"$addToSet": "$winner"},
                        "avg_project_value": {"$avg": "$sum_price_agree"}
                    }
                },
                {
                    "$project": {
                        "department": "$_id",
                        "project_count": 1,
                        "total_value": 1,
                        "avg_project_value": 1,
                        "company_count": {"$size": "$companies"}
                    }
                }
            ]
            
            collection = self.mongo.get_collection("projects")
            results = list(collection.aggregate(pipeline))
            return pd.DataFrame(results)
            
        except Exception as e:
            logger.error(f"Error getting department metrics: {e}")
            return pd.DataFrame() 