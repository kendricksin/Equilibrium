# src/services/analytics/insights_service.py

import pandas as pd
import numpy as np
from typing import Dict, Any, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class InsightsService:
    """Service for generating insights from project data"""
    
    @staticmethod
    def generate_key_insights(df: pd.DataFrame) -> List[str]:
        """Generate key insights from the data"""
        insights = []
        
        try:
            # Market trends
            recent_months = df[df['transaction_date'] >= df['transaction_date'].max() - pd.DateOffset(months=3)]
            avg_recent_value = recent_months['sum_price_agree'].mean()
            avg_overall_value = df['sum_price_agree'].mean()
            
            if avg_recent_value > avg_overall_value * 1.1:
                insights.append("Project values have increased significantly in recent months")
            elif avg_recent_value < avg_overall_value * 0.9:
                insights.append("Project values have decreased significantly in recent months")
            
            # Market concentration
            top_5_share = (
                df.groupby('winner')['sum_price_agree'].sum().nlargest(5).sum() / 
                df['sum_price_agree'].sum() * 100
            )
            
            if top_5_share > 50:
                insights.append(f"Market is highly concentrated with top 5 companies holding {top_5_share:.1f}% share")
            
            # Department activity
            dept_activity = df.groupby('dept_name').size()
            most_active_dept = dept_activity.idxmax()
            dept_share = (dept_activity.max() / len(df) * 100)
            
            insights.append(
                f"{most_active_dept} is the most active department with {dept_share:.1f}% of projects"
            )
            
            # Seasonal patterns
            monthly_counts = df.groupby(df['transaction_date'].dt.month).size()
            peak_month = monthly_counts.idxmax()
            month_name = pd.Timestamp(year=2000, month=peak_month, day=1).strftime('%B')
            
            insights.append(f"Project awards peak in {month_name}")
            
            # Price competition
            avg_price_cut = ((df['sum_price_agree'].sum() / df['price_build'].sum() - 1) * 100)
            
            if avg_price_cut < -10:
                insights.append(f"High price competition with average price cuts of {abs(avg_price_cut):.1f}%")
            
            # Geographic insights
            top_province = df['province'].mode().iloc[0]
            province_share = (len(df[df['province'] == top_province]) / len(df) * 100)
            
            insights.append(
                f"{top_province} leads project activity with {province_share:.1f}% of projects"
            )
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return []
    
    @staticmethod
    def generate_company_insights(
        df: pd.DataFrame,
        company_name: str
    ) -> List[str]:
        """Generate insights for a specific company"""
        insights = []
        
        try:
            company_df = df[df['winner'] == company_name]
            
            if company_df.empty:
                return []
            
            # Market position
            market_share = (company_df['sum_price_agree'].sum() / df['sum_price_agree'].sum() * 100)
            position = (
                df.groupby('winner')['sum_price_agree']
                .sum()
                .sort_values(ascending=False)
                .index
                .get_loc(company_name) + 1
            )
            
            insights.append(
                f"Ranks #{position} in the market with {market_share:.1f}% market share"
            )
            
            # Specialization
            top_dept = company_df['dept_name'].mode().iloc[0]
            dept_share = (
                len(company_df[company_df['dept_name'] == top_dept]) / 
                len(company_df) * 100
            )
            
            if dept_share > 50:
                insights.append(
                    f"Specialized in {top_dept} projects ({dept_share:.1f}% of portfolio)"
                )
            
            # Growth trend
            yearly_projects = company_df.groupby(
                company_df['transaction_date'].dt.year
            )['project_name'].count()
            
            if len(yearly_projects) >= 2:
                yoy_growth = (
                    (yearly_projects.iloc[-1] / yearly_projects.iloc[-2] - 1) * 100
                )
                
                if yoy_growth > 20:
                    insights.append(f"Strong growth with {yoy_growth:.1f}% increase in projects YoY")
                elif yoy_growth < -20:
                    insights.append(f"Significant decline with {abs(yoy_growth):.1f}% decrease in projects YoY")
            
            # Price competitiveness
            avg_price_cut = (
                (company_df['sum_price_agree'].sum() / company_df['price_build'].sum() - 1) * 100
            )
            market_avg_cut = (
                (df['sum_price_agree'].sum() / df['price_build'].sum() - 1) * 100
            )
            
            if avg_price_cut < market_avg_cut - 5:
                insights.append("More aggressive pricing compared to market average")
            elif avg_price_cut > market_avg_cut + 5:
                insights.append("Premium pricing compared to market average")
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating company insights: {e}")
            return []