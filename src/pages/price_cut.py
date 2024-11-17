import streamlit as st
import pandas as pd
import plotly.express as px

def price_cut_vis(df: pd.DataFrame):
    """
    Creates a visualization page with price cut analysis charts.
    
    Args:
        df: pandas DataFrame containing project data
    """
    st.title("Price Cut Analysis")
    
    try:
        # Calculate company metrics
        company_metrics = df.groupby('winner').agg({
            'winner': 'count',
            'sum_price_agree': 'mean',
            'price_build': lambda x: ((df.loc[x.index, 'sum_price_agree'].sum() / x.sum()) - 1) * 100
        }).rename(columns={
            'winner': 'project_count',
            'sum_price_agree': 'avg_value',
            'price_build': 'price_cut'
        })
        
        # Sort by project count and get top 10
        top_10_companies = company_metrics.nlargest(10, 'project_count')
        
        # Create horizontal bar chart for price cuts
        fig_bar = px.bar(
            top_10_companies,
            y=top_10_companies.index,
            x='price_cut',
            orientation='h',
            title='Top 10 Companies by Average Price Cut',
            text=top_10_companies['price_cut'].round(2).astype(str) + '%',
            labels={'price_cut': 'Average Price Cut (%)', 'winner': 'Company'},
            color='avg_value',  # Color bars by average project value
            color_continuous_scale='Viridis',
            hover_data={
                'avg_value': ':.2f',
                'project_count': True
            }
        )
        
        # Customize bar chart
        fig_bar.update_traces(
            textposition='outside',
            hovertemplate=(
                '<b>%{y}</b><br>' +
                'Price Cut: %{x:.2f}%<br>' +
                'Avg Value: %{customdata[0]:.2f} MB<br>' +
                'Projects: %{customdata[1]}<extra></extra>'
            )
        )
        
        fig_bar.update_layout(
            height=500,
            margin=dict(t=30, b=0, l=0, r=0),
            yaxis={'categoryorder': 'total ascending'}
        )
        
        # Display bar chart
        st.plotly_chart(fig_bar, use_container_width=True)
        
        # Calculate yearly price cuts by company
        yearly_metrics = df.groupby(['budget_year', 'winner']).agg({
            'sum_price_agree': 'sum',
            'price_build': 'sum'
        }).reset_index()
        
        # Calculate price cut percentage
        yearly_metrics['price_cut'] = ((yearly_metrics['sum_price_agree'] / yearly_metrics['price_build']) - 1) * 100
        
        # Get top companies by total project count for the line chart
        top_companies = df['winner'].value_counts().nlargest(8).index
        
        # Filter data for top companies
        yearly_metrics_filtered = yearly_metrics[yearly_metrics['winner'].isin(top_companies)]
        
        # Create line chart
        fig_line = px.line(
            yearly_metrics_filtered,
            x='budget_year',
            y='price_cut',
            color='winner',
            title='Price Cut Trends by Budget Year',
            labels={
                'budget_year': 'Budget Year',
                'price_cut': 'Price Cut (%)',
                'winner': 'Company'
            },
            markers=True
        )
        
        # Customize line chart
        fig_line.update_traces(
            hovertemplate='<b>%{customdata}</b><br>Year: %{x}<br>Price Cut: %{y:.2f}%<extra></extra>',
            customdata=yearly_metrics_filtered['winner']
        )
        
        fig_line.update_layout(
            height=500,
            margin=dict(t=30, b=0, l=0, r=0),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Add value labels on the lines
        for trace in fig_line.data:
            trace.text = [f"{y:.1f}%" for y in trace.y]
            trace.textposition = "top center"
        
        # Display line chart
        st.plotly_chart(fig_line, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error creating visualizations: {str(e)}")

# Add this to your main app.py:
"""
if page == "Price Cut Analysis":
    create_visualization_page(df)
"""