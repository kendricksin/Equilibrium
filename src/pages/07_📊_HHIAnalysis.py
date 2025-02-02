# src/pages/07_📊_HHIAnalysis.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from components.layout.MetricsSummary import create_distribution_bar
from state.session import SessionState
from special_functions.context_util import get_analysis_data, show_context_info
from services.analytics.company_comparison import CompanyComparisonService
from typing import List

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
    if hhi < 900:
        return "Competitive", "Low"
    elif hhi < 1600:
        return "Moderate", "Medium"
    else:
        return "Dominated", "High"

def get_company_colors(n: int) -> List[str]:
    """
    Get up to 20 distinct colors for company visualizations.
    If more than 20 colors are requested, returns 20.
    
    Args:
        n (int): Number of colors requested
        
    Returns:
        List[str]: List of RGB color strings (maximum 20)
    """
    colors = [
        'rgb(31, 119, 180)',    # blue
        'rgb(255, 127, 14)',    # orange
        'rgb(44, 160, 44)',     # green
        'rgb(214, 39, 40)',     # red
        'rgb(148, 103, 189)',   # purple
        'rgb(140, 86, 75)',     # brown
        'rgb(227, 119, 194)',   # pink
        'rgb(127, 127, 127)',   # gray
        'rgb(188, 189, 34)',    # olive
        'rgb(23, 190, 207)',    # cyan
        'rgb(141, 211, 199)',   # light blue-green
        'rgb(255, 255, 179)',   # light yellow
        'rgb(190, 186, 218)',   # light purple
        'rgb(251, 128, 114)',   # light red
        'rgb(128, 177, 211)',   # light blue
        'rgb(253, 180, 98)',    # light orange
        'rgb(179, 222, 105)',   # light green
        'rgb(252, 205, 229)',   # light pink
        'rgb(217, 217, 217)',   # light gray
        'rgb(188, 128, 189)'    # medium purple
    ]
    
    # Return at most 20 colors
    return colors[:min(n, 20)]

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
        # Calculate market shares and price cuts
        # First calculate price cuts for each project
        df['price_cut'] = ((df['sum_price_agree'] / df['price_build'] - 1) * 100)
        
        # Group by company and calculate metrics
        company_metrics = df.groupby('winner').agg({
            'sum_price_agree': 'sum',
            'price_cut': ['mean', 'min', 'max'],
            'project_id': 'count'
        })
        
        # Flatten column names
        company_metrics.columns = [
            'sum_price_agree',
            'avg_price_cut',
            'min_price_cut',
            'max_price_cut',
            'project_count'
        ]
        
        # Calculate market shares
        total_value = company_metrics['sum_price_agree'].sum()
        company_shares = company_metrics.reset_index()
        company_shares['market_share'] = (company_shares['sum_price_agree'] / total_value) * 100
        company_shares['value_millions'] = company_shares['sum_price_agree']

        # Sort by market share
        company_shares = company_shares.sort_values('market_share', ascending=False)
        
        # Check number of companies
        if len(company_shares) > 20:
            st.warning("⚠️ Analysis limited to top 20 companies due to visualization constraints.")
            company_shares = company_shares.head(20)
        
        # Calculate HHI
        hhi = calculate_hhi(company_shares['market_share'])
        status, concentration = interpret_hhi(hhi)
        
        # Display HHI metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("HHI Index", f"{hhi:,.0f}")
        with col2:
            st.metric("Market category", status)
        with col3:
            st.metric("Concentration Level", concentration)
        with col4:
            avg_price_cut = company_shares['avg_price_cut'].mean()
            st.metric(
                "Avg Price Cut", 
                f"{avg_price_cut:.1f}%",
                delta=f"{avg_price_cut:.1f}%",
                delta_color="inverse" if avg_price_cut < -5 else "normal"
            )
        with col5:
            max_price_cut = company_shares['min_price_cut'].min()  # Most negative price cut
            st.metric(
                "Max Price Cut",
                f"{max_price_cut:.1f}%",
                delta=f"{max_price_cut:.1f}%",
                delta_color="inverse" if max_price_cut < -10 else "normal"
            )

        # Get colors for each company
        company_colors = get_company_colors(len(company_shares))
        
        # Create distribution visualizations for each company
        st.markdown("### 📊 Company Distributions")
        
        # Add selection for number of companies to display
        num_companies = st.slider("Number of companies to show", 
                                min_value=0, 
                                max_value=len(company_shares), 
                                value=min(2, len(company_shares)))
        
        # Group Competition Analysis Section
        st.markdown("### 🎯 Group Competition Analysis")
        st.markdown("Analyzing competition patterns among top companies")
        
        # Calculate group metrics
        group_metrics = CompanyComparisonService.calculate_group_competition_metrics(df, company_shares['winner'].tolist())
        
        # Display competition heatmaps
        col1, col2 = st.columns(2)
        
        with col1:
            # Direct competitions heatmap
            comp_fig = CompanyComparisonService.create_competition_heatmap(
                group_metrics['competition_matrix'],
                'Direct Competitions Between Companies'
            )
            st.plotly_chart(comp_fig, use_container_width=True)
        
        with col2:
            # Department overlap heatmap
            overlap_fig = CompanyComparisonService.create_competition_heatmap(
                group_metrics['dept_overlap_matrix'],
                'Sub-Department Overlap (%)'
            )
            st.plotly_chart(overlap_fig, use_container_width=True)
        
        # Network visualization
        st.markdown("#### Competition Network")
        min_competitions = st.slider(
            "Minimum competitions for connection",
            min_value=1,
            max_value=20,
            value=5
        )
        
        network_fig = CompanyComparisonService.create_network_graph(group_metrics, threshold=min_competitions)
        st.plotly_chart(network_fig, use_container_width=True)
        
        # Key insights
        insights = CompanyComparisonService.calculate_group_insights(group_metrics)
        
        with st.expander("View Competition Insights"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Top Competing Pairs**")
                for (comp1, comp2), competitions in insights['top_competitions'].items():
                    st.markdown(f"- {comp1} vs {comp2}: {int(competitions)} competitions")
            
            with col2:
                st.markdown("**Highest Department Overlaps**")
                for (comp1, comp2), overlap in insights['top_overlaps'].items():
                    st.markdown(f"- {comp1} & {comp2}: {overlap:.1f}% overlap")
            
            # Competition intensity metrics
            st.markdown("**Most Active Competitors**")
            intensity_df = pd.DataFrame(list(insights['competition_intensity'].items()),
                                      columns=['Company', 'Total Competitions'])
            intensity_df = intensity_df.sort_values('Total Competitions', ascending=False).head(5)
            
            st.dataframe(
                intensity_df,
                column_config={
                    'Company': st.column_config.TextColumn('Company'),
                    'Total Competitions': st.column_config.NumberColumn(
                        'Total Competitions',
                        format="%d"
                    )
                },
                hide_index=True
            )

        # Display distributions for selected number of companies
        for i, (_, company_data) in enumerate(company_shares.head(num_companies).iterrows()):
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
                        base_color=company_colors[i]  # Use i instead of idx
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
                        base_color=company_colors[i]  # Use i instead of idx
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
            
            - **HHI < 900**: Competitive market (Top companies own less than 30% market share)
            - **900 ≤ HHI ≤ 1,600**: Moderately concentrated market (Top companies own more than 30% market share)
            - **HHI > 1,600**: Highly concentrated market (Top companies own more than 40% market share)
            
            The market concentration curve shows:
            - The gray dashed line represents perfect competition (equal market shares)
            - The blue line shows actual market concentration
            - The greater the gap between the lines, the higher the market concentration
            """)
    
    else:
        st.warning("No projects found. Please adjust your filters or add collections to the context.")

if __name__ == "__main__":
    HHIAnalysis()