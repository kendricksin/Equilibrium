import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime
from services.database.postgres import PostgresService

logger = logging.getLogger(__name__)

class ProjectAnalysisService:
    """Service for analyzing project trends, types, and distributions"""
    
    def __init__(self):
        self.db = PostgresService()

    def get_project_summary(self) -> Dict[str, Any]:
        """Get overall project statistics and summary"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    sql = f"""
                        WITH yearly_stats AS (
                            SELECT 
                                EXTRACT(YEAR FROM transaction_date) as year,
                                COUNT(*) as year_count,
                                SUM(sum_price_agree) as year_value
                            FROM {self.db.table_name}
                            GROUP BY EXTRACT(YEAR FROM transaction_date)
                        )
                        SELECT 
                            COUNT(*) as total_projects,
                            COUNT(DISTINCT winner) as unique_companies,
                            COUNT(DISTINCT dept_name) as unique_departments,
                            COUNT(DISTINCT dept_sub_name) as unique_subdepartments,
                            SUM(sum_price_agree) as total_value,
                            AVG(sum_price_agree) as avg_value,
                            MIN(transaction_date) as earliest_date,
                            MAX(transaction_date) as latest_date,
                            (SELECT COUNT(*) 
                             FROM {self.db.table_name} 
                             WHERE transaction_date >= NOW() - INTERVAL '1 year') as projects_last_year,
                            (SELECT SUM(sum_price_agree) 
                             FROM {self.db.table_name} 
                             WHERE transaction_date >= NOW() - INTERVAL '1 year') as value_last_year,
                            (SELECT AVG(year_count) FROM yearly_stats) as avg_yearly_projects,
                            (SELECT AVG(year_value) FROM yearly_stats) as avg_yearly_value
                        FROM {self.db.table_name}
                    """
                    cur.execute(sql)
                    result = cur.fetchone()
                    
                    return {
                        'total_projects': result[0],
                        'unique_companies': result[1],
                        'unique_departments': result[2],
                        'unique_subdepartments': result[3],
                        'total_value': result[4],
                        'avg_value': result[5],
                        'earliest_date': result[6],
                        'latest_date': result[7],
                        'projects_last_year': result[8],
                        'value_last_year': result[9],
                        'avg_yearly_projects': result[10],
                        'avg_yearly_value': result[11]
                    }
        except Exception as e:
            logger.error(f"Error getting project summary: {e}")
            raise

    def get_project_trends(self, period: str = 'Q') -> pd.DataFrame:
        """Get project trends analysis by time period"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    sql = f"""
                        WITH time_periods AS (
                            SELECT 
                                DATE_TRUNC(%s, transaction_date) as period,
                                COUNT(*) as project_count,
                                COUNT(DISTINCT winner) as company_count,
                                COUNT(DISTINCT dept_name) as department_count,
                                SUM(sum_price_agree) as total_value,
                                AVG(sum_price_agree) as avg_value,
                                MIN(sum_price_agree) as min_value,
                                MAX(sum_price_agree) as max_value,
                                COUNT(DISTINCT purchase_method_name) as procurement_methods
                            FROM {self.db.table_name}
                            GROUP BY DATE_TRUNC(%s, transaction_date)
                        )
                        SELECT 
                            period,
                            project_count,
                            company_count,
                            department_count,
                            total_value,
                            avg_value,
                            min_value,
                            max_value,
                            procurement_methods,
                            LAG(project_count) OVER (ORDER BY period) as prev_count,
                            LAG(total_value) OVER (ORDER BY period) as prev_value
                        FROM time_periods
                        ORDER BY period
                    """
                    cur.execute(sql, (period, period))
                    
                    columns = ['period', 'project_count', 'company_count', 'department_count',
                             'total_value', 'avg_value', 'min_value', 'max_value',
                             'procurement_methods', 'prev_count', 'prev_value']
                    df = pd.DataFrame(cur.fetchall(), columns=columns)
                    
                    # Calculate growth rates
                    df['count_growth'] = ((df['project_count'] / df['prev_count']) - 1) * 100
                    df['value_growth'] = ((df['total_value'] / df['prev_value']) - 1) * 100
                    
                    return df
        except Exception as e:
            logger.error(f"Error getting project trends: {e}")
            raise

    def get_procurement_analysis(self) -> pd.DataFrame:
        """Analyze project distribution by procurement method"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    sql = f"""
                        WITH method_stats AS (
                            SELECT 
                                purchase_method_name as method,
                                COUNT(*) as project_count,
                                COUNT(DISTINCT winner) as company_count,
                                COUNT(DISTINCT dept_name) as department_count,
                                SUM(sum_price_agree) as total_value,
                                AVG(sum_price_agree) as avg_value,
                                MIN(sum_price_agree) as min_value,
                                MAX(sum_price_agree) as max_value,
                                AVG((sum_price_agree / price_build - 1) * 100) as avg_price_cut
                            FROM {self.db.table_name}
                            WHERE purchase_method_name IS NOT NULL
                            GROUP BY purchase_method_name
                        )
                        SELECT 
                            method,
                            project_count,
                            company_count,
                            department_count,
                            total_value,
                            avg_value,
                            min_value,
                            max_value,
                            avg_price_cut,
                            project_count * 100.0 / SUM(project_count) OVER () as count_percentage,
                            total_value * 100.0 / SUM(total_value) OVER () as value_percentage
                        FROM method_stats
                        ORDER BY project_count DESC
                    """
                    cur.execute(sql)
                    
                    columns = ['method', 'project_count', 'company_count', 'department_count',
                             'total_value', 'avg_value', 'min_value', 'max_value', 
                             'avg_price_cut', 'count_percentage', 'value_percentage']
                    return pd.DataFrame(cur.fetchall(), columns=columns)
        except Exception as e:
            logger.error(f"Error getting procurement analysis: {e}")
            raise

    def get_value_distribution(self) -> pd.DataFrame:
        """Get project distribution by value ranges"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    sql = f"""
                        WITH value_ranges AS (
                            SELECT 
                                CASE
                                    WHEN sum_price_agree >= 300000000 THEN '>300M'
                                    WHEN sum_price_agree >= 100000000 THEN '100-300M'
                                    WHEN sum_price_agree >= 50000000 THEN '50-100M'
                                    WHEN sum_price_agree >= 10000000 THEN '10-50M'
                                    ELSE '<10M'
                                END as range,
                                COUNT(*) as project_count,
                                COUNT(DISTINCT winner) as company_count,
                                COUNT(DISTINCT dept_name) as department_count,
                                SUM(sum_price_agree) as total_value,
                                AVG(sum_price_agree) as avg_value,
                                COUNT(DISTINCT purchase_method_name) as method_count,
                                AVG((sum_price_agree / price_build - 1) * 100) as avg_price_cut
                            FROM {self.db.table_name}
                            GROUP BY 
                                CASE
                                    WHEN sum_price_agree >= 300000000 THEN '>300M'
                                    WHEN sum_price_agree >= 100000000 THEN '100-300M'
                                    WHEN sum_price_agree >= 50000000 THEN '50-100M'
                                    WHEN sum_price_agree >= 10000000 THEN '10-50M'
                                    ELSE '<10M'
                                END
                        )
                        SELECT 
                            range,
                            project_count,
                            company_count,
                            department_count,
                            total_value,
                            avg_value,
                            method_count,
                            avg_price_cut,
                            project_count * 100.0 / SUM(project_count) OVER () as count_percentage,
                            total_value * 100.0 / SUM(total_value) OVER () as value_percentage
                        FROM value_ranges
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
                    
                    columns = ['range', 'project_count', 'company_count', 'department_count',
                             'total_value', 'avg_value', 'method_count', 'avg_price_cut',
                             'count_percentage', 'value_percentage']
                    return pd.DataFrame(cur.fetchall(), columns=columns)
        except Exception as e:
            logger.error(f"Error getting value distribution: {e}")
            raise

    def get_project_concentration(self) -> pd.DataFrame:
        """Analyze project concentration across departments and companies"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    sql = f"""
                        WITH dept_concentration AS (
                            SELECT 
                                dept_name,
                                winner,
                                COUNT(*) as project_count,
                                SUM(sum_price_agree) as total_value
                            FROM {self.db.table_name}
                            GROUP BY dept_name, winner
                        ),
                        dept_totals AS (
                            SELECT 
                                dept_name,
                                SUM(project_count) as dept_projects,
                                SUM(total_value) as dept_value
                            FROM dept_concentration
                            GROUP BY dept_name
                        ),
                        top_companies AS (
                            SELECT 
                                dc.dept_name,
                                COUNT(DISTINCT dc.winner) as unique_companies,
                                COUNT(DISTINCT CASE 
                                    WHEN dc.project_count >= 5 THEN dc.winner 
                                    END) as active_companies,
                                SUM(CASE 
                                    WHEN row_number() OVER (
                                        PARTITION BY dc.dept_name 
                                        ORDER BY dc.project_count DESC
                                    ) <= 3 
                                    THEN dc.project_count 
                                    END) * 100.0 / dt.dept_projects as top3_project_share,
                                SUM(CASE 
                                    WHEN row_number() OVER (
                                        PARTITION BY dc.dept_name 
                                        ORDER BY dc.total_value DESC
                                    ) <= 3 
                                    THEN dc.total_value 
                                    END) * 100.0 / dt.dept_value as top3_value_share
                            FROM dept_concentration dc
                            JOIN dept_totals dt ON dc.dept_name = dt.dept_name
                            GROUP BY dc.dept_name, dt.dept_projects, dt.dept_value
                        )
                        SELECT 
                            dept_name,
                            unique_companies,
                            active_companies,
                            top3_project_share,
                            top3_value_share
                        FROM top_companies
                        WHERE unique_companies >= 5
                        ORDER BY top3_value_share DESC
                    """
                    cur.execute(sql)
                    
                    columns = ['department', 'unique_companies', 'active_companies',
                             'top3_project_share', 'top3_value_share']
                    return pd.DataFrame(cur.fetchall(), columns=columns)
        except Exception as e:
            logger.error(f"Error getting project concentration: {e}")
            raise

    def create_trend_visualization(self, trend_data: pd.DataFrame) -> go.Figure:
        """Create interactive visualization of project trends"""
        try:
            fig = go.Figure()

            # Add project count bars
            fig.add_trace(go.Bar(
                x=trend_data['period'],
                y=trend_data['project_count'],
                name='Projects',
                marker_color='rgb(31, 119, 180)',
                text=trend_data['project_count'],
                textposition='auto'
            ))

            # Add total value line
            fig.add_trace(go.Scatter(
                x=trend_data['period'],
                y=trend_data['total_value'] / 1e6,  # Convert to millions
                name='Total Value (M฿)',
                yaxis='y2',
                mode='lines+markers',
                line=dict(color='rgb(255, 127, 14)', width=2),
                marker=dict(size=8)
            ))

            # Update layout
            fig.update_layout(
                title='Project Trends Over Time',
                xaxis_title='Period',
                yaxis=dict(
                    title='Number of Projects',
                    titlefont=dict(color='rgb(31, 119, 180)'),
                    tickfont=dict(color='rgb(31, 119, 180)')
                ),
                yaxis2=dict(
                    title='Total Value (M฿)',
                    titlefont=dict(color='rgb(255, 127, 14)'),
                    tickfont=dict(color='rgb(255, 127, 14)'),
                    overlaying='y',
                    side='right'
                ),
                height=500,
                showlegend=True,
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="right",
                    x=0.99
                ),
                hovermode='x unified'
            )

            return fig
        except Exception as e:
            logger.error(f"Error creating trend visualization: {e}")
            raise