# src/services/analytics/company_projects.py

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Any, Tuple

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
    def create_charts(range_data: Dict[str, pd.DataFrame]) -> go.Figure:
        """Create vertical subplots for each value range"""
        # Count number of non-empty ranges
        n_ranges = sum(1 for r in CompanyProjectsService.VALUE_RANGES if r['name'] in range_data)
        
        # Create vertical subplots
        fig = make_subplots(
            rows=n_ranges, cols=1,
            subplot_titles=[f"Projects {range_name}" for range_name in range_data.keys()],
            vertical_spacing=0.05
        )
        
        # Add bars for each range
        current_row = 1
        for value_range in CompanyProjectsService.VALUE_RANGES:
            range_name = value_range['name']
            if range_name in range_data:
                df = range_data[range_name]
                
                # Get companies sorted by total value
                company_totals = df.groupby('winner')['value_millions'].sum()
                companies = company_totals.sort_values(ascending=True).index
                
                # Add bars for each project
                for _, row_data in df.iterrows():
                    fig.add_trace(
                        go.Bar(
                            name='',
                            y=[row_data['winner']],
                            x=[row_data['value_millions']],
                            orientation='h',
                            showlegend=False,
                            marker=dict(
                                color=value_range['color'],
                                line=dict(color='rgb(50, 50, 50)', width=1)  # Add outline
                            ),
                            customdata=[[
                                row_data['project_name'],
                                row_data['value_millions'],
                                row_data['transaction_date'].strftime('%Y-%m-%d')
                            ]],
                            hovertemplate=(
                                "%{customdata[0]}<br><br>" +
                                "Value: ฿%{customdata[1]:.1f}M<br>" +
                                "Date: %{customdata[2]}" +
                                "<extra></extra>"
                            ),
                            hoverlabel=dict(
                                bgcolor="white",
                                font_size=13,
                                font_family="Arial",
                                namelength=-1  # Show full text
                            )
                        ),
                        row=current_row,
                        col=1
                    )
                
                # Update axes for this subplot
                fig.update_yaxes(
                    categoryorder='array',
                    categoryarray=companies,
                    title='Company',
                    row=current_row,
                    col=1
                )
                fig.update_xaxes(
                    title='Project Value (Million ฿)',
                    row=current_row,
                    col=1
                )
                
                current_row += 1
        
        # Calculate dynamic height based on number of companies in each range
        total_companies = sum(len(df['winner'].unique()) for df in range_data.values())
        height_per_company = 25  # pixels per company
        min_height_per_plot = 200  # minimum height per subplot
        
        # Update layout
        fig.update_layout(
            height=max(total_companies * height_per_company, n_ranges * min_height_per_plot),
            title_text="Project Distribution by Value Range",
            showlegend=False,
            barmode='stack',
            bargap=0.2,
            margin=dict(t=60, l=20, r=20, b=20)
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