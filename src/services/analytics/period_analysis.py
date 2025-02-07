# src/services/analytics/period_analysis.py

import pandas as pd
from typing import Dict, Any, Tuple, List
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class PeriodAnalysisService:
    """Service for analyzing and comparing metrics across time periods"""
    
    METRICS = {
        'project_value': {
            'column': 'sum_price_agree',
            'agg': 'sum',
            'label': 'Project Value (M฿)',
            'formatter': lambda x: f"฿{x/1e6:.1f}M"
        },
        'project_count': {
            'column': 'project_name',
            'agg': 'count',
            'label': 'Project Count',
            'formatter': lambda x: f"{int(x):,}"
        }
    }

    @staticmethod
    def analyze_all_periods(df: pd.DataFrame, metric: str) -> Dict[str, Tuple[pd.DataFrame, Dict[str, Any]]]:
        """Analyze data for all period types"""
        periods = {
            'Weekly': 'W',
            'Monthly': 'M',
            'Quarterly': 'Q',
            'Yearly': 'Y'
        }
        
        results = {}
        df['date'] = pd.to_datetime(df['transaction_date'])
        metric_config = PeriodAnalysisService.METRICS[metric]
        
        for period_name, period_code in periods.items():
            df['period'] = df['date'].dt.to_period(period_code)
            period_data = df.groupby('period').agg({
                metric_config['column']: metric_config['agg']
            }).reset_index()
            
            period_data = period_data.sort_values('period', ascending=True).tail(5)
            period_data['previous_value'] = period_data[metric_config['column']].shift(1)
            period_data['change'] = (
                (period_data[metric_config['column']] / period_data['previous_value'] - 1) * 100
            )
            
            summary = {
                'current_period': str(period_data['period'].iloc[-1]),
                'current_value': period_data[metric_config['column']].iloc[-1],
                'previous_period': str(period_data['period'].iloc[-2]),
                'previous_value': period_data[metric_config['column']].iloc[-2],
                'change_percentage': period_data['change'].iloc[-1],
                'trend': 'up' if period_data['change'].iloc[-1] > 0 else 'down',
                'formatter': metric_config['formatter']
            }
            
            results[period_name] = (period_data, summary)
            
        return results

    @staticmethod
    def create_combined_chart(results: Dict[str, Tuple[pd.DataFrame, Dict[str, Any]]], metric: str) -> go.Figure:
        """Create subplot visualization for all periods"""
        metric_config = PeriodAnalysisService.METRICS[metric]
        
        # Create 2x2 subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=list(results.keys()),
            specs=[[{"secondary_y": True}] * 2] * 2
        )
        
        # Add traces for each period
        for idx, (period_name, (period_data, _)) in enumerate(results.items()):
            row = idx // 2 + 1
            col = idx % 2 + 1
            
            # Add bar for values
            fig.add_trace(
                go.Bar(
                    name=f"{period_name} Values",
                    x=[str(p) for p in period_data['period']],
                    y=period_data[metric_config['column']],
                    showlegend=False,
                    marker_color='rgb(55, 83, 109)'
                ),
                row=row, col=col,
                secondary_y=False
            )
            
            # Add line for change percentage
            fig.add_trace(
                go.Scatter(
                    name=f"{period_name} Change %",
                    x=[str(p) for p in period_data['period']],
                    y=period_data['change'],
                    mode='lines+markers',
                    showlegend=False,
                    line=dict(color='rgb(200, 0, 0)'),
                    marker=dict(size=6)
                ),
                row=row, col=col,
                secondary_y=True
            )
            
            # Update axes labels
            fig.update_yaxes(title_text=metric_config['label'], row=row, col=col, secondary_y=False)
            fig.update_yaxes(title_text="Change %", row=row, col=col, secondary_y=True)
        
        # Update layout
        fig.update_layout(
            height=800,
            title_text=f"{metric_config['label']} Trends by Period",
            showlegend=False,
            margin=dict(t=50, r=40, b=20, l=40)
        )
        
        return fig

    @staticmethod
    def format_summary(results: Dict[str, Tuple[pd.DataFrame, Dict[str, Any]]]) -> str:
        """Format summary for all periods"""
        summary_lines = []
        for period_name, (_, summary) in results.items():
            formatter = summary['formatter']
            summary_lines.append(f"""
            **{period_name}**
            Current ({summary['current_period']}): {formatter(summary['current_value'])}
            Previous ({summary['previous_period']}): {formatter(summary['previous_value'])}
            Change: {summary['change_percentage']:.1f}% ({summary['trend']})
            """)
        return "\n".join(summary_lines)