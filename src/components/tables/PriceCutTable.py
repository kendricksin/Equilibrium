# src/components/tables/PriceCutTable.py

import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)

class PriceCutAnalysis:
    """Analysis component for price cut and market share by company"""
    
    def __init__(
        self,
        df: pd.DataFrame,
        price_column: str = 'sum_price_agree',
        budget_column: str = 'price_build',
        company_column: str = 'winner',
        value_unit: float = 1e6,  # Convert to millions
        key_prefix: str = ""
    ):
        """
        Initialize PriceCutAnalysis
        
        Args:
            df: DataFrame containing project data
            price_column: Column name for agreed price
            budget_column: Column name for budget/estimated price
            company_column: Column name for company/winner
            value_unit: Unit to convert values (default 1e6 for millions)
            key_prefix: Key prefix for Streamlit components
        """
        self.df = df
        self.price_column = price_column
        self.budget_column = budget_column
        self.company_column = company_column
        self.value_unit = value_unit
        self.key_prefix = key_prefix
    
    def calculate_price_cut_metrics(
        self,
        min_projects: int = 1,
        max_companies: int = 25  # Max companies to show before grouping as "Others"
    ) -> pd.DataFrame:
        """
        Calculate price cut metrics and market share by company
        
        Args:
            min_projects: Minimum number of projects for a company to be included
            max_companies: Max number of companies to show individually
        
        Returns:
            DataFrame with price cut and market share analysis
        """
        try:
            if self.df.empty:
                return pd.DataFrame(columns=[
                    self.company_column, 'sum_price_agree', 'avg_price_cut', 
                    'min_price_cut', 'max_price_cut', 'project_count',
                    'market_share', 'total_value_mb'
                ])
            
            # Make sure required columns exist
            required_cols = [self.company_column, self.price_column, self.budget_column]
            if not all(col in self.df.columns for col in required_cols):
                missing = [col for col in required_cols if col not in self.df.columns]
                logger.error(f"Missing required columns: {missing}")
                return pd.DataFrame()
            
            # Calculate price cut for each project
            analysis_df = self.df.copy()
            
            # Ensure numeric types
            analysis_df[self.price_column] = pd.to_numeric(analysis_df[self.price_column], errors='coerce')
            analysis_df[self.budget_column] = pd.to_numeric(analysis_df[self.budget_column], errors='coerce')
            
            # Filter out rows where price cut can't be calculated
            analysis_df = analysis_df[
                (analysis_df[self.price_column].notna()) & 
                (analysis_df[self.budget_column].notna()) &
                (analysis_df[self.budget_column] > 0)  # Avoid division by zero
            ]
            
            # Calculate price cut percentage for each project
            analysis_df['price_cut_pct'] = ((analysis_df[self.price_column] / analysis_df[self.budget_column]) - 1) * 100
            
            # Group by company and calculate metrics
            company_metrics = analysis_df.groupby(self.company_column).agg({
                self.price_column: 'sum',
                'price_cut_pct': ['mean', 'min', 'max'],
                'project_name': 'count'
            }).reset_index()
            
            # Fix column names
            company_metrics.columns = [
                self.company_column, 'sum_price_agree', 'avg_price_cut', 
                'min_price_cut', 'max_price_cut', 'project_count'
            ]
            
            # Calculate total market value
            total_market_value = company_metrics['sum_price_agree'].sum()
            
            # Calculate market share percentages
            company_metrics['market_share'] = (company_metrics['sum_price_agree'] / total_market_value) * 100
            
            # Add total value in millions
            company_metrics['total_value_mb'] = company_metrics['sum_price_agree'] / self.value_unit
            
            # Filter by minimum project count
            if min_projects > 1:
                company_metrics = company_metrics[company_metrics['project_count'] >= min_projects]
            
            # Sort by market share in descending order
            company_metrics = company_metrics.sort_values('market_share', ascending=False)
            
            # Limit to max companies if needed
            if len(company_metrics) > max_companies:
                # Keep top companies and group the rest
                top_companies = company_metrics.head(max_companies - 1)  # -1 to make room for "Others"
                other_companies = company_metrics.iloc[max_companies - 1:]
                
                # Create "Others" row
                others_row = pd.DataFrame({
                    self.company_column: ['Others'],
                    'sum_price_agree': [other_companies['sum_price_agree'].sum()],
                    'avg_price_cut': [other_companies['avg_price_cut'].mean()],
                    'min_price_cut': [other_companies['min_price_cut'].min()],
                    'max_price_cut': [other_companies['max_price_cut'].max()],
                    'project_count': [other_companies['project_count'].sum()],
                    'market_share': [other_companies['market_share'].sum()],
                    'total_value_mb': [other_companies['total_value_mb'].sum()]
                })
                
                # Combine top companies with "Others" row
                company_metrics = pd.concat([top_companies, others_row])
            
            return company_metrics
            
        except Exception as e:
            logger.error(f"Error calculating price cut metrics: {e}")
            return pd.DataFrame()
    
    def render_metrics_table(
        self,
        company_metrics: pd.DataFrame,
        highlight_column: str = 'market_share',
        show_details: bool = True
    ):
        """
        Render metrics data table with enhanced formatting
        
        Args:
            company_metrics: DataFrame with price cut and market share analysis
            highlight_column: Column to use for conditional formatting
            show_details: Whether to show detailed statistics
        """
        try:
            if company_metrics.empty:
                st.warning("No data available to display")
                return
            
            # Prepare display dataframe
            display_df = company_metrics.copy()
            
            # Round values for display
            for col in ['avg_price_cut', 'min_price_cut', 'max_price_cut', 'market_share']:
                if col in display_df.columns:
                    display_df[col] = display_df[col].round(2)
            
            if 'total_value_mb' in display_df.columns:
                display_df['total_value_mb'] = display_df['total_value_mb'].round(2)
            
            # Create column configurations with conditional formatting
            column_config = {
                'Company': st.column_config.TextColumn(
                    'Company',
                    width='large'
                ),
                'Projects': st.column_config.NumberColumn(
                    'Projects',
                    format="%d"
                ),
                'Avg Price Cut (%)': st.column_config.NumberColumn(
                    'Avg Price Cut (%)',
                    format="%.2f%%"
                ),
                'Min Price Cut (%)': st.column_config.NumberColumn(
                    'Min Price Cut (%)',
                    format="%.2f%%"
                ),
                'Max Price Cut (%)': st.column_config.NumberColumn(
                    'Max Price Cut (%)',
                    format="%.2f%%"
                ),
                'Market Share (%)': st.column_config.NumberColumn(
                    'Market Share (%)',
                    format="%.2f%%"
                ),
                'Total Value (M฿)': st.column_config.NumberColumn(
                    'Total Value (M฿)',
                    format="%.2f"
                )
            }
            
            # Display dataframe with formatting
            st.dataframe(
                display_df.rename(columns={
                    self.company_column: 'Company',
                    'sum_price_agree': 'Total Value (฿)',
                    'avg_price_cut': 'Avg Price Cut (%)',
                    'min_price_cut': 'Min Price Cut (%)',
                    'max_price_cut': 'Max Price Cut (%)',
                    'project_count': 'Projects',
                    'market_share': 'Market Share (%)',
                    'total_value_mb': 'Total Value (M฿)'
                }),
                column_config=column_config,
                hide_index=True
            )
            
        except Exception as e:
            logger.error(f"Error rendering metrics table: {e}")
            st.error("Error displaying metrics data")
    
    def render(
        self,
        min_projects: int = 1,
        max_companies: int = 25
    ):
        """
        Render price cut and market share analysis table (without charts)
        
        Args:
            min_projects: Minimum projects for a company to be included
            max_companies: Max number of companies to analyze individually
        """
        try:
            st.subheader("📉 Price Cut & Market Share Analysis")
            
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                show_min_projects = st.slider(
                    "Minimum Projects per Company",
                    min_value=1,
                    max_value=10,
                    value=min_projects,
                    key=f"{self.key_prefix}_min_projects"
                )
            
            # Calculate metrics
            company_metrics = self.calculate_price_cut_metrics(
                min_projects=show_min_projects,
                max_companies=max_companies
            )
            
            if company_metrics.empty:
                st.warning("No data available for price cut analysis. Make sure the dataset includes both agreed prices and budget/estimated prices.")
                return
            
            # Display summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Total Market Value",
                    f"฿{company_metrics['sum_price_agree'].sum() / self.value_unit:,.2f}M",
                    help="Total value of all projects in the analysis"
                )
            with col2:
                avg_price_cut = company_metrics['avg_price_cut'].mean()
                delta_color = "normal" if avg_price_cut < 0 else "inverse"
                st.metric(
                    "Average Price Cut",
                    f"{avg_price_cut:.2f}%",
                    delta=f"{'Discount' if avg_price_cut < 0 else 'Premium'}",
                    delta_color=delta_color,
                    help="Average price cut across all companies (negative = discount, positive = premium)"
                )
            with col3:
                company_count = len(company_metrics) - (1 if 'Others' in company_metrics[self.company_column].values else 0)
                st.metric(
                    "Number of Companies",
                    f"{company_count}",
                    help="Number of companies in the analysis"
                )
            
            # Display detailed metrics table
            st.markdown("### 📋 Company Price Cut & Market Share Details")
            self.render_metrics_table(company_metrics)
            
            # Add export functionality
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button(
                    "📥 Export to CSV",
                    key=f"{self.key_prefix}_export_metrics"
                ):
                    # Prepare export data
                    export_df = company_metrics.copy()
                    export_df = export_df.rename(columns={
                        self.company_column: 'Company',
                        'sum_price_agree': 'Total_Value',
                        'avg_price_cut': 'Avg_Price_Cut_Pct',
                        'min_price_cut': 'Min_Price_Cut_Pct',
                        'max_price_cut': 'Max_Price_Cut_Pct',
                        'project_count': 'Project_Count',
                        'market_share': 'Market_Share_Pct',
                        'total_value_mb': 'Total_Value_M'
                    })
                    
                    # Convert to CSV
                    csv = export_df.to_csv(index=False)
                    
                    # Generate download button
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name="price_cut_market_share_analysis.csv",
                        mime="text/csv",
                        key=f"{self.key_prefix}_download_metrics"
                    )
            
            # Add note about project breakdown
            st.info("💡 For a visual breakdown of company projects, use the Company Project Breakdown component.")
            
        except Exception as e:
            logger.error(f"Error in price cut analysis: {e}")
            st.error("An error occurred while analyzing price cut data")

# Simplified function to add price cut analysis to a page
def add_price_cut_analysis(filtered_df):
    """Add price cut and market share analysis section to the page"""
    
    # Add a separator for better visual organization
    st.markdown("---")
    
    # Initialize the analyzer with filtered search results
    price_cut_analyzer = PriceCutAnalysis(
        df=filtered_df,
        price_column='sum_price_agree',
        budget_column='price_build',
        company_column='winner',
        value_unit=1e6,  # Convert to millions
        key_prefix="price_cut"
    )
    
    # Render the table-only analysis
    price_cut_analyzer.render(
        min_projects=1,
        max_companies=25
    )

# Enhanced function that combines both table and project breakdown
def add_combined_price_analysis(filtered_df):
    """Add combined price cut and project breakdown analysis to the page"""
    
    # Add a separator for better visual organization
    st.markdown("---")
    
    # Initialize the price cut analyzer
    price_cut_analyzer = PriceCutAnalysis(
        df=filtered_df,
        price_column='sum_price_agree',
        budget_column='price_build',
        company_column='winner',
        value_unit=1e6,
        key_prefix="combined_analysis"
    )
    
    # Render the price cut table analysis
    price_cut_analyzer.render(
        min_projects=1,
        max_companies=25
    )
    
    # Import and use the project breakdown component
    from components.charts.CompanyProjectBreakdown import CompanyProjectBreakdown
    
    # Initialize the project breakdown component
    breakdown = CompanyProjectBreakdown(
        df=filtered_df,
        price_column='sum_price_agree',
        budget_column='price_build',
        company_column='winner',
        project_column='project_name',
        date_column='transaction_date',
        value_unit=1e6,
        max_companies=15,
        key_prefix="combined_breakdown"
    )
    
    # Render the project breakdown visualization
    breakdown.render(
        min_projects=1,
        height=600,
        show_project_types=True
    )