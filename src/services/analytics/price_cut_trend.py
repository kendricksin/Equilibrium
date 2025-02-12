# src/services/analytics/price_cut_trend.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class CompanyPriceCutAnalysis:
    """Service for analyzing company price cut trends over time"""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with project DataFrame
        
        Args:
            df (pd.DataFrame): Project data with required columns
        """
        self.df = df.copy()
        # Ensure datetime
        self.df['transaction_date'] = pd.to_datetime(self.df['transaction_date'])
        
    def get_top_companies(self, n: int = 10) -> List[str]:
        """
        Get top N companies by total project value
        
        Args:
            n (int): Number of companies to return
            
        Returns:
            List[str]: List of company names
        """
        try:
            company_totals = (
                self.df.groupby('winner')['sum_price_agree']
                .sum()
                .sort_values(ascending=False)
                .head(n)
            )
            return company_totals.index.tolist()
        except Exception as e:
            logger.error(f"Error getting top companies: {e}")
            return []
    
    def calculate_price_cut_trends(
        self,
        companies: List[str],
        period: str = 'Q'
    ) -> pd.DataFrame:
        """
        Calculate price cut trends with proper date handling
        """
        """
        Calculate price cut trends for specified companies
        
        Args:
            companies (List[str]): List of companies to analyze
            period (str): Time period for grouping ('M' for monthly, 'Q' for quarterly, 'Y' for yearly)
            
        Returns:
            pd.DataFrame: Price cut trends data
        """
        try:
            # Filter for selected companies
            company_df = self.df[self.df['winner'].isin(companies)]
            
            # Add period column and ensure proper sorting
            company_df['period'] = company_df['transaction_date'].dt.to_period(period)
            company_df['period_start'] = company_df['period'].dt.start_time
            
            # Calculate price cuts by period and company
            trends = []
            
            # Get full date range to ensure continuous timeline
            date_range = pd.period_range(
                start=company_df['period'].min(),
                end=company_df['period'].max(),
                freq=period
            )
            
            for company in companies:
                company_data = company_df[company_df['winner'] == company]
                
                # Create template with all periods
                period_template = pd.DataFrame({'period': date_range})
                
                # Group by period
                period_data = (
                    company_data.groupby('period')
                    .agg({
                        'sum_price_agree': 'sum',
                        'price_build': 'sum',
                        'project_name': 'count'  # Count projects for tooltip
                    })
                    .reset_index()
                )
                
                # Merge with template to ensure all periods are present
                period_data = pd.merge(
                    period_template,
                    period_data,
                    on='period',
                    how='left'
                ).fillna(0)
                
                # Calculate price cut percentage
                period_data['price_cut'] = (
                    (period_data['sum_price_agree'] / period_data['price_build'] - 1) * 100
                )
                
                # Add company column
                period_data['company'] = company
                trends.append(period_data)
            
            if not trends:
                return pd.DataFrame()
                
            return pd.concat(trends, ignore_index=True)
            
        except Exception as e:
            logger.error(f"Error calculating price cut trends: {e}")
            return pd.DataFrame()
    
    def create_trend_visualization(
        self,
        trend_data: pd.DataFrame,
        title: Optional[str] = None,
        height: int = 600,
        legend_position: str = 'bottom'  # 'bottom' or 'right'
    ) -> go.Figure:
        """
        Create line chart visualization of price cut trends
        
        Args:
            trend_data (pd.DataFrame): Price cut trend data
            title (Optional[str]): Chart title
            height (int): Chart height
            
        Returns:
            go.Figure: Plotly figure object
        """
        try:
            fig = go.Figure()
            
            # Add line for each company
            for company in trend_data['company'].unique():
                company_data = trend_data[trend_data['company'] == company]
                
                fig.add_trace(go.Scatter(
                    x=[str(p) for p in company_data['period']],
                    y=company_data['price_cut'],
                    name=company,
                    mode='lines+markers',
                    line=dict(width=2),
                    marker=dict(size=6),
                    hovertemplate=(
                        "<b>%{x}</b><br>" +
                        f"<b>{company}</b><br>" +
                        "Price Cut: %{y:.1f}%<br>" +
                        "Projects: %{customdata[0]}<br>" +
                        "Value: ฿%{customdata[1]:.1f}M<br>" +
                        "<extra></extra>"
                    ),
                    customdata=list(zip(
                        company_data['project_name'],
                        company_data['sum_price_agree'] / 1e6
                    ))
                ))
            
            # Update layout with configurable legend position
            legend_config = (
                dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.3,
                    xanchor="center",
                    x=0.5
                ) if legend_position == 'bottom' else
                dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=1.05
                )
            )
            
            # Update layout
            fig.update_layout(
                title=title or "Company Price Cut Trends",
                height=height + (150 if legend_position == 'bottom' else 0),
                hovermode='x unified',
                xaxis_title="Period",
                yaxis_title="Price Cut (%)",
                showlegend=True,
                legend=legend_config,
                margin=dict(l=60, r=20, t=40, b=40)
            )
            
            # Add zero line reference
            fig.add_hline(
                y=0,
                line_dash="dash",
                line_color="gray",
                opacity=0.5
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating trend visualization: {e}")
            raise
    
    def get_trend_statistics(self, trend_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate summary statistics for price cut trends
        
        Args:
            trend_data (pd.DataFrame): Price cut trend data
            
        Returns:
            Dict[str, Any]: Summary statistics
        """
        try:
            stats = {}
            
            for company in trend_data['company'].unique():
                company_data = trend_data[trend_data['company'] == company]
                
                stats[company] = {
                    'avg_price_cut': company_data['price_cut'].mean(),
                    'min_price_cut': company_data['price_cut'].min(),
                    'max_price_cut': company_data['price_cut'].max(),
                    'latest_price_cut': company_data.iloc[-1]['price_cut'],
                    'trend': 'up' if (
                        company_data['price_cut'].iloc[-1] >
                        company_data['price_cut'].iloc[-2]
                    ) else 'down',
                    'periods_analyzed': len(company_data)
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating trend statistics: {e}")
            return {}
        
def PriceCutAnalysis(df: pd.DataFrame, key_prefix: str = ""):
    """
    Component for analyzing and visualizing company price cut trends
    
    Args:
        df (pd.DataFrame): Project data DataFrame
        key_prefix (str): Prefix for component keys
    """
    st.markdown("### 📈 Company Price Cut Trends")
    
    # Initialize analysis service
    analyzer = CompanyPriceCutAnalysis(df)
    
    # Controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        num_companies = st.slider(
            "Number of top companies to analyze",
            min_value=5,
            max_value=20,
            value=10,
            key=f"{key_prefix}num_companies"
        )
    
    with col2:
        period = st.selectbox(
            "Analysis Period",
            options=["Monthly", "Quarterly", "Yearly"],
            index=1,
            key=f"{key_prefix}period"
        )
        
    with col3:
        legend_pos = st.selectbox(
            "Legend Position",
            options=["Bottom", "Right"],
            index=0,
            key=f"{key_prefix}legend_pos"
        )
    
    # Get period code
    period_map = {"Monthly": "M", "Quarterly": "Q", "Yearly": "Y"}
    period_code = period_map[period]
    
    # Get top companies
    top_companies = analyzer.get_top_companies(num_companies)
    
    if not top_companies:
        st.warning("No company data available for analysis")
        return
    
    # Calculate trends
    trend_data = analyzer.calculate_price_cut_trends(top_companies, period_code)
    
    if trend_data.empty:
        st.warning("No trend data available for the selected parameters")
        return
    
    # Create visualization
    fig = analyzer.create_trend_visualization(
        trend_data,
        title=f"Price Cut Trends - Top {num_companies} Companies by Value",
        legend_position=legend_pos.lower()
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Show statistics
    st.markdown("#### Trend Statistics")
    stats = analyzer.get_trend_statistics(trend_data)
    
    # Create three columns for statistics
    cols = st.columns(3)
    
    for i, (company, company_stats) in enumerate(stats.items()):
        col_idx = i % 3
        with cols[col_idx]:
            st.markdown(f"**{company}**")
            st.markdown(f"""
            Average Cut: {company_stats['avg_price_cut']:.1f}%  
            Range: {company_stats['min_price_cut']:.1f}% to {company_stats['max_price_cut']:.1f}%  
            Latest: {company_stats['latest_price_cut']:.1f}% ({company_stats['trend']})  
            Periods: {company_stats['periods_analyzed']}
            """)
    
    # Add export functionality
    if st.button("📥 Export Analysis Data", key=f"{key_prefix}export"):
        # Prepare export data
        export_data = trend_data.copy()
        export_data['period'] = export_data['period'].astype(str)
        
        # Convert to CSV
        csv = export_data.to_csv(index=False)
        
        st.download_button(
            "📥 Download CSV",
            csv,
            "price_cut_trends.csv",
            "text/csv",
            key=f"{key_prefix}download"
        )