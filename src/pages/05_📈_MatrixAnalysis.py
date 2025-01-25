# src/pages/05_%F0%9F%93%88_MatrixAnalysis.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from special_functions.context_util import get_analysis_data, show_context_info

def create_heatmap(df: pd.DataFrame, metric: str):
    value_bands = [
        {'name': '0-10M', 'min': 0, 'max': 10},
        {'name': '10-50M', 'min': 10, 'max': 50},
        {'name': '50-100M', 'min': 50, 'max': 100},
        {'name': '100M+', 'min': 100, 'max': float('inf')}
    ]
    
    top_companies = (df.groupby('winner')['sum_price_agree']
                    .sum()
                    .sort_values(ascending=False)
                    .head(10)
                    .index)
    
    data = []
    annotations = []
    
    for i, band in enumerate(value_bands):
        row = []
        for j, company in enumerate(top_companies):
            company_projects = df[
                (df['winner'] == company) & 
                (df['sum_price_agree']/1e6 >= band['min']) & 
                (df['sum_price_agree']/1e6 < band['max'])
            ]
            
            if metric == 'Project Count':
                value = len(company_projects)
                cell_text = f"{value:,.0f}"
                hover_text = f"{value:,.0f} projects"
            elif metric == 'Total Value':
                value = company_projects['sum_price_agree'].sum()  # Remove /1e6 here since it's already divided when filtering
                cell_text = f"{value:,.0f}MB"
                hover_text = f"{value:,.0f}MB"
            else:  # Price Cut %
                value = ((company_projects['price_build'] - company_projects['sum_price_agree']) / 
                        company_projects['price_build']).mean() * 100 if not company_projects.empty else 0
                cell_text = f"{value:.1f}%"
                hover_text = f"{value:.1f}%"
                
            row.append(value)
            
            annotations.append(dict(
                x=j,
                y=i,
                text=cell_text,
                showarrow=False,
                font=dict(size=10)
            ))
        data.append(row)
    
    color_scales = {
        'Project Count': 'Blues',
        'Total Value': 'Greens',
        'Price Cut %': 'Reds'
    }

    hover_templates = {
        'Project Count': "Company: %{x}<br>Band: %{y}<br>Count: %{z:,.0f} projects<extra></extra>",
        'Total Value': "Company: %{x}<br>Band: %{y}<br>Value: %{z:,.0f}MB<extra></extra>",
        'Price Cut %': "Company: %{x}<br>Band: %{y}<br>Price Cut: %{z:.1f}%<extra></extra>"
    }

    fig = go.Figure(data=go.Heatmap(
        z=data,
        x=top_companies,
        y=[band['name'] for band in value_bands],
        colorscale=color_scales[metric],
        showscale=True,
        hoverongaps=False,
        hovertemplate=hover_templates[metric]
    ))
    
    fig.update_layout(
        title=f"Company Analysis - {metric}",
        xaxis_title="Companies",
        yaxis_title="Project Value Band",
        height=500,
        xaxis_tickangle=-45,
        annotations=annotations
    )
    
    return fig

def CompanyAnalysis():
    st.set_page_config(layout="wide")
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
        
    else:
        st.info("Please add collections to the context to perform analysis.")

if __name__ == "__main__":
    CompanyAnalysis()