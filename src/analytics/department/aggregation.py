# src/analytics/department/aggregation.py

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DepartmentAnalytics:
    """Analytics service for department-level analysis"""
    
    @staticmethod
    def calculate_department_metrics(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate metrics for all departments
        
        Args:
            df: DataFrame with project data
            
        Returns:
            Dict containing department metrics
        """
        try:
            dept_metrics = df.groupby('dept_name').agg({
                'sum_price_agree': ['sum', 'mean', 'count'],
                'winner': 'nunique'
            }).reset_index()
            
            dept_metrics.columns = [
                'department', 'total_value', 'avg_project_value',
                'project_count', 'unique_companies'
            ]
            
            # Calculate percentages
            total_value = dept_metrics['total_value'].sum()
            total_projects = dept_metrics['project_count'].sum()
            
            dept_metrics['value_percentage'] = (dept_metrics['total_value'] / 
                                              total_value * 100)
            dept_metrics['project_percentage'] = (dept_metrics['project_count'] / 
                                                total_projects * 100)
            
            return dept_metrics.to_dict('records')
            
        except Exception as e:
            logger.error(f"Error calculating department metrics: {e}")
            return []
    
    @staticmethod
    def analyze_department_trends(
        df: pd.DataFrame,
        department: str
    ) -> Dict[str, Any]:
        """
        Analyze trends for a specific department
        
        Args:
            df: DataFrame with project data
            department: Department name
            
        Returns:
            Dict containing trend analysis
        """
        try:
            dept_data = df[df['dept_name'] == department].copy()
            dept_data['year'] = pd.to_datetime(dept_data['transaction_date']).dt.year
            
            yearly_metrics = dept_data.groupby('year').agg({
                'sum_price_agree': ['sum', 'mean', 'count'],
                'winner': 'nunique'
            })
            
            return {
                'yearly_spend': yearly_metrics['sum_price_agree']['sum'].to_dict(),
                'yearly_projects': yearly_metrics['sum_price_agree']['count'].to_dict(),
                'yearly_companies': yearly_metrics['winner']['nunique'].to_dict(),
                'avg_project_value': yearly_metrics['sum_price_agree']['mean'].to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing department trends: {e}")
            return {} 