import streamlit as st
import plotly.graph_objects as go
from typing import Dict, Any

class ComparisonChart:
    """Reusable company comparison visualization component"""
    
    def __init__(self, metrics: Dict[str, Any]):
        self.metrics = metrics
    
    def render_competition_matrix(self, key: str = "competition_matrix"):
        """Render competition heatmap"""
        matrix = self.metrics['competition_matrix']
        
        fig = go.Figure(data=go.Heatmap(
            z=matrix.values,
            x=matrix.columns,
            y=matrix.index,
            colorscale='RdYlBu'
        ))
        
        fig.update_layout(
            title="Company Competition Matrix",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True, key=key)
    
    def render_market_share(self, key: str = "market_share"):
        """Render market share pie chart"""
        # Implementation here 