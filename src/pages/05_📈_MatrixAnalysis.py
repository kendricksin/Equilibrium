# src/pages/05_📈_MatrixAnalysis.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from special_functions.context_util import get_analysis_data, show_context_info
from services.analytics.price_cut_trend import PriceCutAnalysis
from components.layout.ContextSelector import ContextSelector

def create_heatmap(df: pd.DataFrame, metric: str):
    value_bands = [
        {'name': '0-10M', 'min': 0, 'max': 10},
        {'name': '10-50M', 'min': 10, 'max': 50},
        {'name': '50-100M', 'min': 50, 'max': 100},
        {'name': '100-300M', 'min': 100, 'max': 300},
        {'name': '300M+', 'min': 300, 'max': float('inf')}
    ]
    
    top_companies = (df.groupby('winner')['sum_price_agree']
                    .sum()
                    .sort_values(ascending=False)
                    .head(10)
                    .index)
    
    data = []
    annotations = []
    customdata = []  # For storing whether value is zero
    
    for i, band in enumerate(value_bands):
        row = []
        row_customdata = []  # For storing zero flags in this row
        for j, company in enumerate(top_companies):
            company_projects = df[
                (df['winner'] == company) & 
                (df['sum_price_agree'] >= band['min']) &
                (df['sum_price_agree'] < band['max'])
            ]
            
            if metric == 'Project Count':
                value = len(company_projects)
                cell_text = "N/A" if value == 0 else f"{value:,.0f}"
            elif metric == 'Total Value':
                value = company_projects['sum_price_agree'].sum()
                cell_text = "N/A" if value == 0 else f"{value:,.0f}M"
            else:  # Price Cut %
                if company_projects.empty:
                    value = 0
                    cell_text = "N/A"
                else:
                    value = ((company_projects['price_build'] - company_projects['sum_price_agree']) / 
                            company_projects['price_build']).mean() * 100
                    cell_text = f"{value:.1f}%"
            
            is_zero = value == 0
            row.append(value)
            row_customdata.append(is_zero)
            
            # Configure text style based on whether value is zero
            font_color = 'rgba(0,0,0,0.5)' if is_zero else 'black'
            font_size = 12  # Increased font size
            font_weight = 'normal' if is_zero else 'bold'
            
            annotations.append(dict(
                x=j,
                y=i,
                text=cell_text,
                showarrow=False,
                font=dict(
                    size=font_size,
                    color=font_color,
                    weight=font_weight
                )
            ))
        
        data.append(row)
        customdata.append(row_customdata)
    
    # Calculate average values for each cell
    averages = []
    for i, band in enumerate(value_bands):
        row_avgs = []
        for j, company in enumerate(top_companies):
            company_projects = df[
                (df['winner'] == company) & 
                (df['sum_price_agree'] >= band['min']) &
                (df['sum_price_agree'] < band['max'])
            ]
            if len(company_projects) > 0:
                avg_value = company_projects['sum_price_agree'].mean()
                row_avgs.append(avg_value)
            else:
                row_avgs.append(None)
        averages.append(row_avgs)

    hover_templates = {
        'Project Count': "Company: %{x}<br>Band: %{y}<br>Count: %{z:,.0f} projects<br>Avg Value: %{customdata:,.1f}M<extra></extra>",
        'Total Value': "Company: %{x}<br>Band: %{y}<br>Total Value: %{z:,.0f}M<br>Avg Value: %{customdata:,.1f}M<extra></extra>",
        'Price Cut %': "Company: %{x}<br>Band: %{y}<br>Price Cut: %{z:.1f}%<br>Avg Value: %{customdata:,.1f}M<extra></extra>"
    }

    # Create a custom colorscale with white for zero values
    colorscale = [
        [0, 'rgba(255,255,255,0)'],  # Zero values - transparent white
        [0.000001, 'rgb(220,240,220)'],  # Very low values start with very light color
        [1, 'darkgreen']  # Maximum values
    ]
    
    # Replace zero values with None to make them transparent
    data_with_nones = [[val if not is_zero else None for val, is_zero in zip(row, row_customdata)] 
                      for row, row_customdata in zip(data, customdata)]
    
    fig = go.Figure(data=go.Heatmap(
        z=data_with_nones,
        x=top_companies,
        y=[band['name'] for band in value_bands],
        colorscale=colorscale,
        showscale=True,
        hoverongaps=False,
        hovertemplate=hover_templates[metric],
        customdata=averages  # Use averages for hover data
    ))
    
    fig.update_layout(
        title=dict(
            text=f"Company Analysis - {metric}",
            font=dict(size=24)  # Larger title
        ),
        xaxis_title="Companies",
        yaxis_title="Project Value Band",
        height=600,  # Increased height
        xaxis_tickangle=-45,
        xaxis_tickfont=dict(size=12),  # Larger x-axis labels
        yaxis_tickfont=dict(size=12),  # Larger y-axis labels
        annotations=annotations,
        plot_bgcolor='white'  # White background
    )
    
    return fig

def CompanyAnalysis():
    st.set_page_config(layout="wide")
    ContextSelector()

    st.title("📊 Company Project Analysis")
    
    df, context_source = get_analysis_data()
    show_context_info()
    
    if df is not None and not df.empty:
        st.markdown("### Company Performance Analysis")

        fig = create_heatmap(df, 'Project Count')
        st.plotly_chart(fig, use_container_width=True)

        fig = create_heatmap(df, 'Price Cut %')
        st.plotly_chart(fig, use_container_width=True)

        fig = create_heatmap(df, 'Total Value')
        st.plotly_chart(fig, use_container_width=True)

        PriceCutAnalysis(df)

        st.markdown("---")
    else:
        st.info("Please add collections to the context to perform analysis.")

if __name__ == "__main__":
    CompanyAnalysis()