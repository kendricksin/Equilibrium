# src/services/analytics/price_analysis.py

import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime
from services.database.postgres import PostgresService

logger = logging.getLogger(__name__)

class PriceAnalysisService:
    """Service for analyzing price trends and competition"""
    
    def __init__(self):
        self.db = PostgresService()

    def get_overall_price_metrics(self) -> Dict[str, float]:
        """Get overall price metrics across all projects"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    sql = f"""
                        SELECT 
                            COUNT(*) as total_projects,
                            SUM(sum_price_agree) as total_value,
                            SUM(price_build) as total_budget,
                            AVG((sum_price_agree / price_build - 1) * 100) as avg_price_cut,
                            PERCENTILE_CONT(0.5) WITHIN GROUP (
                                ORDER BY ((sum_price_agree / price_build - 1) * 100)
                            ) as median_price_cut,
                            STDDEV((sum_price_agree / price_build - 1) * 100) as price_cut_stddev
                        FROM {self.db.table_name}
                        WHERE price_build > 0
                    """
                    cur.execute(sql)
                    result = cur.fetchone()
                    
                    return {
                        'total_projects': result[0],
                        'total_value': result[1],
                        'total_budget': result[2],
                        'avg_price_cut': result[3],
                        'median_price_cut': result[4],
                        'price_cut_stddev': result[5],
                        'overall_price_cut': ((result[1] / result[2] - 1) * 100)
                    }
        except Exception as e:
            logger.error(f"Error getting overall price metrics: {e}")
            raise

    def get_price_trends(self, period: str = 'Q') -> pd.DataFrame:
        """Get price trends analysis by time period"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    sql = f"""
                        WITH time_periods AS (
                            SELECT 
                                DATE_TRUNC(%s, transaction_date) as period,
                                COUNT(*) as project_count,
                                SUM(sum_price_agree) as value_sum,
                                SUM(price_build) as budget_sum,
                                AVG(sum_price_agree) as avg_value,
                                AVG(price_build) as avg_budget,
                                AVG((sum_price_agree / price_build - 1) * 100) as avg_cut,
                                PERCENTILE_CONT(0.5) WITHIN GROUP (
                                    ORDER BY ((sum_price_agree / price_build - 1) * 100)
                                ) as median_cut,
                                MIN((sum_price_agree / price_build - 1) * 100) as min_cut,
                                MAX((sum_price_agree / price_build - 1) * 100) as max_cut
                            FROM {self.db.table_name}
                            WHERE price_build > 0
                            GROUP BY DATE_TRUNC(%s, transaction_date)
                        )
                        SELECT 
                            period,
                            project_count,
                            value_sum,
                            budget_sum,
                            avg_value,
                            avg_budget,
                            avg_cut,
                            median_cut,
                            min_cut,
                            max_cut,
                            ((value_sum / budget_sum - 1) * 100) as period_cut,
                            LAG(value_sum) OVER (ORDER BY period) as prev_value,
                            LAG(project_count) OVER (ORDER BY period) as prev_count
                        FROM time_periods
                        ORDER BY period
                    """
                    cur.execute(sql, (period, period))
                    
                    columns = ['period', 'project_count', 'value_sum', 'budget_sum', 
                             'avg_value', 'avg_budget', 'avg_cut', 'median_cut',
                             'min_cut', 'max_cut', 'period_cut', 'prev_value', 'prev_count']
                    df = pd.DataFrame(cur.fetchall(), columns=columns)
                    
                    # Calculate growth rates
                    df['value_growth'] = ((df['value_sum'] / df['prev_value']) - 1) * 100
                    df['count_growth'] = ((df['project_count'] / df['prev_count']) - 1) * 100
                    
                    return df
        except Exception as e:
            logger.error(f"Error getting price trends: {e}")
            raise

    def get_price_competition_by_department(self, min_projects: int = 10) -> pd.DataFrame:
        """Analyze price competition within departments"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    sql = f"""
                        WITH dept_stats AS (
                            SELECT 
                                dept_name,
                                COUNT(*) as projects,
                                COUNT(DISTINCT winner) as companies,
                                SUM(sum_price_agree) as total_value,
                                SUM(price_build) as total_budget,
                                AVG((sum_price_agree / price_build - 1) * 100) as avg_cut,
                                STDDEV((sum_price_agree / price_build - 1) * 100) as cut_stddev,
                                AVG(
                                    (SELECT COUNT(*)
                                    FROM {self.db.table_name} b
                                    WHERE b.dept_name = a.dept_name
                                    AND b.transaction_date >= a.transaction_date - INTERVAL '1 year'
                                    AND b.transaction_date <= a.transaction_date)
                                ) as avg_annual_projects
                            FROM {self.db.table_name} a
                            WHERE price_build > 0
                            GROUP BY dept_name
                            HAVING COUNT(*) >= %s
                        )
                        SELECT 
                            dept_name,
                            projects,
                            companies,
                            total_value,
                            total_budget,
                            ((total_value / total_budget - 1) * 100) as total_cut,
                            avg_cut,
                            cut_stddev,
                            avg_annual_projects,
                            (companies::float / projects) as company_project_ratio
                        FROM dept_stats
                        ORDER BY projects DESC
                    """
                    cur.execute(sql, (min_projects,))
                    
                    columns = ['department', 'projects', 'companies', 'total_value', 
                             'total_budget', 'total_cut', 'avg_cut', 'cut_stddev',
                             'avg_annual_projects', 'company_project_ratio']
                    return pd.DataFrame(cur.fetchall(), columns=columns)
        except Exception as e:
            logger.error(f"Error getting department price competition: {e}")
            raise

    def get_price_distribution(self) -> pd.DataFrame:
        """Analyze price distribution across value ranges"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    sql = f"""
                        WITH value_ranges AS (
                            SELECT 
                                CASE
                                    WHEN project_money >= 300000000 THEN '>300M'
                                    WHEN project_money >= 100000000 THEN '100-300M'
                                    WHEN project_money >= 50000000 THEN '50-100M'
                                    WHEN project_money >= 10000000 THEN '10-50M'
                                    ELSE '<10M'
                                END as range,
                                project_money,
                                price_build as budget,
                                winner,
                                dept_name
                            FROM {self.db.table_name}
                            WHERE price_build > 0
                        )
                        SELECT 
                            range,
                            COUNT(*) as projects,
                            COUNT(DISTINCT winner) as companies,
                            COUNT(DISTINCT dept_name) as departments,
                            SUM(project_money) as total_value,
                            SUM(budget) as total_budget,
                            AVG((project_money / budget - 1) * 100) as avg_cut,
                            STDDEV((project_money / budget - 1) * 100) as cut_stddev
                        FROM value_ranges
                        GROUP BY range
                        ORDER BY 
                            CASE range
                                WHEN '>300M' THEN 1
                                WHEN '100-300M' THEN 2
                                WHEN '50-100M' THEN 3
                                WHEN '10-50M' THEN 4
                                ELSE 5
                            END
                    """
                    cur.execute(sql)
                    columns = ['range', 'projects', 'companies', 'departments', 'total_value',
                            'total_budget', 'avg_cut', 'cut_stddev']
                    return pd.DataFrame(cur.fetchall(), columns=columns)
            
        except Exception as e:
            logger.error(f"Error getting price distribution: {e}")
            raise

    def create_trend_visualization(self, trend_data: pd.DataFrame) -> go.Figure:
        """Create interactive visualization of price trends"""
        try:
            fig = go.Figure()
            
            # Add price cut trend
            fig.add_trace(go.Scatter(
                x=trend_data['period'],
                y=trend_data['period_cut'],
                name='Period Price Cut',
                mode='lines+markers',
                line=dict(color='rgb(31, 119, 180)', width=2),
                hovertemplate="Period: %{x}<br>Price Cut: %{y:.1f}%<extra></extra>"
            ))
            
            # Add running average
            fig.add_trace(go.Scatter(
                x=trend_data['period'],
                y=trend_data['avg_cut'].rolling(4).mean(),
                name='4-Period Average',
                mode='lines',
                line=dict(color='rgb(255, 127, 14)', width=2, dash='dash'),
                hovertemplate="Period: %{x}<br>Avg Cut: %{y:.1f}%<extra></extra>"
            ))
            
            # Add project count
            fig.add_trace(go.Bar(
                x=trend_data['period'],
                y=trend_data['project_count'],
                name='Projects',
                yaxis='y2',
                marker_color='rgba(150, 150, 150, 0.3)',
                hovertemplate="Period: %{x}<br>Projects: %{y}<extra></extra>"
            ))
            
            # Update layout
            fig.update_layout(
                title='Price Cut Trends',
                xaxis_title='Period',
                yaxis=dict(
                    title='Price Cut (%)',
                    titlefont=dict(color='rgb(31, 119, 180)'),
                    tickfont=dict(color='rgb(31, 119, 180)'),
                    tickformat='.1f'
                ),
                yaxis2=dict(
                    title='Number of Projects',
                    titlefont=dict(color='rgb(150, 150, 150)'),
                    tickfont=dict(color='rgb(150, 150, 150)'),
                    overlaying='y',
                    side='right'
                ),
                hovermode='x unified',
                height=500,
                showlegend=True,
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="right",
                    x=0.99
                )
            )
            
            return fig
        except Exception as e:
            logger.error(f"Error creating trend visualization: {e}")
            raise