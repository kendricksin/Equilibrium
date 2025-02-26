# src/components/charts/CompanyProjectBreakdown.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional
import numpy as np
import logging
from components.charts.StackedBarChart import StackedBarChart

logger = logging.getLogger(__name__)

class CompanyProjectBreakdown:
    """Visualization component for company project breakdowns with stacked bars"""
    
    # Color palette for projects (extend this if needed)
    PROJECT_COLORS = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
        '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5',
        '#c49c94', '#f7b6d2', '#c7c7c7', '#dbdb8d', '#9edae5'
    ]
    
    def __init__(
        self,
        df: pd.DataFrame,
        price_column: str = 'sum_price_agree',
        budget_column: str = 'price_build',
        company_column: str = 'winner',
        project_column: str = 'project_name',
        date_column: str = 'transaction_date',
        value_unit: float = 1e6,  # Convert to millions
        max_companies: int = 15,
        key_prefix: str = ""
    ):
        """
        Initialize CompanyProjectBreakdown
        
        Args:
            df: DataFrame containing project data
            price_column: Column name for agreed price
            budget_column: Column name for budget/estimated price
            company_column: Column name for company/winner
            project_column: Column name for project name
            date_column: Column name for transaction date
            value_unit: Unit to convert values (default 1e6 for millions)
            max_companies: Maximum number of companies to show
            key_prefix: Key prefix for Streamlit components
        """
        self.df = df
        self.price_column = price_column
        self.budget_column = budget_column
        self.company_column = company_column
        self.project_column = project_column
        self.date_column = date_column
        self.value_unit = value_unit
        self.max_companies = max_companies
        self.key_prefix = key_prefix
    
    def prepare_data(
        self,
        min_projects: int = 1
    ) -> pd.DataFrame:
        """
        Prepare data for visualization
        
        Args:
            min_projects: Minimum number of projects for a company to be included
        
        Returns:
            DataFrame with prepared data for visualization
        """
        try:
            if self.df.empty:
                return pd.DataFrame()
            
            # Make sure required columns exist
            required_cols = [
                self.company_column, 
                self.price_column, 
                self.budget_column,
                self.project_column,
                self.date_column
            ]
            
            if not all(col in self.df.columns for col in required_cols):
                missing = [col for col in required_cols if col not in self.df.columns]
                logger.error(f"Missing required columns: {missing}")
                return pd.DataFrame()
            
            # Ensure numeric types
            analysis_df = self.df.copy()
            analysis_df[self.price_column] = pd.to_numeric(analysis_df[self.price_column], errors='coerce')
            analysis_df[self.budget_column] = pd.to_numeric(analysis_df[self.budget_column], errors='coerce')
            
            # Ensure date type
            if not pd.api.types.is_datetime64_any_dtype(analysis_df[self.date_column]):
                analysis_df[self.date_column] = pd.to_datetime(analysis_df[self.date_column], errors='coerce')
            
            # Calculate price cut percentage for each project
            analysis_df['price_cut_pct'] = ((analysis_df[self.price_column] / analysis_df[self.budget_column]) - 1) * 100
            
            # Convert price to millions for display
            analysis_df['value_millions'] = analysis_df[self.price_column] / self.value_unit
            
            # Sort by company and date
            analysis_df = analysis_df.sort_values([self.company_column, self.date_column])
            
            # Get company total values and project counts
            company_stats = analysis_df.groupby(self.company_column).agg({
                self.price_column: 'sum',
                self.project_column: 'count'
            }).reset_index()
            
            # Filter by minimum project count
            if min_projects > 1:
                company_stats = company_stats[company_stats[self.project_column] >= min_projects]
            
            # Calculate total market value
            total_market_value = company_stats[self.price_column].sum()
            
            # Calculate market share percentages
            company_stats['market_share'] = (company_stats[self.price_column] / total_market_value) * 100
            
            # Sort by market share
            company_stats = company_stats.sort_values('market_share', ascending=False)
            
            # Limit to max companies
            top_companies = company_stats.head(self.max_companies)[self.company_column].tolist()
            
            # Filter projects to only include top companies
            filtered_projects = analysis_df[analysis_df[self.company_column].isin(top_companies)]
            
            return filtered_projects
            
        except Exception as e:
            logger.error(f"Error preparing data: {e}")
            return pd.DataFrame()
    
    def render_market_share_breakdown(
        self,
        prepared_data: pd.DataFrame,
        height: int = 600,
        use_container_width: bool = True
    ):
        """
        Render market share breakdown with stacked bars by project
        
        Args:
            prepared_data: DataFrame with prepared data
            height: Chart height in pixels
            use_container_width: Whether to use full container width
        """
        try:
            if prepared_data.empty:
                st.warning("No data available to visualize")
                return
            
            # Get company total values to ensure correct ordering
            company_totals = prepared_data.groupby(self.company_column)[self.price_column].sum().reset_index()
            company_totals = company_totals.sort_values(self.price_column, ascending=False)
            ordered_companies = company_totals[self.company_column].tolist()
            
            # Create figure
            fig = go.Figure()
            
            # Generate a unique color for each project
            project_ids = prepared_data[self.project_column].unique()
            color_map = {}
            for i, project in enumerate(project_ids):
                color_idx = i % len(self.PROJECT_COLORS)
                color_map[project] = self.PROJECT_COLORS[color_idx]
            
            # Add each project as a bar segment
            for company in ordered_companies:
                company_data = prepared_data[prepared_data[self.company_column] == company]
                
                for _, row in company_data.iterrows():
                    project_name = row[self.project_column]
                    
                    # Truncate project name if too long
                    display_name = project_name
                    if len(display_name) > 30:
                        display_name = display_name[:27] + "..."
                    
                    # Format date for display
                    date_str = row[self.date_column].strftime("%Y-%m-%d") if pd.notna(row[self.date_column]) else "N/A"
                    
                    fig.add_trace(go.Bar(
                        x=[company],  # Place under company name
                        y=[row['value_millions']],  # Project value in millions
                        name=display_name,
                        marker_color=color_map.get(project_name, '#777777'),
                        customdata=np.array([[
                            project_name,
                            date_str,
                            row['value_millions'],
                            row['price_cut_pct'] if pd.notna(row['price_cut_pct']) else 0
                        ]]),
                        hovertemplate=(
                            "<b>%{x}</b><br>" +
                            "Project: %{customdata[0]}<br>" +
                            "Date: %{customdata[1]}<br>" +
                            "Value: ฿%{customdata[2]:.2f}M<br>" +
                            "Price Cut: %{customdata[3]:.2f}%<br>" +
                            "<extra></extra>"
                        ),
                        showlegend=False  # Too many projects for legend
                    ))
            
            # Update layout
            fig.update_layout(
                title="Company Project Breakdown",
                xaxis_title="Company",
                yaxis_title="Value (Million ฿)",
                height=height,
                barmode='stack',
                xaxis=dict(
                    tickangle=45,
                    categoryorder='array',
                    categoryarray=ordered_companies,
                    tickfont=dict(size=10)
                ),
                margin=dict(t=50, l=50, r=50, b=120),
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=12,
                    font_family="Arial"
                )
            )
            
            # Render in Streamlit
            st.plotly_chart(
                fig,
                use_container_width=use_container_width,
                key=f"{self.key_prefix}_project_breakdown_chart"
            )
            
        except Exception as e:
            logger.error(f"Error rendering project breakdown: {e}")
            st.error("Error rendering project breakdown visualization")
    
    def render_project_type_breakdown(
        self,
        prepared_data: pd.DataFrame,
        project_type_column: str = 'project_type_name',
        height: int = 600,
        use_container_width: bool = True
    ):
        """
        Render project type breakdown within companies
        
        Args:
            prepared_data: DataFrame with prepared data
            project_type_column: Column for project type
            height: Chart height in pixels
            use_container_width: Whether to use full container width
        """
        try:
            if prepared_data.empty or project_type_column not in prepared_data.columns:
                st.warning(f"No {project_type_column} data available to visualize")
                return
            
            # Prepare data for stacked bar chart
            stack_data = prepared_data[[self.company_column, project_type_column, 'value_millions']].copy()
            
            # Group by company and project type
            chart_data = stack_data.groupby([self.company_column, project_type_column])['value_millions'].sum().reset_index()
            
            # Calculate company totals for sorting
            company_totals = chart_data.groupby(self.company_column)['value_millions'].sum().sort_values(ascending=False)
            ordered_companies = company_totals.index.tolist()
            
            # Create a stack order mapping for consistent ordering
            stack_data['sort_order'] = stack_data[self.company_column].map({company: i for i, company in enumerate(ordered_companies)})
            
            # Use StackedBarChart component
            chart = StackedBarChart(
                data=chart_data,
                x_column=self.company_column,
                y_column='value_millions',
                color_column=project_type_column,
                title="Company Project Type Breakdown",
                height=height,
                show_legend=True
            )
            
            chart.render(
                key=f"{self.key_prefix}_project_type_breakdown_chart",
                use_container_width=use_container_width,
                show_totals=True
            )
            
        except Exception as e:
            logger.error(f"Error rendering project type breakdown: {e}")
            st.error("Error rendering project type breakdown visualization")
    
    def render(
        self,
        min_projects: int = 1,
        height: int = 600,
        show_project_types: bool = True
    ):
        """
        Render complete company project breakdown visualization
        
        Args:
            min_projects: Minimum projects for a company to be included
            height: Chart height in pixels
            show_project_types: Whether to show project type breakdown
        """
        try:
            st.subheader("📊 Company Project Breakdown Analysis")
            
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                show_min_projects = st.slider(
                    "Minimum Projects per Company",
                    min_value=1,
                    max_value=10,
                    value=min_projects,
                    key=f"{self.key_prefix}_breakdown_min_projects"
                )
            
            with col2:
                view_type = st.radio(
                    "Display Type",
                    options=["By Project", "By Project Type"] if show_project_types and 'project_type_name' in self.df.columns else ["By Project"],
                    horizontal=True,
                    key=f"{self.key_prefix}_breakdown_view_type"
                )
            
            # Prepare data
            prepared_data = self.prepare_data(min_projects=show_min_projects)
            
            if prepared_data.empty:
                st.warning("No data available for project breakdown analysis.")
                return
            
            # Display summary metrics
            company_count = prepared_data[self.company_column].nunique()
            project_count = len(prepared_data)
            total_value = prepared_data[self.price_column].sum() / self.value_unit
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Companies",
                    f"{company_count}",
                    help="Number of companies in the analysis"
                )
            with col2:
                st.metric(
                    "Projects",
                    f"{project_count}",
                    help="Total number of projects"
                )
            with col3:
                st.metric(
                    "Total Value",
                    f"฿{total_value:,.2f}M",
                    help="Total value of all projects"
                )
            
            # Render chosen visualization
            if view_type == "By Project":
                self.render_market_share_breakdown(
                    prepared_data=prepared_data,
                    height=height
                )
            else:  # By Project Type
                self.render_project_type_breakdown(
                    prepared_data=prepared_data,
                    project_type_column='project_type_name',
                    height=height
                )
                
        except Exception as e:
            logger.error(f"Error in project breakdown analysis: {e}")
            st.error("An error occurred while analyzing project breakdown data")

# Example usage function
def add_company_project_breakdown(filtered_df):
    """Add company project breakdown analysis section to the page"""
    
    # Add a separator for better visual organization
    st.markdown("---")
    
    # Initialize the component with filtered search results
    breakdown = CompanyProjectBreakdown(
        df=filtered_df,
        price_column='sum_price_agree',
        budget_column='price_build',
        company_column='winner',
        project_column='project_name',
        date_column='transaction_date',
        value_unit=1e6,  # Convert to millions
        max_companies=15,
        key_prefix="project_breakdown"
    )
    
    # Render the complete analysis
    breakdown.render(
        min_projects=1,
        height=600,
        show_project_types=True
    )