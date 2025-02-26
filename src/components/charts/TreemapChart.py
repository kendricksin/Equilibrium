# src/components/charts/TreemapChart.py

import streamlit as st
import plotly.graph_objects as go
from typing import List, Dict, Any, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class TreemapChart:
    """Reusable treemap visualization component"""
    
    def __init__(
        self,
        data: pd.DataFrame,
        value_column: str,
        path_columns: List[str],
        title: str = "Treemap",
        height: int = 700,
        color_scheme: str = 'Blues',
        max_items: Optional[int] = None
    ):
        """
        Initialize TreemapChart
        
        Args:
            data: DataFrame containing the data
            value_column: Column name for values
            path_columns: List of column names defining the hierarchy
            title: Chart title
            height: Chart height in pixels
            color_scheme: Color scheme for the treemap
            max_items: Maximum number of items to display (None for all)
        """
        self.data = data
        self.value_column = value_column
        self.path_columns = path_columns
        self.title = title
        self.height = height
        self.color_scheme = color_scheme
        self.max_items = max_items
    
    def render(
        self,
        key: Optional[str] = None,
        use_container_width: bool = True,
        show_percentages: bool = True
    ):
        """
        Render the treemap
        
        Args:
            key: Unique key for the component
            use_container_width: Whether to use container width
            show_percentages: Whether to show percentage values
        """
        try:
            if len(self.data) == 0:
                st.warning("No data available for visualization")
                return
            
            # Limit the number of items if specified
            display_data = self.data
            if self.max_items and len(display_data) > self.max_items:
                # Sort by value column in descending order and take top N
                display_data = display_data.sort_values(
                    by=self.value_column, 
                    ascending=False
                ).head(self.max_items)
            
            # For debugging
            st.write(f"Number of items in treemap: {len(display_data)}")
            
            # Create labels and values for treemap
            labels = display_data[self.path_columns[0]].tolist()
            values = display_data[self.value_column].tolist()
            
            # For single-level treemap, all parents are empty strings
            parents = [""] * len(labels)
            
            # Create figure
            fig = go.Figure(go.Treemap(
                labels=labels,
                parents=parents,
                values=values,
                textinfo="label+value+percent parent",
                hovertemplate="<b>%{label}</b><br>Value: %{value:,.0f}<br>Percentage: %{percentRoot:.1%}<extra></extra>",
                marker=dict(
                    colorscale=self.color_scheme
                )
            ))
            
            # Update layout
            fig.update_layout(
                title=self.title,
                height=self.height,
                margin=dict(t=50, l=25, r=25, b=25)
            )
            
            # Render in Streamlit
            st.plotly_chart(
                fig,
                use_container_width=use_container_width,
                key=key
            )
            
        except Exception as e:
            logger.error(f"Error rendering treemap: {e}")
            st.error(f"Error rendering treemap visualization: {e}")
            
            # Debug information
            st.write("Debug information:")
            st.write(f"Data shape: {self.data.shape}")
            st.write(f"Path columns: {self.path_columns}")
            st.write(f"Value column: {self.value_column}")
            if len(self.data) > 0:
                st.write("Sample data:")
                st.write(self.data.head(3)) 