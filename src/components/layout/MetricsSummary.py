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
    base_color: Union[str, List[str]] = 'rgb(255, 50, 50)'  # Default to red
) -> go.Figure:
    """
    Create a horizontal stacked bar chart showing distribution
    
    Args:
        data (pd.Series): Value counts of categories
        title (str): Chart title
        base_color (Union[str, List[str]]): Base color for the gradient. Can be a single color
            or a list of two colors for custom gradient. Default is red.
        
    Returns:
        go.Figure: Plotly figure object
    """
    # Calculate percentages
    percentages = (data / data.sum() * 100).round(1)
    
    # Sort by percentage
    percentages = percentages.sort_values(ascending=True)
    
    # Calculate color gradient
    n_items = len(data)
    
    if isinstance(base_color, list) and len(base_color) >= 2:
        # Use provided gradient colors
        from_color = base_color[0]
        to_color = base_color[1]
    else:
        # Create gradient from single color with transparency
        if base_color.startswith('rgb'):
            # Convert rgb to rgba format
            if 'rgba' not in base_color:
                base_color = base_color.replace('rgb', 'rgba').replace(')', ',')
        elif base_color.startswith('#'):
            # Convert hex to rgba format
            hex_color = base_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            base_color = f'rgba({r}, {g}, {b}, '
        
        from_color = f'{base_color}0.05)'
        to_color = f'{base_color}1)'
    
    def parse_color(color):
        """Helper function to parse color string to RGB values"""
        if color.startswith('rgba'):
            # Extract RGB values from rgba string
            values = color.replace('rgba(', '').replace(')', '').split(',')
            return [int(v.strip()) for v in values[:3]]
        elif color.startswith('rgb'):
            # Extract RGB values from rgb string
            values = color.replace('rgb(', '').replace(')', '').split(',')
            return [int(v.strip()) for v in values]
        elif color.startswith('#'):
            # Convert hex to RGB values
            hex_color = color.lstrip('#')
            return [
                int(hex_color[i:i+2], 16)
                for i in (0, 2, 4)
            ]
        return [0, 0, 0]  # Default to black if invalid color

    # Parse the gradient colors
    color1 = parse_color(from_color)
    color2 = parse_color(to_color)
    
    # Generate color gradient
    colors = [
        f'rgba({int(c1 * (1 - i/n_items) + c2 * (i/n_items))}, {int(g1 * (1 - i/n_items) + g2 * (i/n_items))}, {int(b1 * (1 - i/n_items) + b2 * (i/n_items))}, 1)'
        for i in range(n_items)
        for (c1, g1, b1), (c2, g2, b2) in [(color1, color2)]
    ]
    
    # Create the figure
    fig = go.Figure()
    
    # Add bars
    left = 0
    for i, (name, pct) in enumerate(percentages.items()):
        fig.add_trace(go.Bar(
            x=[pct],
            y=[title],
            orientation='h',
            name=name,
            text=f'{name}: {pct:.1f}%' if pct > 5 else '',
            textposition='inside',
            insidetextanchor='middle',
            marker=dict(
                color=colors[i],
                line=dict(
                    color='rgba(255, 255, 255, 0.5)',  # Semi-transparent black outline
                    width=1
                ),
                pattern=dict(
                    shape="",  # No pattern, just for gradient effect
                    solidity=0.1 + ((i+1)/len(percentages)) * 0.9  # Gradient based on position
                )
            ),
            showlegend=False,
        ))
        left += pct
    
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
        ),
        yaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False,
        ),
        bargap=0,
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