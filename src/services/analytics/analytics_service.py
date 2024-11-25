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
    def calculate_basic_metrics(df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic project metrics"""
        try:
            metrics = {
                'total_projects': len(df),
                'total_value': df['sum_price_agree'].sum(),
                'avg_value': df['sum_price_agree'].mean(),
                'unique_winners': df['winner'].nunique(),
                'total_departments': df['dept_name'].nunique(),
                'date_range': {
                    'start': df['transaction_date'].min(),
                    'end': df['transaction_date'].max()
                }
            }
            return metrics
        except Exception as e:
            logger.error(f"Error calculating basic metrics: {e}")
            return {}
    
    @staticmethod
    def analyze_company_performance(
        df: pd.DataFrame,
        company_names: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Analyze company performance metrics"""
        try:
            # Filter for specific companies if provided
            if company_names:
                df = df[df['winner'].isin(company_names)]
            
            # Calculate metrics by company
            metrics = df.groupby('winner').agg({
                'project_name': 'count',
                'sum_price_agree': ['sum', 'mean', 'std'],
                'price_build': lambda x: ((df.loc[x.index, 'sum_price_agree'].sum() / x.sum()) - 1) * 100,
                'dept_name': 'nunique'
            })
            
            # Flatten column names
            metrics.columns = [
                'total_projects',
                'total_value',
                'avg_value',
                'value_std',
                'price_cut_percentage',
                'unique_departments'
            ]
            
            # Calculate market share
            total_market = df['sum_price_agree'].sum()
            metrics['market_share'] = (metrics['total_value'] / total_market) * 100
            
            # Calculate project win rate over time
            time_periods = pd.date_range(
                start=df['transaction_date'].min(),
                end=df['transaction_date'].max(),
                freq='M'
            )
            
            win_rates = []
            for company in metrics.index:
                company_projects = df[df['winner'] == company]['transaction_date']
                monthly_wins = pd.Series(0, index=time_periods)
                for date in company_projects:
                    monthly_wins[date.to_period('M').to_timestamp()] += 1
                win_rates.append(monthly_wins.mean())
            
            metrics['avg_monthly_wins'] = win_rates
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error analyzing company performance: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def analyze_purchase_methods(df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze purchase method distribution and metrics"""
        try:
            method_analysis = {
                'by_count': df['purchase_method_name'].value_counts().to_dict(),
                'by_value': df.groupby('purchase_method_name')['sum_price_agree'].sum().to_dict(),
                'by_avg_value': df.groupby('purchase_method_name')['sum_price_agree'].mean().to_dict(),
                'by_unique_companies': df.groupby('purchase_method_name')['winner'].nunique().to_dict(),
                'efficiency': {
                    method: ((group['sum_price_agree'].sum() / group['price_build'].sum() - 1) * 100)
                    for method, group in df.groupby('purchase_method_name')
                }
            }
            return method_analysis
        except Exception as e:
            logger.error(f"Error analyzing purchase methods: {e}")
            return {}

    @staticmethod
    def analyze_project_types(df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze project type distribution and metrics"""
        try:
            type_analysis = {
                'by_count': df['project_type_name'].value_counts().to_dict(),
                'by_value': df.groupby('project_type_name')['sum_price_agree'].sum().to_dict(),
                'by_avg_value': df.groupby('project_type_name')['sum_price_agree'].mean().to_dict(),
                'by_unique_companies': df.groupby('project_type_name')['winner'].nunique().to_dict(),
                'by_dept_distribution': {
                    ptype: group['dept_name'].value_counts().to_dict()
                    for ptype, group in df.groupby('project_type_name')
                }
            }
            return type_analysis
        except Exception as e:
            logger.error(f"Error analyzing project types: {e}")
            return {}
    
    @staticmethod
    def analyze_price_trends(df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze price trends over time"""
        try:
            # Resample by month
            monthly_data = df.resample('M', on='transaction_date').agg({
                'sum_price_agree': ['count', 'sum', 'mean'],
                'price_build': 'sum'
            })
            
            # Calculate trends
            trends = {
                'project_count_trend': monthly_data[('sum_price_agree', 'count')].tolist(),
                'avg_value_trend': monthly_data[('sum_price_agree', 'mean')].tolist(),
                'total_value_trend': monthly_data[('sum_price_agree', 'sum')].tolist(),
                'dates': monthly_data.index.tolist(),
                'price_cut_trend': (
                    (monthly_data[('sum_price_agree', 'sum')] / 
                     monthly_data[('price_build', 'sum')] - 1) * 100
                ).tolist()
            }
            
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing price trends: {e}")
            return {}
    
    @staticmethod
    def analyze_department_distribution(df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze project distribution across departments"""
        try:
            dept_analysis = {
                'by_count': df['dept_name'].value_counts().to_dict(),
                'by_value': df.groupby('dept_name')['sum_price_agree'].sum().to_dict(),
                'by_avg_value': df.groupby('dept_name')['sum_price_agree'].mean().to_dict(),
                'by_unique_companies': df.groupby('dept_name')['winner'].nunique().to_dict()
            }
            return dept_analysis
        except Exception as e:
            logger.error(f"Error analyzing department distribution: {e}")
            return {}
    
    @staticmethod
    def analyze_competitive_landscape(df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze competitive landscape and market concentration"""
        try:
            # Calculate HHI (Herfindahl-Hirschman Index)
            market_shares = df.groupby('winner')['sum_price_agree'].sum() / df['sum_price_agree'].sum() * 100
            hhi = (market_shares ** 2).sum()
            
            # Calculate top player concentration
            sorted_shares = market_shares.sort_values(ascending=False)
            
            analysis = {
                'hhi': hhi,
                'market_concentration': 'High' if hhi > 2500 else 'Moderate' if hhi > 1500 else 'Low',
                'top_3_concentration': sorted_shares.head(3).sum(),
                'top_5_concentration': sorted_shares.head(5).sum(),
                'top_10_concentration': sorted_shares.head(10).sum(),
                'total_players': len(market_shares),
                'market_shares': market_shares.to_dict()
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing competitive landscape: {e}")
            return {}    
    @staticmethod
    def analyze_geographical_distribution(df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze geographical distribution of projects"""
        try:
            geo_analysis = {
                'by_province': df.groupby('province').agg({
                    'project_name': 'count',
                    'sum_price_agree': ['sum', 'mean'],
                    'winner': 'nunique'
                }).to_dict(),
                
                'by_district': df.groupby(['province', 'district']).agg({
                    'project_name': 'count',
                    'sum_price_agree': ['sum', 'mean'],
                    'winner': 'nunique'
                }).to_dict()
            }
            
            return geo_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing geographical distribution: {e}")
            return {}
    
    @staticmethod
    def generate_company_report(
        df: pd.DataFrame,
        company_name: str
    ) -> Dict[str, Any]:
        """Generate comprehensive report for a specific company"""
        try:
            company_df = df[df['winner'] == company_name]
            
            if company_df.empty:
                return {}
            
            report = {
                'summary': {
                    'total_projects': len(company_df),
                    'total_value': company_df['sum_price_agree'].sum(),
                    'avg_project_value': company_df['sum_price_agree'].mean(),
                    'active_years': company_df['transaction_date'].dt.year.nunique(),
                    'departments_worked_with': company_df['dept_name'].nunique()
                },
                
                'trends': {
                    'yearly_projects': company_df.groupby(
                        company_df['transaction_date'].dt.year
                    )['project_name'].count().to_dict(),
                    
                    'yearly_values': company_df.groupby(
                        company_df['transaction_date'].dt.year
                    )['sum_price_agree'].sum().to_dict()
                },
                
                'department_focus': {
                    dept: {
                        'projects': len(dept_df),
                        'total_value': dept_df['sum_price_agree'].sum(),
                        'avg_value': dept_df['sum_price_agree'].mean()
                    }
                    for dept, dept_df in company_df.groupby('dept_name')
                },
                
                'geographical_presence': {
                    province: len(province_df)
                    for province, province_df in company_df.groupby('province')
                },
                
                'performance_metrics': {
                    'avg_price_cut': (
                        (company_df['sum_price_agree'].sum() / company_df['price_build'].sum() - 1) * 100
                    ),
                    'success_rate': None,  # Would need additional data
                    'project_completion': None  # Would need additional data
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating company report: {e}")
            return {}