# src/utils/validators.py

from typing import Any, Optional, List, Dict
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)

class Validators:
    """Utility class for input validation"""
    
    @staticmethod
    def validate_date_range(
        start_date: datetime,
        end_date: datetime
    ) -> bool:
        """
        Validate date range
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if not isinstance(start_date, datetime) or not isinstance(end_date, datetime):
                return False
            return start_date <= end_date
        except Exception as e:
            logger.error(f"Error validating date range: {e}")
            return False
    
    @staticmethod
    def validate_numeric_range(
        min_value: Optional[float],
        max_value: Optional[float]
    ) -> bool:
        """
        Validate numeric range
        
        Args:
            min_value: Minimum value
            max_value: Maximum value
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if min_value is None or max_value is None:
                return True
            return min_value <= max_value
        except Exception as e:
            logger.error(f"Error validating numeric range: {e}")
            return False
    
    @staticmethod
    def validate_tin(tin: str) -> bool:
        """
        Validate Tax ID Number format
        
        Args:
            tin: Tax ID Number to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Thai Tax ID format: 13 digits
            if not tin or not isinstance(tin, str):
                return False
            return bool(re.match(r'^\d{13}$', tin))
        except Exception as e:
            logger.error(f"Error validating TIN: {e}")
            return False
    
    @staticmethod
    def validate_filters(filters: Dict[str, Any]) -> Dict[str, str]:
        """
        Validate filter parameters
        
        Args:
            filters: Dictionary of filters to validate
            
        Returns:
            Dictionary of validation errors (empty if all valid)
        """
        errors = {}
        
        try:
            # Date range validation
            if filters.get('date_start') and filters.get('date_end'):
                if not Validators.validate_date_range(
                    filters['date_start'],
                    filters['date_end']
                ):
                    errors['date_range'] = "Invalid date range"
            
            # Value range validation
            if filters.get('min_value') is not None and filters.get('max_value') is not None:
                if not Validators.validate_numeric_range(
                    filters['min_value'],
                    filters['max_value']
                ):
                    errors['value_range'] = "Invalid value range"
            
            # List length validation
            if filters.get('companies'):
                if not isinstance(filters['companies'], list):
                    errors['companies'] = "Companies must be a list"
                elif len(filters['companies']) > 10:
                    errors['companies'] = "Maximum 10 companies allowed"
            
            return errors
            
        except Exception as e:
            logger.error(f"Error validating filters: {e}")
            return {"general": "Error validating filters"} 