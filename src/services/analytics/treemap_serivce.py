# src/services/analytics/treemap_service.py

import plotly.graph_objects as go
import plotly.colors as pc
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, Tuple, List, Union
import logging

logger = logging.getLogger(__name__)

class TreemapService:
    """Service for creating and customizing treemap visualizations"""
    
    @staticmethod
    def prepare_treemap_data(
        df: pd.DataFrame,
        group_col: str,
        value_cols: List[str],
        percentage_cols: Optional[List[str]] = None,
        top_n: Optional[int] = None,
        min_value: Optional[float] = None,
        include_others: bool = True
    ) -> Tuple[pd.DataFrame, Dict[str, float]]:
        """
        Prepare data for treemap visualization
        
        Args:
            df: Input DataFrame
            group_col: Column to group by
            value_cols: List of columns to aggregate
            percentage_cols: List of pre-calculated percentage columns
            top_n: Number of top items to include
            min_value: Minimum value threshold
            include_others: Whether to include "Others" category
            
        Returns:
            Tuple of prepared DataFrame and totals dictionary
        """
        try:
            # Filter out rows with null or zero values if specified
            if min_value is not None:
                for col in value_cols:
                    df = df[df[col] > min_value]
            
            # Use pre-calculated aggregations if available
            if percentage_cols:
                grouped_data = df
            else:
                # Group and aggregate data
                grouped_data = (
                    df.groupby(group_col)
                    .agg({col: 'sum' for col in value_cols})
                    .reset_index()
                )
            
            # Calculate totals
            totals = {col: grouped_data[col].sum() for col in value_cols}
            
            # Add percentage calculations if not provided
            if not percentage_cols:
                percentage_cols = []
                for col in value_cols:
                    pct_col = f"{col}_percentage"
                    grouped_data[pct_col] = (grouped_data[col] / totals[col] * 100).round(2)
                    percentage_cols.append(pct_col)
            
            # Sort and filter top N if specified
            if top_n and len(grouped_data) > top_n:
                main_value_col = value_cols[0]
                grouped_data = grouped_data.sort_values(main_value_col, ascending=False)
                
                if include_others:
                    top_data = grouped_data.head(top_n)
                    others_data = pd.DataFrame([{
                        group_col: 'Others',
                        **{
                            col: grouped_data.iloc[top_n:][col].sum() 
                            for col in value_cols + percentage_cols
                        }
                    }])
                    grouped_data = pd.concat([top_data, others_data], ignore_index=True)
                else:
                    grouped_data = grouped_data.head(top_n)
            
            return grouped_data, totals
            
        except Exception as e:
            logger.error(f"Error preparing treemap data: {e}")
            raise
    
    @staticmethod
    def create_color_scale(
        n_colors: int,
        color_scheme: Optional[Union[str, List[str]]] = None
    ) -> List[str]:
        """Create a color scale for treemap nodes"""
        try:
            if color_scheme is None:
                # Default blue color scheme
                color_scheme = ['rgb(210,230,255)', 'rgb(30,144,255)']
            
            if isinstance(color_scheme, str):
                # Use predefined Plotly color scales
                colors = pc.sample_colorscale(
                    color_scheme,
                    n_colors
                )
            else:
                # Interpolate between provided colors
                colors = pc.n_colors(
                    color_scheme[0],
                    color_scheme[-1],
                    n_colors,
                    colortype='rgb'
                )
            
            return colors
            
        except Exception as e:
            logger.error(f"Error creating color scale: {e}")
            raise
    
    @staticmethod
    def create_treemap(
        data: pd.DataFrame,
        id_col: str,
        value_col: str,
        hover_data: Optional[Dict[str, str]] = None,
        custom_data: Optional[List] = None,
        title: Optional[str] = None,
        height: int = 600,
        color_scheme: Optional[Union[str, List[str]]] = None,
        show_percentages: bool = True,
        text_template: Optional[str] = None,
        layout_options: Optional[Dict[str, Any]] = None
    ) -> go.Figure:
        """
        Create a customized treemap visualization
        
        Args:
            data: Prepared DataFrame
            id_col: Column for node IDs
            value_col: Column for node values
            hover_data: Hover text format strings
            custom_data: Additional data for hover template
            title: Chart title
            height: Chart height
            color_scheme: Color scheme for nodes
            show_percentages: Whether to show percentage in labels
            text_template: Custom template for node text
            layout_options: Additional layout options
        """
        try:
            # Generate colors based on value distribution
            colors = TreemapService.create_color_scale(
                len(data),
                color_scheme
            )
            
            # Prepare hover template
            if hover_data:
                hover_template = "<br>".join(hover_data.values()) + "<extra></extra>"
            else:
                hover_template = (
                    "<b>%{label}</b><br>"
                    "Value: %{value:,.0f}<extra></extra>"
                )
            
            # Prepare text info
            if text_template and show_percentages:
                # Get percentage column name
                pct_col = (
                    'count_percentage' if 'count' in value_col 
                    else 'value_percentage'
                )
                # Format labels with template
                labels = [
                    text_template.format(row[id_col], row[pct_col])
                    for _, row in data.iterrows()
                ]
            else:
                labels = data[id_col]
            
            # Create figure
            fig = go.Figure(go.Treemap(
                ids=data[id_col],
                parents=[''] * len(data),
                values=data[value_col],
                labels=labels,
                customdata=custom_data,
                textposition="middle center",
                textinfo="text",
                text=labels,
                hovertemplate=hover_template,
                marker=dict(
                    colors=colors,
                    line=dict(width=1, color='white')
                ),
                tiling=dict(
                    packing="squarify",
                    pad=3
                ),
                pathbar=dict(
                    visible=False
                )
            ))
            
            # Update layout
            default_layout = dict(
                title=dict(
                    text=title,
                    x=0.5,
                    xanchor='center'
                ),
                height=height,
                margin=dict(t=50, l=10, r=10, b=10),
                uniformtext=dict(minsize=10, mode='hide'),
                showlegend=False
            )
            
            if layout_options:
                default_layout.update(layout_options)
            
            fig.update_layout(default_layout)
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating treemap: {e}")
            raise