from typing import List, Dict, Any
import pandas as pd

class CompanyAnalytics:
    """Pure analytics logic for company comparisons"""
    
    @staticmethod
    def calculate_competition_metrics(
        df: pd.DataFrame,
        companies: List[str]
    ) -> Dict[str, Any]:
        """Calculate competition metrics between companies"""
        metrics = {
            'competition_matrix': pd.DataFrame(),
            'overlap_score': 0.0,
            'price_differences': pd.DataFrame(),
            'market_share': {}
        }
        
        # Your existing competition calculation logic here
        # Moved from CompanyComparisonService
        
        return metrics
    
    @staticmethod
    def analyze_company_performance(
        df: pd.DataFrame,
        company: str
    ) -> Dict[str, Any]:
        """Analyze single company performance metrics"""
        return {
            'project_count': len(df),
            'total_value': df['sum_price_agree'].sum(),
            'avg_project_value': df['sum_price_agree'].mean(),
            'departments': df['dept_name'].unique().tolist(),
            'win_rate': len(df[df['winner'] == company]) / len(df)
        }