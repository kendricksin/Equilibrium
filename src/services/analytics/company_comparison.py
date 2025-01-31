# src/services/analytics/company_comparison_service.py

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
import logging
import plotly.graph_objects as go

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
    def calculate_group_competition_metrics(df: pd.DataFrame, companies: List[str]) -> Dict[str, Any]:
        """Calculate competition metrics for a group of companies"""
        try:
            # Initialize competition matrix
            competition_matrix = pd.DataFrame(0, index=companies, columns=companies)
            price_diff_matrix = pd.DataFrame(0.0, index=companies, columns=companies)
            dept_overlap_matrix = pd.DataFrame(0.0, index=companies, columns=companies)
            
            # Calculate company metrics
            company_metrics = {}
            for company in companies:
                company_data = df[df['winner'] == company]
                if len(company_data) > 0:
                    # Calculate average price cut
                    avg_price_cut = ((company_data['sum_price_agree'] / company_data['price_build'] - 1) * 100).mean()
                    departments = set(company_data['dept_name'].unique())
                    # Add sub-departments, filter out any None/NaN values
                    sub_departments = set(sub for sub in company_data['dept_sub_name'].unique() if pd.notna(sub))
                    total_value = company_data['sum_price_agree'].sum()
                    
                    company_metrics[company] = {
                        'avg_price_cut': avg_price_cut,
                        'departments': departments,
                        'sub_departments': sub_departments,
                        'project_count': len(company_data),
                        'total_value': total_value
                    }
            
            # Calculate pairwise metrics
            for i, company1 in enumerate(companies):
                for j, company2 in enumerate(companies):
                    if i != j and company1 in company_metrics and company2 in company_metrics:
                        # Calculate sub-department overlap
                        shared_sub_depts = company_metrics[company1]['sub_departments'].intersection(
                            company_metrics[company2]['sub_departments']
                        )
                        total_sub_depts = company_metrics[company1]['sub_departments'].union(
                            company_metrics[company2]['sub_departments']
                        )
                        overlap_pct = len(shared_sub_depts) / len(total_sub_depts) * 100 if total_sub_depts else 0
                        
                        # Count direct competitions in shared sub-departments
                        competitions = len(df[
                            (df['dept_sub_name'].isin(shared_sub_depts)) &
                            (df['winner'].isin([company1, company2]))
                        ]) if shared_sub_depts else 0
                        
                        # Calculate price difference
                        price_diff = company_metrics[company1]['avg_price_cut'] - company_metrics[company2]['avg_price_cut']
                        
                        # Update matrices
                        competition_matrix.loc[company1, company2] = competitions
                        price_diff_matrix.loc[company1, company2] = price_diff
                        dept_overlap_matrix.loc[company1, company2] = overlap_pct
            
            return {
                'competition_matrix': competition_matrix,
                'price_diff_matrix': price_diff_matrix,
                'dept_overlap_matrix': dept_overlap_matrix,
                'company_metrics': company_metrics
            }
            
        except Exception as e:
            logger.error(f"Error calculating group competition metrics: {e}")
            return {}

    @staticmethod
    def create_competition_heatmap(matrix: pd.DataFrame, title: str) -> go.Figure:
        """Create a heatmap visualization from a competition matrix"""
        try:
            fig = go.Figure(data=go.Heatmap(
                z=matrix.values,
                x=matrix.columns,
                y=matrix.index,
                colorscale='RdBu',
                zmid=0,
                text=np.round(matrix.values, 1),
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
            return go.Figure()

    @staticmethod
    def calculate_group_insights(metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key insights from group competition metrics"""
        try:
            competition_matrix = metrics['competition_matrix']
            price_diff_matrix = metrics['price_diff_matrix']
            dept_overlap_matrix = metrics['dept_overlap_matrix']
            company_metrics = metrics['company_metrics']
            
            # Find most competitive pairs
            competitions_flat = competition_matrix.unstack()
            top_competitions = competitions_flat[competitions_flat > 0].nlargest(5)
            
            # Find highest department overlaps
            overlaps_flat = dept_overlap_matrix.unstack()
            top_overlaps = overlaps_flat[overlaps_flat > 0].nlargest(5)
            
            # Calculate overall competition intensity
            competition_intensity = {
                company: row.sum()
                for company, row in competition_matrix.iterrows()
            }
            
            # Find companies with most aggressive pricing
            price_aggressiveness = {
                company: metrics['avg_price_cut']
                for company, metrics in company_metrics.items()
            }
            
            return {
                'top_competitions': top_competitions,
                'top_overlaps': top_overlaps,
                'competition_intensity': competition_intensity,
                'price_aggressiveness': price_aggressiveness
            }
            
        except Exception as e:
            logger.error(f"Error calculating group insights: {e}")
            return {}

    @staticmethod
    def create_network_graph(metrics: Dict[str, Any], threshold: int = 5) -> go.Figure:
        """Create a network visualization of company competitions"""
        try:
            competition_matrix = metrics['competition_matrix']
            company_metrics = metrics['company_metrics']
            
            # Create network edges (for companies with competitions above threshold)
            edges_x = []
            edges_y = []
            edge_colors = []
            
            # Create circular layout for nodes
            n_companies = len(competition_matrix)
            angles = np.linspace(0, 2*np.pi, n_companies, endpoint=False)
            radius = 1
            node_x = radius * np.cos(angles)
            node_y = radius * np.sin(angles)
            node_positions = dict(zip(competition_matrix.index, zip(node_x, node_y)))
            
            # Create edges
            for i, company1 in enumerate(competition_matrix.index):
                for j, company2 in enumerate(competition_matrix.columns):
                    competitions = competition_matrix.loc[company1, company2]
                    if competitions >= threshold:
                        # Add edge
                        x0, y0 = node_positions[company1]
                        x1, y1 = node_positions[company2]
                        edges_x.extend([x0, x1, None])
                        edges_y.extend([y0, y1, None])
                        edge_colors.append(competitions)
            
            # Create figure
            fig = go.Figure()
            
            # Add edges
            if edges_x:
                # Create colored edges using separate traces for each edge
                for i in range(0, len(edges_x), 3):  # Step by 3 because each edge has 3 points (including None)
                    if edge_colors:
                        intensity = edge_colors[i//3] / max(edge_colors)
                        color = f'rgba(250, 200, 180, {intensity})'  
                    else:
                        color = 'rgba(250, 200, 180, 0.5)'
                    
                    fig.add_trace(go.Scatter(
                        x=edges_x[i:i+2],  # Only take the two points, exclude None
                        y=edges_y[i:i+2],
                        line=dict(
                            width=np.sqrt(edge_colors[i//3])/2 if edge_colors else 1,  # Width based on competition intensity
                            color=color
                        ),
                        hoverinfo='none',
                        mode='lines',
                        showlegend=False
                    ))
            
            # Add nodes
            # Calculate node sizes based on total value
            node_sizes = []
            for company in competition_matrix.index:
                if company in company_metrics:
                    # Scale node sizes between 20 and 50 based on total value
                    value = company_metrics[company]['total_value']
                    size = 20 + (np.sqrt(value) / 1e4)  # Base size + scaled value
                    size = min(50, size)  # Cap maximum size
                    node_sizes.append(size)
                else:
                    node_sizes.append(20)  # Default size
            
            # Add nodes
            fig.add_trace(go.Scatter(
                x=node_x,
                y=node_y,
                mode='markers+text',
                marker=dict(
                    size=node_sizes,
                    color='rgb(31, 119, 180)',
                    line=dict(width=2, color='white'),
                    opacity=0.8
                ),
                text=list(competition_matrix.index),
                textposition='middle center',
                hovertemplate='<b>%{text}</b><br>Total Value: ฿%{customdata[0]:.1f}M<br>Projects: %{customdata[1]}<extra></extra>',
                customdata=[[company_metrics[company]['total_value'], company_metrics[company]['project_count']] 
                          if company in company_metrics else [0, 0] 
                          for company in competition_matrix.index]
            ))
            
            fig.update_layout(
                title=dict(
                    text='Competition Network<br><sup>Node size represents total value, edge thickness represents competition intensity</sup>',
                    x=0.5,
                    y=0.95,
                    xanchor='center',
                    yanchor='top'
                ),
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20, l=20, r=20, t=60),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                height=700,
                width=800,
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating network graph: {e}")
            return go.Figure()