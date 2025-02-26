# src/components/common/LoadingState.py

import streamlit as st
from typing import Optional, Callable, Any
import time
import logging

logger = logging.getLogger(__name__)

class LoadingState:
    """Reusable loading state component"""
    
    def __init__(
        self,
        message: str = "Loading...",
        spinner: str = "dots"
    ):
        """
        Initialize LoadingState
        
        Args:
            message: Loading message to display
            spinner: Streamlit spinner type
        """
        self.message = message
        self.spinner = spinner
    
    def __enter__(self):
        """Start loading state"""
        self.placeholder = st.empty()
        with self.placeholder:
            with st.spinner(self.message):
                return self.placeholder
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End loading state"""
        self.placeholder.empty()
    
    @staticmethod
    def with_loading(
        func: Callable,
        message: str = "Loading...",
        error_message: str = "An error occurred",
        **kwargs
    ) -> Any:
        """
        Execute function with loading state
        
        Args:
            func: Function to execute
            message: Loading message
            error_message: Error message on failure
            **kwargs: Arguments to pass to function
            
        Returns:
            Function result
        """
        try:
            with LoadingState(message):
                return func(**kwargs)
        except Exception as e:
            logger.error(f"Error in loading state: {e}")
            st.error(error_message)
            return None

# Usage examples:
"""
# Basic usage with context manager
with LoadingState("Loading data..."):
    time.sleep(2)  # Simulate work
    df = load_data()

# Function wrapper usage
result = LoadingState.with_loading(
    func=process_data,
    message="Processing...",
    error_message="Error processing data",
    data=some_data
)
""" 