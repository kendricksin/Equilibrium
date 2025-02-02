# src/components/layout/MetricsSummary.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Optional, Union, List
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get font sizes from environment variables or use defaults
METRIC_LABEL_SIZE = os.getenv('METRIC_LABEL_SIZE', '0.8rem')
METRIC_VALUE_SIZE = os.getenv('METRIC_VALUE_SIZE', '1.5rem')
METRIC_DELTA_SIZE = os.getenv('METRIC_DELTA_SIZE', '0.8rem')
METRIC_CONTAINER_PADDING = os.getenv('METRIC_CONTAINER_PADDING', '1rem')
METRIC_BORDER_RADIUS = os.getenv('METRIC_BORDER_RADIUS', '0.5rem')

def create_distribution_bar(
    data: pd.Series, 
    title: str,
    base_color: Union[str, List[str]] = 'rgb(255, 50, 50)',  # Default to red
    max_categories: int = 3  # Limit number of categories
) -> go.Figure:
    """
    Create a horizontal stacked bar chart showing distribution
    
    Args:
        data (pd.Series): Value counts of categories
        title (str): Chart title
        base_color (Union[str, List[str]]): Base color for the gradient
        max_categories (int): Maximum number of categories to show
        
    Returns:
        go.Figure: Plotly figure object
    """
    if data.empty:
        return go.Figure()

    # Calculate initial percentages
    percentages = (data / data.sum() * 100).round(1)
    
    # Handle categories limit
    if len(percentages) > max_categories:
        # Get top N-1 categories
        top_categories = percentages.nlargest(max_categories - 1)
        
        # Calculate and add "Others" category
        others_sum = percentages[~percentages.index.isin(top_categories.index)].sum()
        if others_sum > 0:
            top_categories = pd.concat([
                top_categories,
                pd.Series({'Others': others_sum})
            ])
        percentages = top_categories
    
    # Sort by percentage (ascending for visualization)
    percentages = percentages.sort_values(ascending=True)
    
    def generate_color_scale(n, base_color='rgb(255, 50, 50)'):
        """Generate a color scale with varying opacity"""
        if n <= 0:
            return []
            
        if isinstance(base_color, list):
            # Use the first color if a list is provided
            base_color = base_color[0]
            
        # Extract RGB values
        if base_color.startswith('rgb'):
            rgb_values = base_color.replace('rgb(', '').replace(')', '').split(',')
            r, g, b = map(int, rgb_values)
        else:
            # Default to red if color format is not recognized
            r, g, b = 255, 50, 50
            
        # Generate colors with increasing opacity
        colors = []
        if n == 1:
            # Special case for single category
            colors.append(f'rgba({r}, {g}, {b}, 0.8)')
        else:
            for i in range(n):
                opacity = 0.2 + (i / (n - 1)) * 0.8  # Scale from 0.2 to 1.0
                colors.append(f'rgba({r}, {g}, {b}, {opacity})')
            
        return colors
    
    # Calculate color gradient
    n_items = len(percentages)
    colors = generate_color_scale(n_items, base_color)
    
    if not colors:  # Safety check
        return go.Figure()
    
    # Create the figure
    fig = go.Figure()
    
    # Add bars
    for i, (name, pct) in enumerate(percentages.items()):
        text = f'{name}: {pct:.1f}%'
        # Adjust text position and anchor based on percentage
        if pct < 5:
            textposition = 'outside'
            insidetextanchor = 'start'
        else:
            textposition = 'inside'
            insidetextanchor = 'middle'
            
        fig.add_trace(go.Bar(
            x=[pct],
            y=[title],
            orientation='h',
            name=name,
            text=text,
            textposition=textposition,
            insidetextanchor=insidetextanchor,
            marker=dict(
                color=colors[i],
                line=dict(
                    color='rgba(255, 255, 255, 0.5)',  # Semi-transparent white outline
                    width=1
                )
            ),
            showlegend=False,
        ))
    
    # Update layout
    fig.update_layout(
        barmode='stack',
        height=60,
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            range=[0, 100]  # Fix x-axis range to 0-100%
        ),
        yaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False,
        ),
        bargap=0,
        uniformtext=dict(
            mode='hide',
            minsize=8
        )
    )
    
    return fig

def MetricsSummary(df: Optional[pd.DataFrame] = None):
    """
    Enhanced metrics summary with configurable styles and distribution charts
    
    Args:
        df (Optional[pd.DataFrame]): The filtered dataframe containing project data
    """
    with st.container():
        # Custom CSS with environment variable values
        st.markdown(f"""
            <style>
            .metrics-summary {{
                background-color: #f8f9fa;
                padding: {METRIC_CONTAINER_PADDING};
                border-radius: {METRIC_BORDER_RADIUS};
                margin-bottom: 1rem;
            }}
            
            [data-testid="stMetricLabel"] {{
                font-size: {METRIC_LABEL_SIZE} !important;
            }}
            
            [data-testid="stMetricValue"] {{
                font-size: {METRIC_VALUE_SIZE} !important;
            }}
            
            [data-testid="stMetricDelta"] {{
                font-size: {METRIC_DELTA_SIZE} !important;
            }}
            
            .distribution-chart {{
                margin-top: 1rem;
                padding: 0.5rem;
                background-color: white;
                border-radius: 0.25rem;
            }}
            </style>
        """, unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="metrics-summary">', unsafe_allow_html=True)
            
            if df is not None and not df.empty:
                # First row of metrics
                col1, col2, col3, col4, col5 = st.columns(5)
                
                total_projects = len(df)
                total_value = df['sum_price_agree'].sum()
                avg_value = df['sum_price_agree'].mean()
                unique_companies = df['winner'].nunique()
                
                # Calculate price cut percentage
                avg_price_cut = (((df['sum_price_agree'].sum() / df['price_build'].sum()) - 1) * 100)
                
                with col1:
                    st.metric(
                        label="Total Projects",
                        value=f"{total_projects:,}",
                        help="Total number of projects in the selected period"
                    )
                with col2:
                    st.metric(
                        label="Total Value",
                        value=f"฿{total_value/1e6:,.2f}M",
                        help="Total value of all projects"
                    )
                with col3:
                    st.metric(
                        label="Average Value",
                        value=f"฿{avg_value/1e6:,.2f}M",
                        help="Average value per project"
                    )
                with col4:
                    st.metric(
                        label="Companies",
                        value=f"{unique_companies:,}",
                        help="Number of unique companies"
                    )
                with col5:
                    st.metric(
                        label="Price Cut",
                        value=f"{(avg_price_cut):.1f}%",
                        delta="Competitive" if avg_price_cut < -5 else "Fair",
                        delta_color="inverse" if avg_price_cut < -5 else "normal",
                        help="Average percentage difference between agreed price and budget"
                    )
                
                # Distribution charts
                st.markdown("##### Purchase Methods & Project Types Distribution")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Purchase methods distribution
                    purchase_methods = df['purchase_method_name'].value_counts()
                    fig_methods = create_distribution_bar(
                        purchase_methods, 
                        "Purchase Methods",
                        base_color='rgb(255, 50, 50)'  # Keeping red as default
                    )
                    st.plotly_chart(fig_methods, use_container_width=True, config={'displayModeBar': False})
                    
                    # Show top method details
                    top_method = purchase_methods.index[0]
                    method_share = purchase_methods.iloc[0] / len(df) * 100
                    st.caption(f"Top Method: {top_method} ({method_share:.1f}%)")
                
                with col2:
                    # Project types distribution
                    project_types = df['project_type_name'].value_counts()
                    fig_types = create_distribution_bar(
                        project_types, 
                        "Project Types",
                        base_color='rgb(255, 50, 50)'  # Keeping red as default
                    )
                    st.plotly_chart(fig_types, use_container_width=True, config={'displayModeBar': False})
                    
                    # Show top type details
                    top_type = project_types.index[0]
                    type_share = project_types.iloc[0] / len(df) * 100
                    st.caption(f"Top Type: {top_type} ({type_share:.1f}%)")
            
            else:
                # Display placeholder values when no data is available
                for _ in range(5):
                    st.metric(label="-", value="-")
            
            st.markdown('</div>', unsafe_allow_html=True)