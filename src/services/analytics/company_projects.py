# src/services/analytics/company_projects.py

import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Any

class CompanyProjectsService:
    """Service for analyzing project distribution across companies"""
    
    VALUE_RANGES = [
        {'name': '>100M', 'min': 100, 'max': float('inf'), 'color': 'rgb(99, 110, 250)'},
        {'name': '50-100M', 'min': 50, 'max': 100, 'color': 'rgb(239, 85, 59)'},
        {'name': '10-50M', 'min': 10, 'max': 50, 'color': 'rgb(0, 204, 150)'},
        {'name': '0-10M', 'min': 0, 'max': 10, 'color': 'rgb(171, 99, 250)'}
    ]
    
    @staticmethod
    def prepare_data(df: pd.DataFrame, top_n: int = 15) -> Dict[str, pd.DataFrame]:
        """Prepare data for company projects visualization by value range"""
        # Convert to millions
        df = df.copy()
        df['value_millions'] = df['sum_price_agree'] / 1e6
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        
        # Split data by value ranges
        range_data = {}
        for value_range in CompanyProjectsService.VALUE_RANGES:
            # Filter for value range
            range_df = df[
                (df['value_millions'] >= value_range['min']) &
                (df['value_millions'] < value_range['max'])
            ].copy()
            
            if not range_df.empty:
                # Get top companies for this range
                company_totals = range_df.groupby('winner')['value_millions'].sum()
                top_companies = company_totals.sort_values(ascending=False).head(top_n).index
                
                # Filter for top companies and sort
                range_df = range_df[range_df['winner'].isin(top_companies)]
                range_df = range_df.sort_values(['winner', 'transaction_date'])
                
                range_data[value_range['name']] = range_df
        
        return range_data

    @staticmethod
    def create_chart_for_range(df: pd.DataFrame, range_name: str, color: str) -> go.Figure:
        """Create individual chart for a value range"""
        # Get companies sorted by total value
        company_totals = df.groupby('winner')['value_millions'].sum()
        companies = company_totals.sort_values(ascending=True).index
        
        fig = go.Figure()
        
        # Add bars for each project
        for _, row_data in df.iterrows():
            # Calculate price cut percentage
            price_cut = ((row_data['sum_price_agree'] / row_data['price_build']) - 1) * 100
            
            fig.add_trace(
                go.Bar(
                    name='',
                    x=[row_data['winner']],
                    y=[row_data['value_millions']],
                    orientation='v',
                    showlegend=False,
                    marker=dict(
                        color=color,
                        line=dict(color='rgb(50, 50, 50)', width=1)
                    ),
                    customdata=[[
                        row_data['project_name'],
                        row_data['value_millions'],
                        row_data['transaction_date'].strftime('%Y-%m-%d'),
                        price_cut,
                        row_data.get('province', 'N/A'),
                        row_data.get('district', 'N/A')
                    ]],
                    hovertemplate=(
                        "<b>%{customdata[0]}</b><br>" +
                        "฿%{customdata[1]:.1f}M | %{customdata[2]}<br>" +
                        "Price Cut: %{customdata[3]:.1f}%<br>" +
                        "%{customdata[4]}, %{customdata[5]}" +
                        "<extra></extra>"
                    ),
                    hoverlabel=dict(
                        bgcolor="rgba(255, 255, 255, 0.7)",  # Increased alpha
                        bordercolor="rgba(0, 0, 0, 0.1)",    # Subtle border
                        font_size=12,
                        font_family="Arial",
                        namelength=-1
                    )
                )
            )
        
        # Calculate dynamic height based on number of companies
        height = max(len(companies) * 25, 200)
        
        # Update layout
        fig.update_layout(
            title=f"Projects {range_name}",
            height=500,  # Fixed height since we're using vertical bars
            showlegend=False,
            barmode='stack',
            bargap=0.2,
            margin=dict(t=40, l=20, r=20, b=100),  # Increased bottom margin for company names
            xaxis=dict(
                categoryorder='array',
                categoryarray=companies,
                title='Company',
                tickangle=45  # Angled labels for better readability
            ),
            yaxis=dict(
                title='Project Value (Million ฿)'
            )
        )
        
        return fig
    
    @staticmethod
    def get_range_statistics(range_data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        """Calculate statistics for each value range"""
        stats = []
        for value_range in CompanyProjectsService.VALUE_RANGES:
            range_name = value_range['name']
            if range_name in range_data:
                df = range_data[range_name]
                stats.append({
                    'range': range_name,
                    'total_projects': len(df),
                    'total_companies': len(df['winner'].unique()),
                    'total_value': df['value_millions'].sum(),
                    'avg_value': df['value_millions'].mean(),
                    'color': value_range['color']
                })
            else:
                stats.append({
                    'range': range_name,
                    'total_projects': 0,
                    'total_companies': 0,
                    'total_value': 0,
                    'avg_value': 0,
                    'color': value_range['color']
                })
        return stats