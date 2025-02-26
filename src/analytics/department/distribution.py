# src/analytics/department/distribution.py

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DepartmentDistribution:
    """Analytics service for department distribution analysis"""
    
    @staticmethod
    def analyze_project_distribution(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze project distribution across departments
        
        Args:
            df: DataFrame with project data
            
        Returns:
            Dict containing distribution analysis
        """
        try:
            # Calculate project distribution
            dept_dist = df.groupby('dept_name').agg({
                'id': 'count',
                'sum_price_agree': 'sum'
            }).reset_index()
            
            # Calculate percentages
            total_projects = dept_dist['id'].sum()
            total_value = dept_dist['sum_price_agree'].sum()
            
            dept_dist['project_percentage'] = (dept_dist['id'] / total_projects * 100)
            dept_dist['value_percentage'] = (dept_dist['sum_price_agree'] / total_value * 100)
            
            # Calculate concentration metrics
            gini_coefficient = DepartmentDistribution._calculate_gini(dept_dist['sum_price_agree'])
            
            return {
                'distribution': dept_dist.to_dict('records'),
                'gini_coefficient': gini_coefficient,
                'top_5_departments': dept_dist.nlargest(5, 'sum_price_agree')[
                    ['dept_name', 'sum_price_agree', 'value_percentage']
                ].to_dict('records')
            }
            
        except Exception as e:
            logger.error(f"Error analyzing project distribution: {e}")
            return {}
    
    @staticmethod
    def analyze_company_distribution(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze company distribution within departments
        
        Args:
            df: DataFrame with project data
            
        Returns:
            Dict containing company distribution analysis
        """
        try:
            # Calculate company distribution by department
            dept_company_dist = df.groupby('dept_name').agg({
                'winner': ['nunique', lambda x: list(x.unique())],
                'sum_price_agree': 'sum'
            }).reset_index()
            
            dept_company_dist.columns = [
                'department', 'unique_companies', 'company_list', 'total_value'
            ]
            
            # Calculate concentration for each department
            dept_company_dist['concentration'] = dept_company_dist.apply(
                lambda x: len(x['company_list']) / df['winner'].nunique() * 100,
                axis=1
            )
            
            return {
                'department_companies': dept_company_dist.to_dict('records'),
                'avg_companies_per_dept': dept_company_dist['unique_companies'].mean(),
                'max_companies_dept': dept_company_dist.loc[
                    dept_company_dist['unique_companies'].idxmax(),
                    'department'
                ]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing company distribution: {e}")
            return {}
    
    @staticmethod
    def _calculate_gini(values: pd.Series) -> float:
        """Calculate Gini coefficient for distribution analysis"""
        try:
            sorted_values = np.sort(values)
            n = len(values)
            index = np.arange(1, n + 1)
            return ((2 * np.sum(index * sorted_values)) / (n * np.sum(sorted_values))) - (
                (n + 1) / n
            )
        except Exception as e:
            logger.error(f"Error calculating Gini coefficient: {e}")
            return 0.0 