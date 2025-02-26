# src/analytics/company/comparison.py

from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CompanyAnalytics:
    """Analytics service for company comparison and metrics"""
    
    @staticmethod
    def calculate_competition_metrics(df: pd.DataFrame, companies: List[str]) -> Dict[str, Any]:
        """
        Calculate competition metrics between companies
        
        Args:
            df: DataFrame with project data
            companies: List of company names to analyze
            
        Returns:
            Dict containing competition matrices and metrics
        """
        try:
            # Initialize matrices
            competition_matrix = pd.DataFrame(0, index=companies, columns=companies)
            price_diff_matrix = pd.DataFrame(0.0, index=companies, columns=companies)
            dept_overlap_matrix = pd.DataFrame(0.0, index=companies, columns=companies)
            
            # Calculate metrics for each company
            company_metrics = {}
            for company in companies:
                company_projects = df[df['winner'] == company]
                if len(company_projects) > 0:
                    company_metrics[company] = {
                        'total_projects': len(company_projects),
                        'total_value': company_projects['sum_price_agree'].sum(),
                        'avg_project_value': company_projects['sum_price_agree'].mean(),
                        'departments': set(company_projects['dept_name'].unique()),
                        'win_rate': len(company_projects) / len(df)
                    }
            
            return {
                'competition_matrix': competition_matrix,
                'price_differences': price_diff_matrix,
                'department_overlap': dept_overlap_matrix,
                'company_metrics': company_metrics
            }
            
        except Exception as e:
            logger.error(f"Error calculating competition metrics: {e}")
            return {}
    
    @staticmethod
    def analyze_growth_trends(df: pd.DataFrame, company: str) -> Dict[str, Any]:
        """
        Analyze company growth trends over time
        
        Args:
            df: DataFrame with project data
            company: Company name to analyze
            
        Returns:
            Dict containing growth metrics and trends
        """
        try:
            company_data = df[df['winner'] == company].copy()
            company_data['year'] = pd.to_datetime(company_data['transaction_date']).dt.year
            
            yearly_metrics = company_data.groupby('year').agg({
                'sum_price_agree': ['sum', 'mean', 'count']
            }).reset_index()
            
            return {
                'yearly_revenue': yearly_metrics['sum_price_agree']['sum'].to_dict(),
                'yearly_project_count': yearly_metrics['sum_price_agree']['count'].to_dict(),
                'yearly_avg_project_value': yearly_metrics['sum_price_agree']['mean'].to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing growth trends: {e}")
            return {}