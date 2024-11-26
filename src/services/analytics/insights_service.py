# src/services/analytics/insights_service.py

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class InsightsService:
    """Service for generating insights from project data"""
    
    @staticmethod
    def _validate_recent_data(df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Validate and get recent data for analysis"""
        try:
            if df.empty:
                return None
                
            max_date = df['transaction_date'].max()
            
            # If max date is in the future, use today
            today = pd.Timestamp.today()
            if max_date > today:
                max_date = today
            
            recent_cutoff = max_date - pd.DateOffset(months=3)
            recent_data = df[df['transaction_date'] >= recent_cutoff]
            
            return recent_data if not recent_data.empty else None
            
        except Exception as e:
            logger.error(f"Error validating recent data: {e}")
            return None
    
    @staticmethod
    def generate_key_insights(df: pd.DataFrame) -> List[str]:
        """Generate key insights from the data"""
        insights = []
        
        try:
            if df.empty:
                logger.warning("Empty DataFrame provided for insights generation")
                return []
            
            # Market trends
            recent_data = InsightsService._validate_recent_data(df)
            if recent_data is not None:
                avg_recent_value = recent_data['sum_price_agree'].mean()
                avg_overall_value = df['sum_price_agree'].mean()
                
                if avg_recent_value > avg_overall_value * 1.1:
                    insights.append(
                        f"Project values have increased by {((avg_recent_value/avg_overall_value - 1) * 100):.1f}% "
                        "in recent months"
                    )
                elif avg_recent_value < avg_overall_value * 0.9:
                    insights.append(
                        f"Project values have decreased by {((1 - avg_recent_value/avg_overall_value) * 100):.1f}% "
                        "in recent months"
                    )
            
            # Market concentration
            market_shares = df.groupby('winner')['sum_price_agree'].sum()
            total_market = market_shares.sum()
            top_5_share = (market_shares.nlargest(5).sum() / total_market * 100)
            
            if top_5_share > 50:
                insights.append(
                    f"Market is highly concentrated with top 5 companies holding {top_5_share:.1f}% share"
                )
            
            # Department activity
            dept_activity = df.groupby('dept_name').agg({
                'project_name': 'count',
                'sum_price_agree': 'sum'
            })
            
            most_active_dept = dept_activity['project_name'].idxmax()
            highest_value_dept = dept_activity['sum_price_agree'].idxmax()
            
            dept_share = (dept_activity.loc[most_active_dept, 'project_name'] / len(df) * 100)
            
            insights.append(
                f"{most_active_dept} is the most active department with {dept_share:.1f}% of projects"
            )
            
            if most_active_dept != highest_value_dept:
                value_share = (
                    dept_activity.loc[highest_value_dept, 'sum_price_agree'] / 
                    df['sum_price_agree'].sum() * 100
                )
                insights.append(
                    f"{highest_value_dept} leads in project value with {value_share:.1f}% of total spending"
                )
            
            # Seasonal patterns
            monthly_stats = df.groupby(df['transaction_date'].dt.month).agg({
                'project_name': 'count',
                'sum_price_agree': 'mean'
            })
            
            peak_month = monthly_stats['project_name'].idxmax()
            peak_value_month = monthly_stats['sum_price_agree'].idxmax()
            
            month_name = pd.Timestamp(year=2000, month=peak_month, day=1).strftime('%B')
            insights.append(f"Project awards peak in {month_name}")
            
            if peak_month != peak_value_month:
                value_month_name = pd.Timestamp(year=2000, month=peak_value_month, day=1).strftime('%B')
                insights.append(f"Highest value projects tend to be awarded in {value_month_name}")
            
            # Price competition
            if df['price_build'].sum() != 0:
                avg_price_cut = ((df['sum_price_agree'].sum() / df['price_build'].sum() - 1) * 100)
                
                if avg_price_cut < -10:
                    insights.append(
                        f"High price competition with average price cuts of {abs(avg_price_cut):.1f}%"
                    )
                elif avg_price_cut > 5:
                    insights.append(
                        f"Projects typically awarded above estimate by {avg_price_cut:.1f}%"
                    )
            
            # Geographic insights
            geo_stats = df.groupby('province').agg({
                'project_name': 'count',
                'sum_price_agree': 'sum'
            })
            
            top_province_count = geo_stats['project_name'].idxmax()
            top_province_value = geo_stats['sum_price_agree'].idxmax()
            
            count_share = (geo_stats.loc[top_province_count, 'project_name'] / len(df) * 100)
            insights.append(
                f"{top_province_count} leads in project activity with {count_share:.1f}% of projects"
            )
            
            if top_province_count != top_province_value:
                value_share = (
                    geo_stats.loc[top_province_value, 'sum_price_agree'] / 
                    df['sum_price_agree'].sum() * 100
                )
                insights.append(
                    f"{top_province_value} leads in project value with {value_share:.1f}% of total spending"
                )
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return []
