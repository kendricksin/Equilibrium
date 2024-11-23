import pandas as pd
import plotly.express as px
from typing import Dict, Any
import streamlit as st

def calculate_project_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate project metrics from the filtered DataFrame.
    
    Args:
        df: pandas DataFrame containing project data
        
    Returns:
        Dictionary containing calculated metrics
    """
    try:
        # Basic metrics
        total_projects = len(df)
        unique_winners = df['winner'].nunique() if 'winner' in df.columns else 0
        
        # Financial metrics
        total_value = df['sum_price_agree'].sum() if 'sum_price_agree' in df.columns else 0
        avg_value = df['sum_price_agree'].mean() if 'sum_price_agree' in df.columns else 0
        
        # Calculate price cut percentage
        total_price_build = df['price_build'].sum() if 'price_build' in df.columns else 0
        if total_price_build > 0:
            price_cut = ((total_value / total_price_build) - 1) * 100
        else:
            price_cut = 0
            
        # Purchase method distribution
        purchase_method_dist = None
        if 'purchase_method_name' in df.columns:
            purchase_method_dist = df['purchase_method_name'].value_counts()

        # Calculate company-level metrics
        company_metrics = None
        if all(col in df.columns for col in ['winner', 'sum_price_agree', 'price_build']):
            company_metrics = df.groupby('winner').agg({
                'winner': 'count',  # Count of projects
                'sum_price_agree': 'mean',  # Average project value
                'price_build': lambda x: ((df.loc[x.index, 'sum_price_agree'].sum() / x.sum()) - 1) * 100  # Average price cut
            }).rename(columns={
                'winner': 'count',
                'sum_price_agree': 'avg_project_value',
                'price_build': 'avg_price_cut'
            })
            
            # Sort by count (number of projects) in descending order
            company_metrics = company_metrics.sort_values('count', ascending=False)
        
        metrics = {
            'total_projects': total_projects,
            'unique_winners': unique_winners,
            'total_value': total_value,
            'avg_value': avg_value,
            'price_cut': price_cut,
            'purchase_method_dist': purchase_method_dist,
            'company_metrics': company_metrics
        }
        
        return metrics
        
    except Exception as e:
        st.error(f"Error calculating metrics: {str(e)}")
        return None

def display_metrics_dashboard(df: pd.DataFrame):
    """
    Display metrics dashboard with calculated values and visualizations.
    """
    try:
        # Calculate metrics
        metrics = calculate_project_metrics(df)
        
        if metrics is None:
            st.error("Unable to calculate metrics")
            return
            
        # Create layout with columns
        col1, col2, col3 = st.columns(3)
        
        # Display metrics in columns
        with col1:
            st.metric(
                label="Total Projects",
                value=f"{metrics['total_projects']:,}"
            )
            st.metric(
                label="Unique Winners",
                value=f"{metrics['unique_winners']:,}"
            )
            
        with col2:
            st.metric(
                label="Total Value (M THB)",
                value=f"{metrics['total_value']/1e6:,.2f} MB"
            )
            st.metric(
                label="Average Value (M THB)",
                value=f"{metrics['avg_value']/1e6:,.2f} MB"
            )
            
        with col3:
            st.metric(
                label="Average Price Cut",
                value=f"{metrics['price_cut']:.2f}%"
            )
        
        # # Create purchase method distribution pie chart
        # if metrics['purchase_method_dist'] is not None:
        #     st.subheader("Purchase Method Distribution")
            
        #     # Convert to DataFrame for Plotly
        #     dist_df = pd.DataFrame({
        #         'Method': metrics['purchase_method_dist'].index,
        #         'Count': metrics['purchase_method_dist'].values
        #     })
            
            # # Create pie chart
            # fig = px.pie(
            #     dist_df,
            #     values='Count',
            #     names='Method',
            #     title='Distribution of Purchase Methods',
            #     hole=0.3  # Makes it a donut chart
            # )
            
            # # Update layout
            # fig.update_layout(
            #     showlegend=True,
            #     legend=dict(
            #         orientation="h",
            #         yanchor="bottom",
            #         y=1.02,
            #         xanchor="right",
            #         x=1
            #     )
            # )
            
            # Display chart
            # st.plotly_chart(fig, use_container_width=True)
            
        # Display company metrics table
        if metrics['company_metrics'] is not None:
                
            # Format the company metrics for display
            display_df = metrics['company_metrics'].copy()
            
            # Format the columns
            display_df['avg_project_value'] = display_df['avg_project_value'].apply(
                lambda x: f"{x/1e6:.2f} MB"
            )
            display_df['avg_price_cut'] = display_df['avg_price_cut'].apply(
                lambda x: f"{x:.2f}%"
            )
                
            # Rename columns for display
            display_df.columns = [
                'Number of Projects',
                'Avg Project Value',
                'Avg Price Cut'
            ]
                
            # Display the formatted DataFrame
            st.dataframe(display_df)
            
    except Exception as e:
        st.error(f"Error displaying metrics: {str(e)}")