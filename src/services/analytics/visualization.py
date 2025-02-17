# src/srvices/analytics/visualization.py

import plotly.graph_objects as go
import plotly.colors as pc
from typing import Dict, List, Any, Optional, Union
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class VisualizationService:
    """Service for creating consistent data visualizations"""
    
    # Color schemes
    COLORS = {
        'primary': 'rgb(31, 119, 180)',      # Blue
        'secondary': 'rgb(255, 127, 14)',    # Orange
        'tertiary': 'rgb(44, 160, 44)',      # Green
        'quaternary': 'rgb(214, 39, 40)',    # Red
        'background': 'rgb(240, 240, 240)'   # Light Gray
    }
    
    # Default color sequences for multiple items
    COLOR_SEQUENCE = [
        'rgb(31, 119, 180)',   # Blue
        'rgb(255, 127, 14)',   # Orange
        'rgb(44, 160, 44)',    # Green
        'rgb(214, 39, 40)',    # Red
        'rgb(148, 103, 189)',  # Purple
        'rgb(140, 86, 75)',    # Brown
        'rgb(227, 119, 194)',  # Pink
        'rgb(127, 127, 127)',  # Gray
    ]

    @staticmethod
    def create_time_series(
        df: pd.DataFrame,
        x_col: str,
        y_cols: List[str],
        labels: List[str],
        title: str,
        height: int = 500,
        show_legend: bool = True
    ) -> go.Figure:
        """Create a time series visualization with multiple series"""
        fig = go.Figure()
        
        for y_col, label, color in zip(y_cols, labels, VisualizationService.COLOR_SEQUENCE):
            fig.add_trace(go.Scatter(
                x=df[x_col],
                y=df[y_col],
                name=label,
                line=dict(color=color, width=2),
                mode='lines+markers'
            ))

        fig.update_layout(
            title=title,
            height=height,
            showlegend=show_legend,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99
            ),
            margin=dict(l=50, r=50, t=50, b=50),
            hovermode='x unified'
        )
        
        return fig

    @staticmethod
    def create_bar_chart(
        df: pd.DataFrame,
        x_col: str,
        y_col: str,
        title: str,
        color: Optional[str] = None,
        height: int = 400,
        show_percentage: bool = False
    ) -> go.Figure:
        """Create a bar chart with optional percentage labels"""
        if show_percentage:
            total = df[y_col].sum()
            text = [f"{(val/total)*100:.1f}%" for val in df[y_col]]
        else:
            text = df[y_col]

        fig = go.Figure(data=[
            go.Bar(
                x=df[x_col],
                y=df[y_col],
                text=text,
                textposition='auto',
                marker_color=color or VisualizationService.COLORS['primary']
            )
        ])

        fig.update_layout(
            title=title,
            height=height,
            margin=dict(l=50, r=50, t=50, b=50),
            showlegend=False
        )
        
        return fig

    @staticmethod
    def create_dual_axis_chart(
        df: pd.DataFrame,
        x_col: str,
        y1_col: str,
        y2_col: str,
        y1_label: str,
        y2_label: str,
        title: str,
        height: int = 500
    ) -> go.Figure:
        """Create a dual axis chart combining bars and lines"""
        fig = go.Figure()

        # Add bars for first y-axis
        fig.add_trace(go.Bar(
            x=df[x_col],
            y=df[y1_col],
            name=y1_label,
            marker_color=VisualizationService.COLORS['primary']
        ))

        # Add line for second y-axis
        fig.add_trace(go.Scatter(
            x=df[x_col],
            y=df[y2_col],
            name=y2_label,
            yaxis='y2',
            line=dict(color=VisualizationService.COLORS['secondary'], width=2),
            mode='lines+markers'
        ))

        fig.update_layout(
            title=title,
            height=height,
            yaxis=dict(
                title=y1_label,
                titlefont=dict(color=VisualizationService.COLORS['primary']),
                tickfont=dict(color=VisualizationService.COLORS['primary'])
            ),
            yaxis2=dict(
                title=y2_label,
                titlefont=dict(color=VisualizationService.COLORS['secondary']),
                tickfont=dict(color=VisualizationService.COLORS['secondary']),
                overlaying='y',
                side='right'
            ),
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99
            ),
            margin=dict(l=50, r=50, t=50, b=50),
            hovermode='x unified'
        )
        
        return fig

    @staticmethod
    def create_heatmap(
        data: Union[pd.DataFrame, np.ndarray],
        x_labels: List[str],
        y_labels: List[str],
        title: str,
        height: int = 600,
        color_scale: str = 'RdBu'
    ) -> go.Figure:
        """Create a heatmap visualization"""
        fig = go.Figure(data=go.Heatmap(
            z=data,
            x=x_labels,
            y=y_labels,
            colorscale=color_scale,
            hoverongaps=False
        ))

        fig.update_layout(
            title=title,
            height=height,
            margin=dict(l=50, r=50, t=50, b=50),
            xaxis_title="",
            yaxis_title="",
            xaxis={'side': 'bottom'}
        )
        
        return fig

    @staticmethod
    def create_treemap(
        df: pd.DataFrame,
        labels: List[str],
        values: str,
        title: str,
        height: int = 500,
        color_scale: Optional[str] = None
    ) -> go.Figure:
        """Create a treemap visualization"""
        fig = go.Figure(go.Treemap(
            labels=labels,
            values=df[values],
            parents=[''] * len(df),
            textinfo='label+value',
            hovertemplate='<b>%{label}</b><br>Value: %{value}<extra></extra>',
            marker=dict(
                colorscale=color_scale or 'RdBu',
                showscale=True
            )
        ))

        fig.update_layout(
            title=title,
            height=height,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        
        return fig

    @staticmethod
    def create_summary_metrics(metrics: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Format metrics for Streamlit metrics display"""
        formatted_metrics = {}
        
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                if key.endswith('_growth') or key.endswith('_change'):
                    formatted_metrics[key] = {
                        'value': f"{value:.1f}%",
                        'delta': value,
                        'delta_color': 'normal' if value >= 0 else 'inverse'
                    }
                elif key.endswith('_value') or key.endswith('_amount'):
                    formatted_metrics[key] = {
                        'value': f"฿{value/1e6:.1f}M",
                        'delta': None
                    }
                elif key.endswith('_count') or key.endswith('_number'):
                    formatted_metrics[key] = {
                        'value': f"{value:,}",
                        'delta': None
                    }
                else:
                    formatted_metrics[key] = {
                        'value': f"{value:,}",
                        'delta': None
                    }
                    
        return formatted_metrics

    @staticmethod
    def format_table_data(
        df: pd.DataFrame,
        value_cols: List[str],
        percentage_cols: List[str]
    ) -> pd.DataFrame:
        """Format DataFrame for Streamlit table display"""
        formatted_df = df.copy()
        
        # Format value columns
        for col in value_cols:
            if col in formatted_df.columns:
                formatted_df[col] = formatted_df[col].apply(lambda x: f"฿{x/1e6:,.2f}M")
        
        # Format percentage columns
        for col in percentage_cols:
            if col in formatted_df.columns:
                formatted_df[col] = formatted_df[col].apply(lambda x: f"{x:.1f}%")
        
        return formatted_df