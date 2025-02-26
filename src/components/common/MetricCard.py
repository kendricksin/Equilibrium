# src/components/layout/MetricCard.py

import streamlit as st
from typing import Optional, Callable, Any

class MetricCard:
    """
    A card component for displaying metrics with formatting options
    """
    def __init__(
        self,
        title: str,
        value: Any,
        prefix: str = "",
        suffix: str = "",
        formatter: Optional[Callable[[Any], str]] = None,
        help_text: Optional[str] = None,
        delta: Optional[Any] = None,
        delta_formatter: Optional[Callable[[Any], str]] = None,
        color: Optional[str] = None
    ):
        """
        Initialize a metric card
        
        Args:
            title: Title of the metric
            value: Value to display
            prefix: Prefix to add before the value
            suffix: Suffix to add after the value
            formatter: Function to format the value
            help_text: Tooltip text
            delta: Delta value to display
            delta_formatter: Function to format the delta value
            color: Visual color indicator ("success", "danger", "warning", or None)
        """
        self.title = title
        self.value = value
        self.prefix = prefix
        self.suffix = suffix
        self.formatter = formatter or (lambda x: str(x))
        self.help_text = help_text
        self.delta = delta
        self.delta_formatter = delta_formatter or (lambda x: str(x))
        self.color = color
    
    def render(self):
        """Render the metric card in Streamlit"""
        # Format the value
        formatted_value = self.formatter(self.value)
        display_value = f"{self.prefix}{formatted_value}{self.suffix}"
        
        # Calculate delta and delta_color
        delta_value = None
        delta_color = "normal"
        
        if self.delta is not None:
            delta_value = f"{self.delta_formatter(self.delta)}"
            
            # If color is specified, use it to determine delta_color
            if self.color == "success":
                delta_color = "normal"  # Green color
            elif self.color == "danger":
                delta_color = "inverse"  # Red color
            elif self.color == "warning":
                delta_color = "off"      # Yellow/orange color
        
        # Display the metric
        st.metric(
            label=self.title,
            value=display_value,
            delta=delta_value,
            delta_color=delta_color,
            help=self.help_text
        )
        
        # Optional: Add colored indicator using custom HTML if needed
        if self.color and not self.delta:
            color_map = {
                "success": "green",
                "danger": "red",
                "warning": "orange",
                "info": "blue"
            }
            html_color = color_map.get(self.color)
            if html_color:
                st.markdown(f"<div style='height:3px;background-color:{html_color};margin-top:-15px;'></div>", 
                           unsafe_allow_html=True)

# Factory methods that use the 'color' parameter instead of 'color_scheme'
def create_success_metric(title, value, **kwargs):
    """Factory method for success metrics (green)"""
    return MetricCard(
        title=title,
        value=value,
        color="success",
        **kwargs
    )

def create_danger_metric(title, value, **kwargs):
    """Factory method for danger metrics (red)"""
    return MetricCard(
        title=title,
        value=value,
        color="danger",
        **kwargs
    )

def create_warning_metric(title, value, **kwargs):
    """Factory method for warning metrics (yellow)"""
    return MetricCard(
        title=title,
        value=value,
        color="warning",
        **kwargs
    )

def create_info_metric(title, value, **kwargs):
    """Factory method for info metrics (blue)"""
    return MetricCard(
        title=title,
        value=value,
        color="info",
        **kwargs
    )