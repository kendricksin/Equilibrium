# src/components/charts/PriceCutScatterPlot.py

import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import streamlit as st
import logging

logger = logging.getLogger(__name__)

class PriceCutScatterPlot:
    """
    Component for visualizing project price cuts as a scatter plot.
    X-axis represents companies sorted by total value (largest on left),
    Y-axis represents price cut percentage, and each dot represents a project.
    """
    
    def __init__(
        self,
        data: pd.DataFrame,
        title: str = "Project Price Cut Analysis",
        height: int = 600,
        max_companies: int = 15,
        dot_size_column: Optional[str] = None,
        color_column: Optional[str] = None
    ):
        """
        Initialize PriceCutScatterPlot
        
        Args:
            data: DataFrame containing project data (must have 'winner', 'sum_price_agree', and 'price_build' columns)
            title: Chart title
            height: Chart height in pixels
            max_companies: Maximum number of companies to display (sorted by total project value)
            dot_size_column: Optional column to use for dot sizing (e.g., 'sum_price_agree')
            color_column: Optional column to use for dot coloring (e.g., 'dept_name')
        """
        self.data = data.copy()
        self.title = title
        self.height = height
        self.max_companies = max_companies
        self.dot_size_column = dot_size_column
        self.color_column = color_column
        
        # Validate data
        required_columns = ['winner', 'sum_price_agree', 'price_build']
        if not all(col in self.data.columns for col in required_columns):
            missing = [col for col in required_columns if col not in self.data.columns]
            raise ValueError(f"DataFrame missing required columns: {', '.join(missing)}")
        
        # Calculate price cut percentage
        self.data['price_cut_pct'] = ((self.data['sum_price_agree'] / self.data['price_build']) - 1) * 100
        
        # Prepare data
        self._prepare_data()
    
    def _prepare_data(self):
        """Prepare data for visualization"""
        # Convert dates if present
        if 'transaction_date' in self.data.columns and not pd.api.types.is_datetime64_any_dtype(self.data['transaction_date']):
            self.data['transaction_date'] = pd.to_datetime(self.data['transaction_date'])
        
        # Format transaction date for display
        if 'transaction_date' in self.data.columns:
            self.data['formatted_date'] = self.data['transaction_date'].dt.strftime('%Y-%m-%d')
        
        # Format values for display
        self.data['formatted_value'] = (self.data['sum_price_agree'] / 1e6).round(2).astype(str) + " M฿"
        
        # Calculate company metrics for sorting and labeling
        self.company_metrics = (
            self.data.groupby('winner')
            .agg({
                'sum_price_agree': 'sum',
                'project_name': 'count'
            })
            .reset_index()
            .rename(columns={
                'project_name': 'project_count'
            })
        )
        
        # Add formatted total value in millions
        self.company_metrics['total_value_mb'] = self.company_metrics['sum_price_agree'] / 1e6
        
        # Sort by total value (descending) and get top companies
        self.company_metrics = self.company_metrics.sort_values('sum_price_agree', ascending=False)
        self.top_companies = self.company_metrics.head(self.max_companies)['winner'].tolist()
        
        # Filter data for top companies
        self.plot_data = self.data[self.data['winner'].isin(self.top_companies)].copy()
        
        # Create company labels with count and value
        self.company_labels = {}
        for _, row in self.company_metrics.iterrows():
            if row['winner'] in self.top_companies:
                value_str = f"{row['total_value_mb']:.2f}M฿"
                self.company_labels[row['winner']] = f"{row['winner']}<br>({row['project_count']} projects, {value_str})"
        
        # Create categorical type for companies to maintain order
        company_order = pd.CategoricalDtype(categories=self.top_companies, ordered=True)
        self.plot_data['winner'] = self.plot_data['winner'].astype(company_order)
    
    def render(self, key: Optional[str] = None, use_container_width: bool = True):
        """
        Render the scatter plot
        
        Args:
            key: Unique key for the component
            use_container_width: Whether to use container width
        """
        try:
            if len(self.plot_data) == 0:
                st.warning("No data available for visualization")
                return
            
            # Initialize figure
            fig = go.Figure()
            
            # Define hover template
            hovertemplate = (
                "<b>%{customdata[0]}</b><br>" +
                "Company: %{x}<br>" +
                "Price Cut: %{y:.2f}%<br>" +
                "Value: %{customdata[1]}<br>" +
                "Date: %{customdata[2]}"
                "<extra></extra>"
            )
            
            # Calculate dot sizes if specified
            marker_size = 8  # Default size
            marker_sizes = None
            size_max = 25
            
            if self.dot_size_column and self.dot_size_column in self.plot_data.columns:
                # Normalize sizes between 5 and 25
                min_val = self.plot_data[self.dot_size_column].min()
                max_val = self.plot_data[self.dot_size_column].max()
                
                if min_val != max_val:
                    marker_sizes = 5 + ((self.plot_data[self.dot_size_column] - min_val) / (max_val - min_val)) * 20
                else:
                    marker_sizes = [8] * len(self.plot_data)
            
            # Determine color mapping
            if self.color_column and self.color_column in self.plot_data.columns:
                # Group by color column
                for color_value, group_data in self.plot_data.groupby(self.color_column):
                    custom_data = list(zip(
                        group_data['project_name'],
                        group_data['formatted_value'],
                        group_data.get('formatted_date', ['N/A'] * len(group_data))
                    ))
                    
                    # Apply per-group sizes if needed
                    group_sizes = marker_sizes[group_data.index] if marker_sizes is not None else marker_size
                    
                    fig.add_trace(go.Scatter(
                        x=group_data['winner'],
                        y=group_data['price_cut_pct'],
                        mode='markers',
                        marker=dict(
                            size=group_sizes,
                            opacity=0.7,
                            line=dict(width=1, color='DarkSlateGrey')
                        ),
                        name=str(color_value),
                        customdata=custom_data,
                        hovertemplate=hovertemplate
                    ))
            else:
                # Single group, all same color
                custom_data = list(zip(
                    self.plot_data['project_name'],
                    self.plot_data['formatted_value'],
                    self.plot_data.get('formatted_date', ['N/A'] * len(self.plot_data))
                ))
                
                fig.add_trace(go.Scatter(
                    x=self.plot_data['winner'],
                    y=self.plot_data['price_cut_pct'],
                    mode='markers',
                    marker=dict(
                        size=marker_sizes if marker_sizes is not None else marker_size,
                        opacity=0.7,
                        color='royalblue',
                        line=dict(width=1, color='DarkSlateGrey')
                    ),
                    customdata=custom_data,
                    hovertemplate=hovertemplate
                ))
            
            # Create custom ticktext with project count and total value
            tickvals = list(range(len(self.top_companies)))
            ticktext = [self.company_labels.get(company, company) for company in self.top_companies]
            
            # Update layout
            fig.update_layout(
                title=self.title,
                height=self.height,
                xaxis=dict(
                    title="Companies (sorted by total project value)",
                    tickangle=45,
                    tickmode='array',
                    tickvals=tickvals,
                    ticktext=ticktext,
                    tickfont=dict(size=10)
                ),
                yaxis=dict(
                    title="Price Cut Percentage (%)",
                    zeroline=True,
                    zerolinecolor='rgba(0,0,0,0.2)',
                    gridcolor='rgba(0,0,0,0.1)'
                ),
                hovermode='closest',
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=12,
                    font_family="Arial"
                ),
                margin=dict(t=50, l=25, r=25, b=200),  # Extra bottom margin for company labels with info
                showlegend=self.color_column is not None
            )
            
            # Add reference line at 0% price cut
            fig.add_shape(
                type="line",
                x0=-0.5,  # Extend beyond the first category
                y0=0,
                x1=len(self.top_companies) - 0.5,  # Extend beyond the last category
                y1=0,
                line=dict(
                    color="rgba(255, 0, 0, 0.5)",
                    width=2,
                    dash="dash"
                )
            )
            
            # Add annotations for value zones
            if self.plot_data['price_cut_pct'].min() < 0:
                fig.add_annotation(
                    x=0,
                    y=min(-5, self.plot_data['price_cut_pct'].min() * 0.8),
                    text="Competitive Pricing (Discount)",
                    showarrow=False,
                    font=dict(color="green")
                )
            
            if self.plot_data['price_cut_pct'].max() > 0:
                fig.add_annotation(
                    x=0,
                    y=max(5, self.plot_data['price_cut_pct'].max() * 0.8),
                    text="Premium Pricing (Markup)",
                    showarrow=False,
                    font=dict(color="red")
                )
            
            # Render in Streamlit
            st.plotly_chart(
                fig,
                use_container_width=use_container_width,
                key=key
            )
            
        except Exception as e:
            logger.error(f"Error rendering price cut scatter plot: {e}")
            st.error("Error rendering visualization")


def plot_price_cut_scatter(
    df: pd.DataFrame,
    title: str = "Project Price Cut Analysis",
    height: int = 600,
    max_companies: int = 15,
    use_size_by_value: bool = True,
    color_by: Optional[str] = None,
    key_prefix: str = ""
):
    """
    Convenience function to create and render a price cut scatter plot
    
    Args:
        df: DataFrame containing project data
        title: Chart title
        height: Chart height
        max_companies: Maximum companies to display
        use_size_by_value: Whether to size dots by project value
        color_by: Column to use for coloring dots
        key_prefix: Prefix for component keys
    """
    try:
        # Check for required columns
        if 'sum_price_agree' in df.columns and 'price_build' in df.columns:
            # Create and render plot
            dot_size_column = 'sum_price_agree' if use_size_by_value else None
            
            PriceCutScatterPlot(
                data=df,
                title=title,
                height=height,
                max_companies=max_companies,
                dot_size_column=dot_size_column,
                color_column=color_by
            ).render(key=f"{key_prefix}_price_cut_scatter")
        else:
            st.warning("Cannot create price cut visualization: missing required columns")
    except Exception as e:
        logger.error(f"Error creating price cut scatter plot: {e}")
        st.error(f"Error creating visualization: {str(e)}")