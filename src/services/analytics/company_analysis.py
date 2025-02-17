# src/services/analytics/company_analysis.py

import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional, Tuple
import logging
from services.database.postgres import PostgresService

logger = logging.getLogger(__name__)

class CompanyAnalysisService:
    """Service for analyzing company performance and competition"""
    
    def __init__(self):
        self.db = PostgresService()
    
    def get_top_companies(self, limit: int = 20) -> pd.DataFrame:
        """Get top companies by total project value"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    sql = f"""
                        SELECT 
                            winner as company,
                            COUNT(*) as project_count,
                            SUM(sum_price_agree) as total_value,
                            AVG(sum_price_agree) as avg_value,
                            COUNT(DISTINCT dept_name) as unique_departments,
                            ((SUM(sum_price_agree) / SUM(price_build) - 1) * 100) as avg_price_cut
                        FROM {self.db.table_name}
                        GROUP BY winner
                        ORDER BY total_value DESC
                        LIMIT %s
                    """
                    cur.execute(sql, (limit,))
                    results = cur.fetchall()
                    
                    columns = ['company', 'project_count', 'total_value', 'avg_value', 
                              'unique_departments', 'avg_price_cut']
                    return pd.DataFrame(results, columns=columns)
        except Exception as e:
            logger.error(f"Error getting top companies: {e}")
            raise

    def get_company_competition_data(self, companies: List[str]) -> Dict[str, Any]:
        """Analyze competition between companies"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get shared departments
                    sql = f"""
                        WITH company_pairs AS (
                            SELECT DISTINCT
                                a.winner as company1,
                                b.winner as company2,
                                a.dept_name,
                                COUNT(*) as competitions
                            FROM {self.db.table_name} a
                            JOIN {self.db.table_name} b 
                                ON a.dept_name = b.dept_name
                                AND a.winner < b.winner
                            WHERE a.winner = ANY(%s) AND b.winner = ANY(%s)
                            GROUP BY a.winner, b.winner, a.dept_name
                        )
                        SELECT 
                            company1,
                            company2,
                            COUNT(DISTINCT dept_name) as shared_departments,
                            SUM(competitions) as total_competitions
                        FROM company_pairs
                        GROUP BY company1, company2
                    """
                    cur.execute(sql, (companies, companies))
                    competition_results = cur.fetchall()
                    
                    # Get company performance in shared projects
                    sql = f"""
                        WITH shared_projects AS (
                            SELECT 
                                p1.winner,
                                p1.dept_name,
                                COUNT(*) as wins,
                                AVG((p1.sum_price_agree / p1.price_build - 1) * 100) as avg_price_cut
                            FROM {self.db.table_name} p1
                            WHERE p1.dept_name IN (
                                SELECT DISTINCT dept_name 
                                FROM {self.db.table_name}
                                WHERE winner = ANY(%s)
                            )
                            AND p1.winner = ANY(%s)
                            GROUP BY p1.winner, p1.dept_name
                        )
                        SELECT 
                            winner,
                            COUNT(DISTINCT dept_name) as active_departments,
                            SUM(wins) as total_wins,
                            AVG(avg_price_cut) as overall_price_cut
                        FROM shared_projects
                        GROUP BY winner
                    """
                    cur.execute(sql, (companies, companies))
                    performance_results = cur.fetchall()
                    
                    return {
                        'competition_data': competition_results,
                        'performance_data': performance_results
                    }
        except Exception as e:
            logger.error(f"Error getting competition data: {e}")
            raise

    def get_company_projects(self, company: str) -> pd.DataFrame:
        """Get detailed project data for a specific company"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    sql = f"""
                        SELECT 
                            project_id,
                            project_name,
                            transaction_date,
                            dept_name,
                            sum_price_agree as value,
                            price_build as budget,
                            ((sum_price_agree / price_build - 1) * 100) as price_cut,
                            purchase_method_name as procurement_method
                        FROM {self.db.table_name}
                        WHERE winner = %s
                        ORDER BY transaction_date DESC
                    """
                    cur.execute(sql, (company,))
                    columns = ['project_id', 'project_name', 'transaction_date', 'dept_name', 
                             'value', 'budget', 'price_cut', 'procurement_method']
                    return pd.DataFrame(cur.fetchall(), columns=columns)
        except Exception as e:
            logger.error(f"Error getting company projects: {e}")
            raise

    def get_value_distribution(self, companies: List[str]) -> Dict[str, Dict[str, Any]]:
        """Analyze project value distribution for companies"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    sql = f"""
                        WITH value_ranges AS (
                            SELECT 
                                winner,
                                CASE
                                    WHEN sum_price_agree >= 300000000 THEN '>300M'
                                    WHEN sum_price_agree >= 100000000 THEN '100-300M'
                                    WHEN sum_price_agree >= 50000000 THEN '50-100M'
                                    WHEN sum_price_agree >= 10000000 THEN '10-50M'
                                    ELSE '<10M'
                                END as value_range,
                                COUNT(*) as project_count,
                                SUM(sum_price_agree) as total_value,
                                AVG(sum_price_agree) as avg_value,
                                MIN(sum_price_agree) as min_value,
                                MAX(sum_price_agree) as max_value
                            FROM {self.db.table_name}
                            WHERE winner = ANY(%s)
                            GROUP BY winner, value_range
                        )
                        SELECT *,
                            project_count * 100.0 / SUM(project_count) OVER (PARTITION BY winner) as percentage
                        FROM value_ranges
                        ORDER BY winner, 
                            CASE value_range
                                WHEN '>300M' THEN 1
                                WHEN '100-300M' THEN 2
                                WHEN '50-100M' THEN 3
                                WHEN '10-50M' THEN 4
                                ELSE 5
                            END
                    """
                    cur.execute(sql, (companies,))
                    results = cur.fetchall()
                    
                    # Process results into a more usable format
                    distribution = {}
                    for row in results:
                        if row[0] not in distribution:
                            distribution[row[0]] = {}
                        distribution[row[0]][row[1]] = {
                            'count': row[2],
                            'total_value': row[3],
                            'avg_value': row[4],
                            'min_value': row[5],
                            'max_value': row[6],
                            'percentage': row[7]
                        }
                    
                    return distribution
        except Exception as e:
            logger.error(f"Error getting value distribution: {e}")
            raise

    def create_competition_heatmap(self, 
        competition_data: List[Tuple],
        title: str = "Competition Intensity"
    ) -> go.Figure:
        """Create a heatmap visualization of company competition"""
        try:
            # Extract unique companies
            companies = set()
            competitions = {}
            for comp1, comp2, _, comp_count in competition_data:
                companies.add(comp1)
                companies.add(comp2)
                competitions[(comp1, comp2)] = comp_count
                competitions[(comp2, comp1)] = comp_count
            
            companies = sorted(list(companies))
            
            # Create matrix
            matrix = []
            for comp1 in companies:
                row = []
                for comp2 in companies:
                    if comp1 == comp2:
                        row.append(0)
                    else:
                        row.append(competitions.get((comp1, comp2), 0))
                matrix.append(row)
            
            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=matrix,
                x=companies,
                y=companies,
                colorscale='RdBu',
                zmid=0,
                text=matrix,
                texttemplate='%{text}',
                textfont={"size": 10},
                hoverongaps=False
            ))
            
            fig.update_layout(
                title=title,
                height=600,
                width=800,
                xaxis={'side': 'bottom'},
                xaxis_tickangle=-45
            )
            
            return fig
        except Exception as e:
            logger.error(f"Error creating competition heatmap: {e}")
            raise

    def create_value_distribution_chart(self,
        distribution_data: Dict[str, Dict[str, Any]],
        company: str
    ) -> go.Figure:
        """Create a visualization of project value distribution"""
        try:
            company_dist = distribution_data.get(company, {})
            if not company_dist:
                raise ValueError(f"No distribution data for company {company}")
            
            # Order ranges
            ranges = ['>300M', '100-300M', '50-100M', '10-50M', '<10M']
            values = []
            counts = []
            
            for range_name in ranges:
                if range_name in company_dist:
                    values.append(company_dist[range_name]['percentage'])
                    counts.append(company_dist[range_name]['count'])
                else:
                    values.append(0)
                    counts.append(0)
            
            # Create bar chart
            fig = go.Figure(data=[
                go.Bar(
                    x=ranges,
                    y=values,
                    text=[f"{v:.1f}%<br>({c} projects)" for v, c in zip(values, counts)],
                    textposition='auto',
                )
            ])
            
            fig.update_layout(
                title=f"Project Value Distribution - {company}",
                xaxis_title="Value Range",
                yaxis_title="Percentage of Projects",
                height=400,
                showlegend=False
            )
            
            return fig
        except Exception as e:
            logger.error(f"Error creating value distribution chart: {e}")
            raise