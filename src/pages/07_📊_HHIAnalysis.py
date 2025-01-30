# src/pages/07_📊_HHIAnalysis.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from components.layout.MetricsSummary import create_distribution_bar
from state.session import SessionState
from special_functions.context_util import get_analysis_data, show_context_info

st.set_page_config(layout="wide")

def calculate_hhi(market_shares):
    """
    Calculate Herfindahl-Hirschman Index
    
    Args:
        market_shares: Market shares as percentages (0-100)
        
    Returns:
        float: HHI value (0-10000)
    """
    # Convert percentages to proportions (0-1) before squaring
    return round(sum((share/100) ** 2 * 10000 for share in market_shares), 2)

def interpret_hhi(hhi):
    """Interpret HHI value"""
    if hhi < 1500:
        return "Competitive Market", "Low concentration"
    elif hhi < 2500:
        return "Moderately Concentrated", "Medium concentration"
    else:
        return "Highly Concentrated", "High concentration"

def get_company_colors(n):
    """Generate a list of distinct colors for companies"""
    colors = [
        'rgb(31, 119, 180)',   # blue
        'rgb(255, 127, 14)',   # orange
        'rgb(44, 160, 44)',    # green
        'rgb(214, 39, 40)',    # red
        'rgb(148, 103, 189)',  # purple
        'rgb(140, 86, 75)',    # brown
        'rgb(227, 119, 194)',  # pink
        'rgb(127, 127, 127)',  # gray
        'rgb(188, 189, 34)',   # olive
        'rgb(23, 190, 207)',   # cyan
        'rgb(141, 211, 199)',
        'rgb(255, 255, 179)',
        'rgb(190, 186, 218)',
        'rgb(251, 128, 114)',
        'rgb(128, 177, 211)',
        'rgb(253, 180, 98)',
        'rgb(179, 222, 105)',
        'rgb(252, 205, 229)',
        'rgb(217, 217, 217)',
        'rgb(188, 128, 189)'
    ]
    return colors[:n]

def get_distribution_data(df, company, column):
    """Get distribution percentages for a specific company and column"""
    company_data = df[df['winner'] == company]
    total_projects = len(company_data)
    if total_projects == 0:
        return pd.Series()
    
    distribution = company_data[column].value_counts()
    distribution_pct = (distribution / total_projects) * 100
    return distribution_pct

def HHIAnalysis():
    SessionState.initialize_state()
    
    st.title("Market Concentration Analysis (HHI)")
    
    show_context_info()
    df, source = get_analysis_data()
    
    if df is None:
        st.info("No context data loaded. Use the Context Manager to add collections for analysis.")
        return
    
    st.info(f"📊 Analyzing data from: {source}")

    if df is not None and not df.empty:
        # Calculate market shares
        total_value = df['sum_price_agree'].sum()
        company_shares = (df.groupby('winner')['sum_price_agree']
                        .sum()
                        .sort_values(ascending=False)
                        .reset_index())
        
        company_shares['market_share'] = (company_shares['sum_price_agree'] / total_value) * 100
        company_shares['value_millions'] = company_shares['sum_price_agree']
        
        # Check number of companies
        if len(company_shares) > 20:
            st.warning("⚠️ Analysis limited to top 20 companies due to visualization constraints.")
            company_shares = company_shares.head(20)
        
        # Calculate HHI
        hhi = calculate_hhi(company_shares['market_share'])
        status, concentration = interpret_hhi(hhi)
        
        # Display HHI metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("HHI Index", f"{hhi:,.0f}")
        with col2:
            st.metric("Market Status", status)
        with col3:
            st.metric("Concentration Level", concentration)

        # Get colors for each company
        company_colors = get_company_colors(len(company_shares))
        
        # Create distribution visualizations for each company
        st.markdown("### 📊 Company Distributions")
        
        # Add selection for number of companies to display
        num_companies = st.slider("Number of companies to show", 
                                min_value=1, 
                                max_value=len(company_shares), 
                                value=min(5, len(company_shares)))
        
        # Display distributions for selected number of companies
        for idx, company_data in company_shares.head(num_companies).iterrows():
            company = company_data['winner']
            
            st.markdown(f"#### {company}")
            st.caption(f"Market Share: {company_data['market_share']:.2f}% | Value: ฿{company_data['value_millions']:.2f}M")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Purchase Methods Distribution**")
                purchase_dist = get_distribution_data(df, company, 'purchase_method_name')
                if not purchase_dist.empty:
                    fig1 = create_distribution_bar(
                        purchase_dist,
                        "Distribution",
                        base_color=company_colors[idx]
                    )
                    st.plotly_chart(fig1, use_container_width=True)
                else:
                    st.info("No purchase method data available")
            
            with col2:
                st.markdown("**Project Types Distribution**")
                project_dist = get_distribution_data(df, company, 'project_type_name')
                if not project_dist.empty:
                    fig2 = create_distribution_bar(
                        project_dist,
                        "Distribution",
                        base_color=company_colors[idx]
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("No project type data available")
            
            st.markdown("---")
        
        # Display detailed metrics table
        st.markdown("### 📋 Company Market Share Details")
        
        display_df = company_shares.copy()
        display_df['market_share'] = display_df['market_share'].round(2)
        display_df['value_millions'] = display_df['value_millions'].round(2)
        
        st.dataframe(
            display_df.rename(columns={
                'winner': 'Company',
                'market_share': 'Market Share (%)',
                'value_millions': 'Total Value (M฿)'
            }),
            column_config={
                'Company': st.column_config.TextColumn(
                    'Company',
                    width='large'
                ),
                'Market Share (%)': st.column_config.NumberColumn(
                    'Market Share (%)',
                    format="%.2f%%"
                ),
                'Total Value (M฿)': st.column_config.NumberColumn(
                    'Total Value (M฿)',
                    format="%.2f"
                )
            },
            hide_index=True
        )
        
        # Market concentration curve
        st.markdown("### 🎯 Market Concentration Analysis")
        
        company_shares['cumulative_share'] = company_shares['market_share'].cumsum()
        
        fig2 = go.Figure()
        
        # Perfect competition line
        x = list(range(len(company_shares) + 1))
        y = [i * (100 / len(company_shares)) for i in range(len(company_shares) + 1)]
        fig2.add_trace(go.Scatter(
            x=x,
            y=y,
            name='Perfect Competition',
            line=dict(dash='dash', color='gray'),
            hovertemplate='Companies: %{x}<br>Market Share: %{y:.1f}%<extra></extra>'
        ))
        
        # Actual concentration curve
        fig2.add_trace(go.Scatter(
            x=list(range(len(company_shares))),
            y=company_shares['cumulative_share'],
            name='Actual Concentration',
            line=dict(color='rgb(31, 119, 180)'),
            hovertemplate='Companies: %{x}<br>Cumulative Share: %{y:.1f}%<extra></extra>'
        ))
        
        fig2.update_layout(
            title='Market Concentration Curve',
            xaxis_title='Number of Companies',
            yaxis_title='Cumulative Market Share (%)',
            height=500,
            showlegend=True,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        
        # Add explanation
        with st.expander("ℹ️ About HHI and Market Concentration"):
            st.markdown("""
            The Herfindahl-Hirschman Index (HHI) is a measure of market concentration that ranges from close to 0 to 10,000:
            
            - **HHI < 1,500**: Competitive market
            - **1,500 ≤ HHI ≤ 2,500**: Moderately concentrated market
            - **HHI > 2,500**: Highly concentrated market
            
            The market concentration curve shows:
            - The gray dashed line represents perfect competition (equal market shares)
            - The blue line shows actual market concentration
            - The greater the gap between the lines, the higher the market concentration
            """)
    
    else:
        st.warning("No projects found. Please adjust your filters or add collections to the context.")

if __name__ == "__main__":
    HHIAnalysis()