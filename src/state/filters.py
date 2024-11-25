# src/state/filters.py

from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, Any, Optional
import streamlit as st
import logging

logger = logging.getLogger(__name__)

@dataclass
class FilterState:
    """Filter state configuration"""
    dept_name: str = ''
    dept_sub_name: str = ''
    date_start: date = datetime(2022, 1, 1).date()
    date_end: date = datetime(2023, 12, 31).date()
    price_start: float = 0.0
    price_end: float = 200.0

class FilterManager:
    """Manages filter state and operations"""
    
    @staticmethod
    def get_default_filters() -> FilterState:
        """Get default filter values"""
        return FilterState()
    
    @staticmethod
    def validate_filters(filters: Dict[str, Any]) -> bool:
        """
        Validate filter values
        
        Args:
            filters (Dict[str, Any]): Filter values to validate
            
        Returns:
            bool: True if filters are valid
        """
        try:
            # Date validation
            if filters['date_start'] > filters['date_end']:
                logger.warning("Invalid date range: start date after end date")
                return False
            
            # Price validation
            if filters['price_start'] < 0 or filters['price_end'] < 0:
                logger.warning("Invalid price range: negative values")
                return False
            
            if filters['price_start'] > filters['price_end']:
                logger.warning("Invalid price range: start price greater than end price")
                return False
            
            return True
            
        except KeyError as e:
            logger.error(f"Missing required filter key: {e}")
            return False
        except Exception as e:
            logger.error(f"Filter validation error: {e}")
            return False
    
    @staticmethod
    def build_mongo_query(filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build MongoDB query from filters"""
        query = {}
        
        try:
            # Department filter
            if filters.get('dept_name'):
                query['dept_name'] = filters['dept_name']
            
            # Sub-department filter
            if filters.get('dept_sub_name'):
                query['dept_sub_name'] = filters['dept_sub_name']
            
            # Purchase method filter
            if filters.get('purchase_method_name'):
                query['purchase_method_name'] = filters['purchase_method_name']
            
            # Project type filter
            if filters.get('project_type_name'):
                query['project_type_name'] = filters['project_type_name']
            
            # Date range filter
            if filters.get('date_start') and filters.get('date_end'):
                query['transaction_date'] = {
                    "$gte": datetime.combine(filters['date_start'], datetime.min.time()),
                    "$lte": datetime.combine(filters['date_end'], datetime.max.time())
                }
            
            # Price range filter
            price_query = {}
            if filters.get('price_start') is not None:
                price_query["$gte"] = filters['price_start'] * 1e6
            if filters.get('price_end') is not None:
                price_query["$lte"] = filters['price_end'] * 1e6
            if price_query:
                query["sum_price_agree"] = price_query
            
            return query
            
        except Exception as e:
            logger.error(f"Error building MongoDB query: {e}")
            return {}
    
    @staticmethod
    def format_filter_summary(filters: Dict[str, Any]) -> str:
        """
        Create human-readable filter summary
        
        Args:
            filters (Dict[str, Any]): Filter values
            
        Returns:
            str: Formatted summary
        """
        try:
            summary_parts = []
            
            if filters.get('dept_name'):
                summary_parts.append(f"Department: {filters['dept_name']}")
                
                if filters.get('dept_sub_name'):
                    summary_parts.append(f"Sub-dept: {filters['dept_sub_name']}")
            
            if filters.get('date_start') and filters.get('date_end'):
                date_range = (
                    f"Date: {filters['date_start'].strftime('%Y-%m-%d')} to "
                    f"{filters['date_end'].strftime('%Y-%m-%d')}"
                )
                summary_parts.append(date_range)
            
            if filters.get('price_start') is not None or filters.get('price_end') is not None:
                price_range = (
                    f"Price: {filters.get('price_start', 0)}M฿ to "
                    f"{filters.get('price_end', 'unlimited')}M฿"
                )
                summary_parts.append(price_range)
            
            return " | ".join(summary_parts) if summary_parts else "No filters applied"
            
        except Exception as e:
            logger.error(f"Error formatting filter summary: {e}")
            return "Error in filter summary"