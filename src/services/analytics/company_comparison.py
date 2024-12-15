# src/services/analytics/company_comparison_service.py

import pandas as pd
import numpy as np
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class CompanyComparisonService:
    """Service for analyzing and comparing companies"""
    
    @staticmethod
    def calculate_price_cuts(df: pd.DataFrame, companies: List[str]) -> pd.DataFrame:
        """Calculate price cut metrics for selected companies"""
        try:
            # Filter for selected companies
            company_df = df[df['winner'].isin(companies)]
            
            # Calculate metrics per company
            metrics = []
            for company in companies:
                company_data = company_df[company_df['winner'] == company]
                if not company_data.empty:
                    total_agreed = company_data['sum_price_agree'].sum()
                    total_build = company_data['price_build'].sum()
                    price_cut = ((total_agreed / total_build) - 1) * 100
                    
                    metrics.append({
                        'company_name': company,
                        'price_cut_percent': price_cut,
                        'avg_price_agree': company_data['sum_price_agree'].mean(),
                        'project_count': len(company_data)
                    })
            
            return pd.DataFrame(metrics).sort_values('price_cut_percent', ascending=True)
            
        except Exception as e:
            logger.error(f"Error calculating price cuts: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def calculate_yearly_price_cuts(df: pd.DataFrame, companies: List[str]) -> pd.DataFrame:
        """Calculate yearly price cut trends for selected companies"""
        try:
            # Filter for selected companies
            company_df = df[df['winner'].isin(companies)]
            
            # Add budget year if not present
            if 'budget_year' not in company_df.columns:
                company_df['budget_year'] = company_df['transaction_date'].dt.year
            
            # Calculate yearly price cuts per company
            yearly_cuts = []
            
            for company in companies:
                company_data = company_df[company_df['winner'] == company]
                if not company_data.empty:
                    yearly_data = company_data.groupby('budget_year').agg({
                        'sum_price_agree': 'sum',
                        'price_build': 'sum'
                    })
                    
                    yearly_data['price_cut_percent'] = (
                        (yearly_data['sum_price_agree'] / yearly_data['price_build'] - 1) * 100
                    )
                    
                    for year, row in yearly_data.iterrows():
                        yearly_cuts.append({
                            'company_name': company,
                            'year': year,
                            'price_cut_percent': row['price_cut_percent']
                        })
            
            return pd.DataFrame(yearly_cuts)
            
        except Exception as e:
            logger.error(f"Error calculating yearly price cuts: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_company_details(df: pd.DataFrame, company_name: str) -> Dict[str, Any]:
        """Get detailed metrics for a specific company"""
        try:
            company_data = df[df['winner'] == company_name]
            if company_data.empty:
                return {}
            
            total_agreed = company_data['sum_price_agree'].sum()
            total_build = company_data['price_build'].sum()
            
            details = {
                'total_projects': len(company_data),
                'total_value': total_agreed,
                'avg_project_value': company_data['sum_price_agree'].mean(),
                'price_cut_percent': ((total_agreed / total_build) - 1) * 100,
                'departments': company_data['dept_name'].nunique(),
                'years_active': company_data['budget_year'].nunique(),
                'largest_project': company_data['sum_price_agree'].max(),
                'smallest_project': company_data['sum_price_agree'].min()
            }
            
            return details
            
        except Exception as e:
            logger.error(f"Error getting company details: {e}")
            return {}