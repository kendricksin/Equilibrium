# src/utils/formatters.py

from typing import Union, Optional
from datetime import datetime
import locale
import logging

logger = logging.getLogger(__name__)

class Formatters:
    """Utility class for formatting data values"""
    
    @staticmethod
    def format_currency(
        value: Union[int, float],
        currency: str = "THB",
        precision: int = 2
    ) -> str:
        """
        Format number as currency
        
        Args:
            value: Number to format
            currency: Currency code
            precision: Decimal precision
            
        Returns:
            Formatted currency string
        """
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
            formatted = locale.currency(
                value,
                grouping=True,
                symbol=currency,
                international=True
            )
            return formatted
        except Exception as e:
            logger.error(f"Error formatting currency: {e}")
            return f"{currency} {value:,.{precision}f}"
    
    @staticmethod
    def format_percentage(
        value: float,
        precision: int = 1
    ) -> str:
        """
        Format number as percentage
        
        Args:
            value: Number to format (0-100)
            precision: Decimal precision
            
        Returns:
            Formatted percentage string
        """
        try:
            return f"{value:.{precision}f}%"
        except Exception as e:
            logger.error(f"Error formatting percentage: {e}")
            return f"{value}%"
    
    @staticmethod
    def format_date(
        date: datetime,
        format_string: str = "%Y-%m-%d"
    ) -> str:
        """
        Format datetime object
        
        Args:
            date: Datetime to format
            format_string: Date format string
            
        Returns:
            Formatted date string
        """
        try:
            return date.strftime(format_string)
        except Exception as e:
            logger.error(f"Error formatting date: {e}")
            return str(date)
    
    @staticmethod
    def format_number(
        value: Union[int, float],
        precision: int = 0,
        use_thousands: bool = True
    ) -> str:
        """
        Format number with thousands separator
        
        Args:
            value: Number to format
            precision: Decimal precision
            use_thousands: Whether to use thousands separator
            
        Returns:
            Formatted number string
        """
        try:
            if use_thousands:
                return f"{value:,.{precision}f}"
            return f"{value:.{precision}f}"
        except Exception as e:
            logger.error(f"Error formatting number: {e}")
            return str(value) 