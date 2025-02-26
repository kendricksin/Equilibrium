# src/analytics/projects/metrics.py

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ProjectMetrics:
    """Service for calculating project metrics"""
    
    def calculate_summary_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate comprehensive summary metrics from project data
        
        Args:
            df: DataFrame containing project data
            
        Returns:
            Dictionary containing calculated metrics
        """
        try:
            metrics = {}
            
            # Basic metrics
            metrics['total_projects'] = len(df)
            metrics['total_value'] = df['sum_price_agree'].sum()
            metrics['average_value'] = df['sum_price_agree'].mean()
            metrics['unique_companies'] = df['winner'].nunique()
            
            # Calculate price cut percentage
            if 'project_money' in df.columns and 'sum_price_agree' in df.columns:
                total_budget = df['project_money'].sum()
                total_agreed = df['sum_price_agree'].sum()
                if total_budget > 0:
                    metrics['price_cut'] = ((total_agreed - total_budget) / total_budget) * 100
                else:
                    metrics['price_cut'] = 0
            
            # Purchase Methods Distribution
            purchase_methods = df['purchase_method_name'].value_counts()
            metrics['purchase_methods'] = {
                'distribution': purchase_methods.to_dict(),
                'percentages': (purchase_methods / len(df) * 100).to_dict(),
                'top_method': purchase_methods.index[0] if not purchase_methods.empty else None,
                'top_method_percentage': (purchase_methods.iloc[0] / len(df) * 100) if not purchase_methods.empty else 0
            }
            
            # Project Types Distribution
            project_types = df['project_type_name'].value_counts()
            metrics['project_types'] = {
                'distribution': project_types.to_dict(),
                'percentages': (project_types / len(df) * 100).to_dict(),
                'top_type': project_types.index[0] if not project_types.empty else None,
                'top_type_percentage': (project_types.iloc[0] / len(df) * 100) if not project_types.empty else 0
            }
            
            # Department Overview
            dept_stats = df.groupby('dept_name').agg({
                'project_name': 'count',
                'sum_price_agree': 'sum',
                'winner': 'nunique'
            }).reset_index()
            dept_stats.columns = ['dept_name', 'projects', 'value', 'companies']
            
            # Top Companies
            company_stats = df.groupby('winner').agg({
                'project_name': 'count',
                'sum_price_agree': 'sum'
            }).reset_index()
            company_stats = company_stats.sort_values('sum_price_agree', ascending=False)
            company_stats.columns = ['company', 'projects', 'value']
            
            metrics['top_companies'] = company_stats.head().to_dict('records')
            metrics['department_stats'] = dept_stats.to_dict('records')
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            return {
                'total_projects': 0,
                'total_value': 0,
                'average_value': 0,
                'unique_companies': 0,
                'price_cut': 0,
                'purchase_methods': {'distribution': {}, 'percentages': {}, 'top_method': None, 'top_method_percentage': 0},
                'project_types': {'distribution': {}, 'percentages': {}, 'top_type': None, 'top_type_percentage': 0},
                'top_companies': [],
                'department_stats': []
            }
    
    @staticmethod
    def analyze_time_distribution(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze project distribution over time
        
        Args:
            df: DataFrame with project data
            
        Returns:
            Dict containing time-based analysis
        """
        try:
            df = df.copy()
            df['year'] = pd.to_datetime(df['transaction_date']).dt.year
            df['month'] = pd.to_datetime(df['transaction_date']).dt.month
            
            yearly_stats = df.groupby('year').agg({
                'sum_price_agree': ['sum', 'mean', 'count'],
                'winner': 'nunique'
            })
            
            monthly_stats = df.groupby(['year', 'month']).agg({
                'sum_price_agree': ['sum', 'count']
            })
            
            return {
                'yearly_distribution': yearly_stats.to_dict(),
                'monthly_distribution': monthly_stats.to_dict(),
                'peak_month': monthly_stats['sum_price_agree']['count'].idxmax(),
                'peak_year': yearly_stats['sum_price_agree']['count'].idxmax()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing time distribution: {e}")
            return {} 