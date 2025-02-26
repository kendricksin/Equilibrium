# src/services/analytics/company_projects.py

import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Any
import random

class CompanyProjectsService:
    """Service for analyzing project distribution across companies"""
    
    # Safe, light colors from Plotly's built-in colors
    SAFE_COLORS = [
        '#FFB6C1',  # lightpink
        '#98FB98',  # palegreen
        '#87CEFA',  # lightskyblue
        '#DDA0DD',  # plum
        '#F0E68C',  # khaki
        '#E6E6FA',  # lavender
        '#FFA07A',  # lightsalmon
        '#B0E0E6',  # powderblue
        '#FFE4B5',  # moccasin
        '#F5DEB3',  # wheat
        '#FFDAB9',  # peachpuff
        '#AFEEEE',  # paleturquoise
        '#D8BFD8',  # thistle
        '#DEB887',  # burlywood
        '#FA8072',  # salmon
    ]
    
    VALUE_RANGES = [
        {'name': '>300M', 'min': 300, 'max': float('inf'), 'color': '#87CEFA'},
        {'name': '100-300M', 'min': 100, 'max': 300, 'color': '#FFB6C1'},
        {'name': '50-100M', 'min': 50, 'max': 100, 'color': '#98FB98'},
        {'name': '10-50M', 'min': 10, 'max': 50, 'color': '#DDA0DD'},
        {'name': '0-10M', 'min': 0, 'max': 10, 'color': '#F0E68C'}
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
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Creating chart for range: {range_name}")
        logger.info(f"Input DataFrame shape: {df.shape}")
        
        if df.empty:
            logger.error(f"Empty DataFrame for range {range_name}")
            raise ValueError(f"Empty DataFrame for range {range_name}")
        
        # Get companies sorted by total value
        company_totals = df.groupby('winner')['value_millions'].sum()
        companies = company_totals.sort_values(ascending=False).index
        
        # Calculate project counts per company
        project_counts = df.groupby('winner').size()
        
        fig = go.Figure()
        
        # Create a color map for years using safe colors
        years = sorted(df['transaction_date'].dt.year.unique())
        year_colors = {
            year: CompanyProjectsService.SAFE_COLORS[i % len(CompanyProjectsService.SAFE_COLORS)]
            for i, year in enumerate(years)
        }
        
        # Add bars for each project
        for _, row_data in df.iterrows():
            # Calculate price cut percentage with validation
            try:
                if row_data['price_build'] == 0:
                    logger.error(f"Zero price_build value found for project {row_data['project_name']}")
                    price_cut = 0
                else:
                    price_cut = ((row_data['sum_price_agree'] / row_data['price_build']) - 1) * 100
                    if abs(price_cut) > 100:
                        logger.warning(f"Large price cut detected ({price_cut:.2f}%) for project {row_data['project_name']}")
            except Exception as e:
                logger.error(f"Error calculating price cut for project {row_data['project_name']}: {str(e)}")
                price_cut = 0
            
            # Get year and its assigned color
            year = row_data['transaction_date'].year
            year_color = year_colors[year]

            # Only show in legend if it's the first occurrence of this year
            show_in_legend = str(year) not in [trace.name for trace in fig.data]
            
            fig.add_trace(
                go.Bar(
                    name=str(year),
                    x=[row_data['winner']],
                    y=[row_data['value_millions']],
                    orientation='v',
                    showlegend=show_in_legend,
                    marker=dict(
                        color=year_color,
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
                        bgcolor="rgba(255, 255, 255, 0.7)",
                        bordercolor="rgba(0, 0, 0, 0.1)",
                        font_size=12,
                        font_family="Arial",
                        namelength=-1
                    )
                )
            )
        
        # Add project count annotations at the top of each bar stack
        for company in companies:
            total_value = company_totals[company]
            project_count = project_counts[company]
            
            fig.add_annotation(
                x=company,
                y=total_value,
                text=f"{project_count} projects",
                showarrow=False,
                yshift=10,
                font=dict(size=10),
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0, 0, 0, 0.1)",
                borderwidth=1,
                borderpad=4
            )
        
        # Update layout
        fig.update_layout(
            title=f"Projects {range_name}",
            height=500,
            showlegend=True,
            legend=dict(
                title="Transaction Year",
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            barmode='stack',
            bargap=0.2,
            margin=dict(t=40, l=20, r=20, b=100),
            xaxis=dict(
                categoryorder='array',
                categoryarray=companies,
                title='Company',
                tickangle=45
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