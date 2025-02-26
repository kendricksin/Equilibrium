# src/analytics/projects/filters.py

from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ProjectFilters:
    """Service for filtering project data"""
    
    @staticmethod
    def apply_filters(
        df: pd.DataFrame,
        filters: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        Apply filters to project DataFrame
        
        Args:
            df: Project DataFrame
            filters: Dictionary of filters to apply
            
        Returns:
            Filtered DataFrame
        """
        try:
            filtered_df = df.copy()
            
            # Department filter
            if filters.get('dept_name'):
                filtered_df = filtered_df[
                    filtered_df['dept_name'] == filters['dept_name']
                ]
            
            # Date range filter
            if filters.get('date_start') and filters.get('date_end'):
                filtered_df = filtered_df[
                    (filtered_df['transaction_date'] >= filters['date_start']) &
                    (filtered_df['transaction_date'] <= filters['date_end'])
                ]
            
            # Value range filter
            if filters.get('min_value'):
                filtered_df = filtered_df[
                    filtered_df['sum_price_agree'] >= filters['min_value']
                ]
            if filters.get('max_value'):
                filtered_df = filtered_df[
                    filtered_df['sum_price_agree'] <= filters['max_value']
                ]
            
            # Company filter
            if filters.get('companies'):
                filtered_df = filtered_df[
                    filtered_df['winner'].isin(filters['companies'])
                ]
            
            return filtered_df
            
        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            return df
    
    @staticmethod
    def build_mongo_query(filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build MongoDB query from filters
        
        Args:
            filters: Dictionary of filters
            
        Returns:
            MongoDB query dictionary
        """
        try:
            query = {}
            
            if filters.get('dept_name'):
                query['dept_name'] = filters['dept_name']
                
            if filters.get('date_start') and filters.get('date_end'):
                query['transaction_date'] = {
                    '$gte': filters['date_start'],
                    '$lte': filters['date_end']
                }
                
            if filters.get('min_value') or filters.get('max_value'):
                query['sum_price_agree'] = {}
                if filters.get('min_value'):
                    query['sum_price_agree']['$gte'] = filters['min_value']
                if filters.get('max_value'):
                    query['sum_price_agree']['$lte'] = filters['max_value']
                    
            if filters.get('companies'):
                query['winner'] = {'$in': filters['companies']}
                
            return query
            
        except Exception as e:
            logger.error(f"Error building MongoDB query: {e}")
            return {} 