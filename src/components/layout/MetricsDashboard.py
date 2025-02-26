# src/components/layout/MetricsDashboard.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional, Union
from components.common.MetricCard import MetricCard, create_info_metric, create_success_metric, create_danger_metric

class MetricsDashboard:
    """
    A component for displaying a comprehensive metrics dashboard with overview,
    distributions, and quick statistics in a standardized layout.
    """
    
    def __init__(
        self,
        metrics: Dict[str, Any],
        time_trends: Optional[Dict[str, Any]] = None,
        value_dist: Optional[Dict[str, Any]] = None,
        max_items_per_category: int = 5
    ):
        """
        Initialize the metrics dashboard
        
        Args:
            metrics: Dictionary with calculated metrics
            time_trends: Time trend analysis results (optional)
            value_dist: Value distribution analysis (optional)
            max_items_per_category: Maximum items to show in each category
        """
        self.metrics = metrics
        self.time_trends = time_trends
        self.value_dist = value_dist
        self.max_items = max_items_per_category
    
    def create_distribution_bar(
        self,
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
    
    def render_overview_metrics(self):
        """Render the overview metrics section"""
        st.subheader("Search Results Overview")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            # Total Projects - use info style (blue)
            create_info_metric(
                title="Total Projects",
                value=self.metrics['total_projects'],
                formatter=lambda x: f"{x:,}"
            ).render()
        
        with col2:
            # Total Value - use info style (blue)
            create_info_metric(
                title="Total Value",
                value=self.metrics['total_value'],
                prefix="฿",
                suffix="M",
                formatter=lambda x: f"{x/1e6:,.2f}"
            ).render()
        
        with col3:
            # Average Value - use info style (blue)
            create_info_metric(
                title="Average Value",
                value=self.metrics['average_value'],
                prefix="฿",
                suffix="M",
                formatter=lambda x: f"{x/1e6:,.2f}"
            ).render()
        
        with col4:
            # Companies - use info style (blue)
            create_info_metric(
                title="Companies",
                value=self.metrics['unique_companies'],
                formatter=lambda x: f"{x:,}"
            ).render()
        
        with col5:
            # Price Cut - use success/danger based on value
            if self.metrics['price_cut'] > 0:
                create_success_metric(
                    title="Price Cut",
                    value=self.metrics['price_cut'],
                    suffix="%",
                    formatter=lambda x: f"{x:.1f}",
                    delta="Positive"
                ).render()
            else:
                create_danger_metric(
                    title="Price Cut",
                    value=self.metrics['price_cut'],
                    suffix="%",
                    formatter=lambda x: f"{x:.1f}",
                    delta="Negative"
                ).render()
    
    def render_distribution_overview(self):
        """Render the distribution overview section with visualization bars"""
        st.subheader("Purchase Methods & Project Types Distribution")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Purchase methods distribution
            if 'purchase_methods' in self.metrics and 'distribution' in self.metrics['purchase_methods']:
                # Create Series from distribution dictionary
                methods_data = pd.Series(
                    self.metrics['purchase_methods']['distribution']
                )
                
                fig_methods = self.create_distribution_bar(
                    methods_data, 
                    "Purchase Methods",
                    base_color='rgb(255, 50, 50)'  # Red
                )
                st.plotly_chart(fig_methods, use_container_width=True, config={'displayModeBar': False})
                
                # Show top method details
                top_method = self.metrics['purchase_methods']['top_method']
                method_percentage = self.metrics['purchase_methods']['top_method_percentage']
                st.caption(f"Top Method: {top_method} ({method_percentage:.1f}%)")
        
        with col2:
            # Project types distribution
            if 'project_types' in self.metrics and 'distribution' in self.metrics['project_types']:
                # Create Series from distribution dictionary
                types_data = pd.Series(
                    self.metrics['project_types']['distribution']
                )
                
                fig_types = self.create_distribution_bar(
                    types_data, 
                    "Project Types",
                    base_color='rgb(50, 50, 255)'  # Blue
                )
                st.plotly_chart(fig_types, use_container_width=True, config={'displayModeBar': False})
                
                # Show top type details
                top_type = self.metrics['project_types']['top_type']
                type_percentage = self.metrics['project_types']['top_type_percentage']
                st.caption(f"Top Type: {top_type} ({type_percentage:.1f}%)")
    
    def render_quick_statistics(self):
        """Render the quick statistics section"""
        st.subheader("📊 Quick Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            self._render_department_overview()
        
        with col2:
            self._render_top_companies()
        
        with col3:
            self._render_procurement_methods()
    
    def _render_department_overview(self):
        """Render the department overview sub-section"""
        st.write("Department Overview")
        if self.metrics['department_stats']:
            # Limit to top N departments
            top_departments = sorted(
                self.metrics['department_stats'], 
                key=lambda x: x['value'], 
                reverse=True
            )[:self.max_items]
            
            for dept in top_departments:
                st.write(f"**{dept['dept_name']}**")
                st.write(f"Projects: {dept['projects']:,}")
                st.write(f"Value: ฿{dept['value']/1e6:,.1f}M")
                st.write(f"Companies: {dept['companies']:,}")
    
    def _render_top_companies(self):
        """Render the top companies sub-section"""
        st.write("Top Companies")
        if self.metrics['top_companies']:
            # Display up to N top companies
            top_companies = self.metrics['top_companies'][:self.max_items]
            for company in top_companies:
                st.write(f"**{company['company']}**")
                st.write(f"฿{company['value']/1e6:,.1f}M ({company['projects']} projects)")
    
    def _render_procurement_methods(self):
        """Render the procurement methods sub-section"""
        st.write("Procurement Methods")
        # Get top N procurement methods by count
        if self.metrics['purchase_methods']['distribution']:
            sorted_methods = sorted(
                self.metrics['purchase_methods']['distribution'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:self.max_items]
            
            for method, count in sorted_methods:
                percentage = self.metrics['purchase_methods']['percentages'][method]
                st.write(f"**{method}**")
                st.write(f"{count:,} projects ({percentage:.1f}%)")
    
    def render(self):
        """Render the complete metrics dashboard"""
        self.render_overview_metrics()
        self.render_distribution_overview()
        self.render_quick_statistics()


# Simplified function that uses the component
def display_metrics(metrics, time_trends=None, value_dist=None):
    """
    Display metrics for the project data using the MetricsDashboard component
    
    Args:
        metrics: Dictionary with calculated metrics
        time_trends: Time trend analysis results
        value_dist: Value distribution analysis
        
    Returns:
        None (renders metrics directly)
    """
    dashboard = MetricsDashboard(metrics, time_trends, value_dist)
    dashboard.render()