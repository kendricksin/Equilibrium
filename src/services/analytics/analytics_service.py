# src/services/analytics/analytics_service.py

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service for analyzing project data"""
    
    @staticmethod
    def _validate_dataframe(df: pd.DataFrame) -> bool:
        """Validate required columns and data types"""
        try:
            required_columns = [
                'transaction_date', 'winner', 'sum_price_agree',
                'price_build', 'dept_name', 'project_name'
            ]
            
            # Check required columns
            if not all(col in df.columns for col in required_columns):
                logger.error("Missing required columns in DataFrame")
                return False
            
            # Check if DataFrame is empty
            if df.empty:
                logger.warning("Empty DataFrame provided")
                return False
            
            # Ensure date column is datetime
            if not pd.api.types.is_datetime64_any_dtype(df['transaction_date']):
                logger.error("transaction_date column is not datetime type")
                return False
            
            # Ensure numeric columns are numeric
            numeric_columns = ['sum_price_agree', 'price_build']
            for col in numeric_columns:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    logger.error(f"{col} is not numeric type")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating DataFrame: {e}")
            return False
    
    @staticmethod
    def _get_safe_date_range(df: pd.DataFrame) -> Tuple[datetime, datetime]:
        """Get safe date range for analysis"""
        try:
            min_date = df['transaction_date'].min()
            max_date = df['transaction_date'].max()
            
            # If max_date is in the future, use today
            today = pd.Timestamp.today()
            if max_date > today:
                max_date = today
            
            # Ensure we have at least one month of data
            if min_date >= max_date:
                min_date = max_date - timedelta(days=30)
            
            return min_date, max_date
            
        except Exception as e:
            logger.error(f"Error getting date range: {e}")
            return datetime.now() - timedelta(days=30), datetime.now()
    
    @staticmethod
    def analyze_company_performance(
        df: pd.DataFrame,
        company_names: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Analyze company performance metrics"""
        try:
            if not AnalyticsService._validate_dataframe(df):
                return pd.DataFrame()
            
            # Filter for specific companies if provided
            if company_names:
                df = df[df['winner'].isin(company_names)]
            
            # Calculate metrics by company
            metrics = df.groupby('winner').agg({
                'project_name': 'count',
                'sum_price_agree': ['sum', 'mean', 'std'],
                'dept_name': 'nunique'
            })
            
            # Flatten column names and rename
            metrics.columns = [
                'total_projects',
                'total_value',
                'avg_value',
                'value_std',
                'unique_departments'
            ]
            
            # Calculate market share
            total_market = df['sum_price_agree'].sum()
            metrics['market_share'] = (metrics['total_value'] / total_market * 100).round(2)
            
            # Calculate price competitiveness
            company_price_cuts = []
            for company in metrics.index:
                company_df = df[df['winner'] == company]
                if not company_df.empty and company_df['price_build'].sum() != 0:
                    price_cut = ((company_df['sum_price_agree'].sum() / 
                                company_df['price_build'].sum() - 1) * 100)
                    company_price_cuts.append(price_cut)
                else:
                    company_price_cuts.append(0)
            
            metrics['price_cut_percentage'] = company_price_cuts
            
            # Calculate win rates
            min_date, max_date = AnalyticsService._get_safe_date_range(df)
            time_periods = pd.date_range(start=min_date, end=max_date, freq='M')
            
            win_rates = []
            for company in metrics.index:
                company_projects = df[df['winner'] == company]['transaction_date']
                if not company_projects.empty:
                    monthly_wins = pd.Series(0, index=time_periods)
                    for date in company_projects:
                        period = date.to_period('M').to_timestamp()
                        if period in monthly_wins.index:
                            monthly_wins[period] += 1
                    win_rates.append(monthly_wins.mean())
                else:
                    win_rates.append(0)
            
            metrics['avg_monthly_wins'] = win_rates
            
            # Round numeric columns
            numeric_cols = ['total_value', 'avg_value', 'value_std', 'market_share', 
                          'price_cut_percentage', 'avg_monthly_wins']
            metrics[numeric_cols] = metrics[numeric_cols].round(2)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error analyzing company performance: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def analyze_competitive_landscape(df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze competitive landscape and market concentration"""
        try:
            if not AnalyticsService._validate_dataframe(df):
                return {}
            
            # Calculate market shares
            market_shares = (
                df.groupby('winner')['sum_price_agree'].sum() / 
                df['sum_price_agree'].sum() * 100
            ).round(2)
            
            # Calculate HHI
            hhi = (market_shares ** 2).sum()
            
            # Sort shares for concentration metrics
            sorted_shares = market_shares.sort_values(ascending=False)
            
            # Determine market concentration
            concentration = (
                'High' if hhi > 2500 else
                'Moderate' if hhi > 1500 else
                'Low'
            )
            
            analysis = {
                'hhi': round(hhi, 2),
                'market_concentration': concentration,
                'top_3_concentration': round(sorted_shares.head(3).sum(), 2),
                'top_5_concentration': round(sorted_shares.head(5).sum(), 2),
                'top_10_concentration': round(sorted_shares.head(10).sum(), 2),
                'total_players': len(market_shares),
                'market_shares': market_shares.to_dict()
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing competitive landscape: {e}")
            return {}
