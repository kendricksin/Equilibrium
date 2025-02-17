# src/services/analytics/department_analysis.py

import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional, Tuple
import logging
from services.database.postgres import PostgresService

logger = logging.getLogger(__name__)

class DepartmentAnalysisService:
    """Service for analyzing department and sub-department data"""
    
    def __init__(self):
        self.db = PostgresService()

    def get_department_overview(self) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Get department overview with metadata
        
        Returns:
            Tuple containing (department_data, metadata)
        """
        try:
            # Get all departments without limit
            dept_data = self.db.get_department_summary(limit=None)
            
            if not dept_data:
                return [], {}
                
            # Calculate metadata
            total_projects = sum(dept['count'] for dept in dept_data)
            total_value = sum(dept['total_value'] for dept in dept_data)
            unique_departments = len(dept_data)
            unique_companies = sum(dept['unique_companies'] for dept in dept_data)
            
            metadata = {
                "total_projects": total_projects,
                "total_value": total_value,
                "unique_departments": unique_departments,
                "unique_companies": unique_companies,
                "avg_project_value": total_value / total_projects if total_projects > 0 else 0
            }
            
            return dept_data, metadata
            
        except Exception as e:
            logger.error(f"Error getting department overview: {e}")
            raise
    
    def get_department_projects(
        self, 
        departments: Optional[List[str]] = None, 
        subdepartments: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Get project data for specific departments and sub-departments
        
        Args:
            departments: List of department names
            subdepartments: List of sub-department names
            
        Returns:
            DataFrame of projects
        """
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    # Base query
                    query = "SELECT * FROM public_data.thai_govt_project WHERE 1=1"
                    params = []
                    
                    # Add department filter
                    if departments:
                        query += " AND dept_name = ANY(%s)"
                        params.append(departments)
                    
                    # Add sub-department filter
                    if subdepartments:
                        query += " AND dept_sub_name = ANY(%s)"
                        params.append(subdepartments)
                    
                    # Execute query
                    cur.execute(query, tuple(params))
                    columns = [desc[0] for desc in cur.description]
                    return pd.DataFrame(cur.fetchall(), columns=columns)
            
        except Exception as e:
            logger.error(f"Error getting department projects: {e}")
            return pd.DataFrame()

    def get_department_distribution(
        self,
        view_by: str = "count",
        limit: int = 20
    ) -> pd.DataFrame:
        """
        Get department distribution data
        
        Args:
            view_by: Sort by "count" or "value"
            limit: Number of departments to return
            
        Returns:
            DataFrame with department distribution data
        """
        try:
            dept_data = self.db.get_department_summary(
                view_by=view_by,
                limit=limit
            )
            
            if not dept_data:
                return pd.DataFrame()
                
            return pd.DataFrame(dept_data)
            
        except Exception as e:
            logger.error(f"Error getting department distribution: {e}")
            raise

    def create_distribution_visualization(
        self,
        df: pd.DataFrame,
        view_type: str = "count",
        height: int = 600
    ) -> go.Figure:
        """
        Create department distribution visualization
        
        Args:
            df: Department data DataFrame
            view_type: "count" or "value"
            height: Chart height
            
        Returns:
            Plotly figure object
        """
        try:
            # Set up parameters based on view type
            if view_type == "count":
                value_col = 'count'
                color_scale = 'Blues'
                hover_template = (
                    "<b>%{customdata[0]}</b><br>" +
                    "Projects: %{value:,}<br>" +
                    "Value: ฿%{customdata[1]:.1f}M<br>" +
                    "Companies: %{customdata[2]:,}<br>" +
                    "<extra></extra>"
                )
            else:
                value_col = 'total_value_millions'
                color_scale = 'Reds'
                hover_template = (
                    "<b>%{customdata[0]}</b><br>" +
                    "Value: ฿%{value:.1f}M<br>" +
                    "Projects: %{customdata[1]:,}<br>" +
                    "Companies: %{customdata[2]:,}<br>" +
                    "<extra></extra>"
                )

            # Create figure
            fig = go.Figure(go.Treemap(
                ids=df.index,
                labels=df['department'],
                parents=[''] * len(df),
                values=df[value_col],
                customdata=df[['department', 'total_value_millions', 'unique_companies']].values,
                hovertemplate=hover_template,
                marker=dict(
                    colorscale=color_scale,
                    showscale=True
                ),
                textinfo='label+value',
                texttemplate='%{label}<br>%{value:,.0f}',
                tiling=dict(
                    packing='squarify',
                    pad=3
                )
            ))

            # Update layout
            fig.update_layout(
                height=height,
                margin=dict(t=30, l=10, r=10, b=10),
                uniformtext=dict(minsize=12, mode='hide')
            )

            return fig
            
        except Exception as e:
            logger.error(f"Error creating distribution visualization: {e}")
            raise
    
    def get_project_timeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate project timeline data from DataFrame
        
        Args:
            df: DataFrame with project data
        
        Returns:
            DataFrame with timeline metrics
        """
        try:
            # Group by transaction date (month or quarter)
            df['transaction_date'] = pd.to_datetime(df['transaction_date'])
            timeline = df.groupby(pd.Grouper(key='transaction_date', freq='M')).agg({
                'project_id': 'count',
                'sum_price_agree': 'sum'
            }).reset_index()
            
            timeline.columns = ['period', 'project_count', 'total_value']
            
            return timeline
            
        except Exception as e:
            logger.error(f"Error getting project timeline: {e}")
            return pd.DataFrame()

    def get_subdepartment_analysis(
        self,
        department: str,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Get sub-department analysis for a specific department
        
        Args:
            department: Department name
            limit: Optional limit on number of sub-departments
            
        Returns:
            DataFrame with sub-department analysis
        """
        try:
            subdept_data = self.db.get_subdepartment_data(
                department=department,
                limit=limit
            )
            
            if not subdept_data:
                return pd.DataFrame()
                
            return pd.DataFrame(subdept_data)
            
        except Exception as e:
            logger.error(f"Error getting sub-department analysis: {e}")
            raise