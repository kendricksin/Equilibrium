# src/components/filters/DatePriceFilter.py

import streamlit as st
from datetime import datetime, date
from typing import Tuple

def DatePriceFilter(
    current_date_start: date = datetime(2022, 1, 1).date(),
    current_date_end: date = datetime(2023, 12, 31).date(),
    current_price_start: float = 0.0,
    current_price_end: float = 200.0,
    key_prefix: str = ""
) -> Tuple[date, date, float, float]:
    """
    A component for date range and price range selection.
    
    Args:
        current_date_start (date): Current start date
        current_date_end (date): Current end date
        current_price_start (float): Current minimum price (in millions)
        current_price_end (float): Current maximum price (in millions)
        key_prefix (str): Prefix for component keys to avoid conflicts
        
    Returns:
        Tuple[date, date, float, float]: Selected date range and price range
    """
    # Date Range
    st.markdown("#### Date Range")
    date_start = st.date_input(
        "Start Date",
        value=current_date_start,
        key=f"{key_prefix}date_start"
    )
    date_end = st.date_input(
        "End Date",
        value=current_date_end,
        key=f"{key_prefix}date_end"
    )
    
    # Price Range
    st.markdown("#### Price Range (Million Baht)")
    col1, col2 = st.columns(2)
    
    with col1:
        price_start = st.number_input(
            "Minimum",
            min_value=0.0,
            max_value=10000.0,
            value=float(current_price_start),
            step=10.0,
            format="%.1f",
            key=f"{key_prefix}price_start"
        )
    
    with col2:
        price_end = st.number_input(
            "Maximum",
            min_value=0.0,
            max_value=20000.0,
            value=float(current_price_end),
            step=10.0,
            format="%.1f",
            key=f"{key_prefix}price_end"
        )
    
    return date_start, date_end, price_start, price_end