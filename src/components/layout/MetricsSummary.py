# src/components/layout/MetricsSummary.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any, Optional, List
from services.analytics.project_analysis import ProjectAnalysisService
from services.analytics.visualization import VisualizationService

def create_distribution_bar(data: pd.Series, title: str, base_color: str = 'rgb(31, 119, 180)') -> go.Figure:
    """Create a horizontal distribution bar chart"""
    if data.empty:
        return go.Figure()
    
    # Calculate percentages
    percentages = (data / data.sum() * 100).round(1)
    
    # Sort by percentage (ascending for visualization)
    percentages = percentages.sort_values(ascending=True)
    
    # Create figure
    fig = go.Figure()
    
    # Add stacked bars
    fig.add_trace(go.Bar(
        x=percentages,
        y=[title],
        orientation='h',
        text=[f"{name}: {pct:.1f}%" for name, pct in percentages.items()],
        textposition='inside',
        marker=dict(
            color=base_color,
            opacity=[0.3 + (i/len(percentages))*0.7 for i in range(len(percentages))]
        ),
        hovertemplate="<b>%{text}</b><extra></extra>"
    ))
    
    # Update layout
    fig.update_layout(
        height=60,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            range=[0, 100]
        ),
        yaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False
        ),
        bargap=0,
        uniformtext=dict(mode='hide', minsize=8)
    )
    
    return fig

def MetricsSummary(df: Optional[pd.DataFrame] = None):
    """
    Display a summary of key metrics with distribution charts
    
    Args:
        df: Optional DataFrame with project data. If None, will fetch from ProjectAnalysisService
    """
    # Custom CSS for metrics styling
    st.markdown("""
        <style>
        .metric-container {
            background-color: #f8f9fa;
            padding: 1.5rem;
            border-radius: 0.5rem;
            margin-bottom: 1.5rem;
        }
        .metric-row {
            margin-bottom: 1rem;
        }
        .distribution-row {
            background-color: white;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-top: 1rem;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.5rem !important;
        }
        [data-testid="stMetricDelta"] {
            font-size: 0.8rem !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    if df is None:
        # Get data from ProjectAnalysisService
        project_service = ProjectAnalysisService()
        metrics = project_service.get_project_summary()
        df = project_service.get_project_trends('M').tail(12)  # Last 12 months
    else:
        # Calculate metrics from provided DataFrame
        metrics = {
            'total_projects': len(df),
            'total_value': df['sum_price_agree'].sum(),
            'unique_companies': df['winner'].nunique(),
            'unique_departments': df['dept_name'].nunique(),
            'avg_value': df['sum_price_agree'].mean()
        }
    
    # Format metrics
    formatted_metrics = VisualizationService.create_summary_metrics(metrics)
    
    # Start metrics container
    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
    
    # Key metrics row
    st.markdown('<div class="metric-row">', unsafe_allow_html=True)
    cols = st.columns(5)
    
    with cols[0]:
        st.metric(
            "Total Projects",
            formatted_metrics['total_projects']['value'],
            help="Total number of projects"
        )
    
    with cols[1]:
        st.metric(
            "Total Value",
            formatted_metrics['total_value']['value'],
            help="Total project value"
        )
    
    with cols[2]:
        st.metric(
            "Companies",
            formatted_metrics['unique_companies']['value'],
            help="Number of unique companies"
        )
    
    with cols[3]:
        st.metric(
            "Departments",
            formatted_metrics['unique_departments']['value'],
            help="Number of unique departments"
        )
    
    with cols[4]:
        st.metric(
            "Average Value",
            formatted_metrics['avg_value']['value'],
            help="Average project value"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Distribution charts row
    st.markdown('<div class="distribution-row">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Project Types")
        if 'project_type_name' in df.columns:
            type_dist = df['project_type_name'].value_counts()
            fig1 = create_distribution_bar(
                type_dist,
                "Distribution",
                base_color='rgb(31, 119, 180)'
            )
            st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
            
            # Show top type details
            top_type = type_dist.index[0]
            type_share = type_dist.iloc[0] / len(df) * 100
            st.caption(f"Most common: {top_type} ({type_share:.1f}%)")
    
    with col2:
        st.markdown("##### Procurement Methods")
        if 'purchase_method_name' in df.columns:
            method_dist = df['purchase_method_name'].value_counts()
            fig2 = create_distribution_bar(
                method_dist,
                "Distribution",
                base_color='rgb(255, 127, 14)'
            )
            st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
            
            # Show top method details
            top_method = method_dist.index[0]
            method_share = method_dist.iloc[0] / len(df) * 100
            st.caption(f"Most common: {top_method} ({method_share:.1f}%)")
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)