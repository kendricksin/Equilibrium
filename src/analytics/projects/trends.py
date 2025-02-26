# src/analytics/projects/trends.py

import pandas as pd
import numpy as np
from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ProjectTrends:
    """Analyzes trends in project data over time"""
    
    def __init__(self):
        """Initialize ProjectTrends analyzer"""
        pass
    
    def analyze_monthly_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze monthly trends in project data
        
        Args:
            df: DataFrame containing project data
        
        Returns:
            Dictionary containing trend analysis results
        """
        try:
            # Create copy of dataframe
            df = df.copy()
            
            # Convert date and ensure proper sorting
            df['transaction_date'] = pd.to_datetime(df['transaction_date'])
            df = df.sort_values('transaction_date')
            
            # Calculate monthly aggregates
            monthly_data = df.groupby(pd.Grouper(key='transaction_date', freq='M')).agg({
                'project_name': 'count',
                'sum_price_agree': 'sum',
                'winner': 'nunique'
            }).reset_index()
            
            # Rename columns for clarity
            monthly_data.columns = ['date', 'project_count', 'total_value', 'unique_companies']
            
            # Calculate moving averages
            monthly_data['ma_count_3m'] = monthly_data['project_count'].rolling(window=3).mean()
            monthly_data['ma_value_3m'] = monthly_data['total_value'].rolling(window=3).mean()
            
            # Calculate year-over-year growth rates
            monthly_data['yoy_count'] = monthly_data['project_count'].pct_change(periods=12)
            monthly_data['yoy_value'] = monthly_data['total_value'].pct_change(periods=12)
            
            # Calculate summary statistics
            summary = {
                'total_months': len(monthly_data),
                'avg_monthly_projects': monthly_data['project_count'].mean(),
                'avg_monthly_value': monthly_data['total_value'].mean(),
                'max_monthly_projects': monthly_data['project_count'].max(),
                'max_monthly_value': monthly_data['total_value'].max(),
                'latest_month_projects': monthly_data['project_count'].iloc[-1],
                'latest_month_value': monthly_data['total_value'].iloc[-1],
                'latest_yoy_count': monthly_data['yoy_count'].iloc[-1],
                'latest_yoy_value': monthly_data['yoy_value'].iloc[-1]
            }
            
            # Calculate seasonality
            monthly_data['month'] = monthly_data['date'].dt.month
            seasonal_patterns = monthly_data.groupby('month').agg({
                'project_count': 'mean',
                'total_value': 'mean'
            }).reset_index()
            
            return {
                'monthly_data': monthly_data,
                'summary': summary,
                'seasonality': seasonal_patterns
            }
            
        except Exception as e:
            logger.error(f"Error analyzing monthly trends: {e}")
            raise
    
    def analyze_value_distribution(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze distribution of project values over time
        
        Args:
            df: DataFrame containing project data
        
        Returns:
            Dictionary containing value distribution analysis
        """
        try:
            # Create copy and convert values to millions
            df = df.copy()
            df['value_millions'] = df['sum_price_agree'] / 1e6
            
            # Define value ranges
            VALUE_RANGES = [
                {'name': '>300M', 'min': 300, 'max': float('inf')},
                {'name': '100-300M', 'min': 100, 'max': 300},
                {'name': '50-100M', 'min': 50, 'max': 100},
                {'name': '10-50M', 'min': 10, 'max': 50},
                {'name': '0-10M', 'min': 0, 'max': 10}
            ]
            
            # Analyze distribution by range
            range_stats = []
            for value_range in VALUE_RANGES:
                range_df = df[
                    (df['value_millions'] >= value_range['min']) &
                    (df['value_millions'] < value_range['max'])
                ]
                
                if not range_df.empty:
                    stats = {
                        'range': value_range['name'],
                        'count': len(range_df),
                        'total_value': range_df['value_millions'].sum(),
                        'avg_value': range_df['value_millions'].mean(),
                        'min_value': range_df['value_millions'].min(),
                        'max_value': range_df['value_millions'].max()
                    }
                    range_stats.append(stats)
            
            return {
                'value_ranges': range_stats,
                'total_projects': len(df),
                'total_value': df['value_millions'].sum()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing value distribution: {e}")
            raise
    
    def get_trend_insights(self, trends: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Generate insights from trend analysis
        
        Args:
            trends: Dictionary containing trend analysis results
        
        Returns:
            List of insight dictionaries with title and description
        """
        insights = []
        summary = trends['summary']
        
        try:
            # Growth trends
            if summary['latest_yoy_count'] > 0:
                insights.append({
                    'title': 'Project Growth',
                    'description': f"Project count increased by {summary['latest_yoy_count']*100:.1f}% compared to last year"
                })
            elif summary['latest_yoy_count'] < 0:
                insights.append({
                    'title': 'Project Decline',
                    'description': f"Project count decreased by {abs(summary['latest_yoy_count'])*100:.1f}% compared to last year"
                })
            
            # Value trends
            if summary['latest_yoy_value'] > 0:
                insights.append({
                    'title': 'Value Growth',
                    'description': f"Project value increased by {summary['latest_yoy_value']*100:.1f}% compared to last year"
                })
            elif summary['latest_yoy_value'] < 0:
                insights.append({
                    'title': 'Value Decline',
                    'description': f"Project value decreased by {abs(summary['latest_yoy_value'])*100:.1f}% compared to last year"
                })
            
            # Activity level
            current_vs_avg = summary['latest_month_projects'] / summary['avg_monthly_projects']
            if current_vs_avg > 1.2:
                insights.append({
                    'title': 'High Activity',
                    'description': f"Current month shows {(current_vs_avg-1)*100:.1f}% more projects than average"
                })
            elif current_vs_avg < 0.8:
                insights.append({
                    'title': 'Low Activity',
                    'description': f"Current month shows {(1-current_vs_avg)*100:.1f}% fewer projects than average"
                })
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return [] 