# src/components/common/MetricCard.py

import streamlit as st
from typing import Any, Optional, Callable
import logging

logger = logging.getLogger(__name__)

class MetricCard:
    """Component for displaying metric cards with consistent styling"""
    
    def __init__(
        self,
        title: str,
        value: Any,
        formatter: Optional[Callable] = None,
        help_text: Optional[str] = None,
        suffix: str = "",
        prefix: str = ""
    ):
        """
        Initialize MetricCard
        
        Args:
            title: Title of the metric
            value: Value to display
            formatter: Optional function to format the value
            help_text: Optional help text to display
            suffix: Optional suffix to append to value
            prefix: Optional prefix to prepend to value
        """
        self.title = title
        self.value = value
        self.formatter = formatter
        self.help_text = help_text
        self.suffix = suffix
        self.prefix = prefix
    
    def render(self):
        """Render the metric card"""
        try:
            # Format the value if formatter is provided
            display_value = self.value
            if self.formatter:
                try:
                    display_value = self.formatter(self.value)
                except Exception as e:
                    logger.error(f"Error formatting value: {e}")
                    display_value = str(self.value)
            
            # Add prefix/suffix if provided
            if self.prefix:
                display_value = f"{self.prefix}{display_value}"
            if self.suffix:
                display_value = f"{display_value}{self.suffix}"
            
            # Create container with border and padding
            with st.container():
                st.markdown(
                    f"""
                    <div style="
                        padding: 1rem;
                        border-radius: 0.5rem;
                        background: white;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
                        margin-bottom: 1rem;
                    ">
                        <p style="
                            color: #666;
                            font-size: 0.875rem;
                            margin-bottom: 0.5rem;
                        ">{self.title}</p>
                        <h3 style="
                            color: #1f1f1f;
                            font-size: 1.5rem;
                            margin: 0;
                        ">{display_value}</h3>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Show help text if provided
                if self.help_text:
                    st.caption(self.help_text)
                    
        except Exception as e:
            logger.error(f"Error rendering metric card: {e}")
            st.error("Error displaying metric") 