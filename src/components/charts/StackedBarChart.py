# src/components/charts/StackedBarChart.py

import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict, Any, Optional
import streamlit as st
import logging

logger = logging.getLogger(__name__)

class StackedBarChart:
    """Reusable stacked bar chart visualization component"""
    
    # Safe, light colors from Plotly's built-in colors
    SAFE_COLORS = [
        '#FFB6C1',  # lightpink
        '#98FB98',  # palegreen
        '#87CEFA',  # lightskyblue
        '#DDA0DD',  # plum
        '#F0E68C',  # khaki
        '#E6E6FA',  # lavender
        '#FFA07A',  # lightsalmon
        '#B0E0E6',  # powderblue
        '#FFE4B5',  # moccasin
        '#F5DEB3',  # wheat
        '#FFDAB9',  # peachpuff
        '#AFEEEE',  # paleturquoise
        '#D8BFD8',  # thistle
        '#DEB887',  # burlywood
        '#FA8072',  # salmon
    ]
    
    def __init__(
        self,
        data: pd.DataFrame,
        x_column: str,
        y_column: str,
        color_column: str,
        title: str = "",
        height: int = 500,
        show_legend: bool = True
    ):
        """
        Initialize StackedBarChart
        
        Args:
            data: DataFrame containing the data
            x_column: Column name for x-axis categories
            y_column: Column name for y-axis values
            color_column: Column name for color grouping
            title: Chart title
            height: Chart height in pixels
            show_legend: Whether to show the legend
        """
        self.data = data
        self.x_column = x_column
        self.y_column = y_column
        self.color_column = color_column
        self.title = title
        self.height = height
        self.show_legend = show_legend
    
    def render(
        self,
        key: Optional[str] = None,
        use_container_width: bool = True,
        show_totals: bool = True
    ):
        """
        Render the stacked bar chart
        
        Args:
            key: Unique key for the component
            use_container_width: Whether to use container width
            show_totals: Whether to show total values on top of bars
        """
        try:
            if len(self.data) == 0:
                st.warning("No data available for visualization")
                return
            
            # Get unique categories for color grouping
            categories = sorted(self.data[self.color_column].unique())
            
            # Create color map
            color_map = {
                cat: self.SAFE_COLORS[i % len(self.SAFE_COLORS)]
                for i, cat in enumerate(categories)
            }
            
            # Initialize figure
            fig = go.Figure()
            
            # Add traces for each category
            for category in categories:
                category_data = self.data[self.data[self.color_column] == category]
                
                # Only show in legend if it's the first occurrence
                show_in_legend = True
                
                fig.add_trace(
                    go.Bar(
                        name=str(category),
                        x=category_data[self.x_column],
                        y=category_data[self.y_column],
                        marker=dict(
                            color=color_map[category],
                            line=dict(color='rgb(50, 50, 50)', width=1)
                        ),
                        showlegend=show_in_legend,
                        hovertemplate=(
                            "<b>%{x}</b><br>" +
                            f"{self.color_column}: {category}<br>" +
                            f"{self.y_column}: %{{y:,.0f}}<br>" +
                            "<extra></extra>"
                        )
                    )
                )
            
            # Add total annotations if requested
            if show_totals:
                # Calculate totals for each x category
                totals = self.data.groupby(self.x_column)[self.y_column].sum()
                
                for x_cat in totals.index:
                    total = totals[x_cat]
                    fig.add_annotation(
                        x=x_cat,
                        y=total,
                        text=f"Total: {total:,.0f}",
                        showarrow=False,
                        yshift=10,
                        font=dict(size=10),
                        bgcolor="rgba(255, 255, 255, 0.8)",
                        bordercolor="rgba(0, 0, 0, 0.1)",
                        borderwidth=1,
                        borderpad=4
                    )
            
            # Update layout
            fig.update_layout(
                title=self.title,
                height=self.height,
                showlegend=self.show_legend,
                legend=dict(
                    title=self.color_column,
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                barmode='stack',
                bargap=0.2,
                margin=dict(t=50, l=25, r=25, b=100),
                xaxis=dict(
                    title=self.x_column,
                    tickangle=45
                ),
                yaxis=dict(
                    title=self.y_column
                ),
                hoverlabel=dict(
                    bgcolor="rgba(255, 255, 255, 0.7)",
                    bordercolor="rgba(0, 0, 0, 0.1)",
                    font_size=12,
                    font_family="Arial",
                    namelength=-1
                )
            )
            
            # Render in Streamlit
            st.plotly_chart(
                fig,
                use_container_width=use_container_width,
                key=key
            )
            
        except Exception as e:
            logger.error(f"Error rendering stacked bar chart: {e}")
            st.error("Error rendering visualization") 