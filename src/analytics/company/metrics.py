# src/analytics/company/metrics.py

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CompanyMetrics:
    """Service for calculating company-specific metrics"""
    
    @staticmethod
    def calculate_basic_metrics(df: pd.DataFrame, company: str) -> Dict[str, Any]:
        """
        Calculate basic company metrics
        
        Args:
            df: DataFrame with project data
            company: Company name
            
        Returns:
            Dict containing basic metrics
        """
        try:
            company_data = df[df['winner'] == company]
            
            return {
                'total_projects': len(company_data),
                'total_value': company_data['sum_price_agree'].sum(),
                'avg_project_value': company_data['sum_price_agree'].mean(),
                'departments_worked': company_data['dept_name'].nunique(),
                'first_project_date': company_data['transaction_date'].min(),
                'latest_project_date': company_data['transaction_date'].max(),
                'active_years': company_data['transaction_date'].dt.year.nunique()
            }
            
        except Exception as e:
            logger.error(f"Error calculating basic metrics: {e}")
            return {}
    
    @staticmethod
    def calculate_performance_metrics(df: pd.DataFrame, company: str) -> Dict[str, Any]:
        """
        Calculate performance metrics for a company
        
        Args:
            df: DataFrame with project data
            company: Company name
            
        Returns:
            Dict containing performance metrics
        """
        try:
            company_data = df[df['winner'] == company]
            all_projects = len(df)
            
            # Calculate win rate by department
            dept_win_rates = {}
            for dept in company_data['dept_name'].unique():
                dept_projects = df[df['dept_name'] == dept]
                dept_wins = company_data[company_data['dept_name'] == dept]
                dept_win_rates[dept] = len(dept_wins) / len(dept_projects)
            
            return {
                'overall_win_rate': len(company_data) / all_projects,
                'department_win_rates': dept_win_rates,
                'avg_price_difference': ((company_data['sum_price_agree'] / 
                                        company_data['price_build']) - 1).mean()
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return {} 