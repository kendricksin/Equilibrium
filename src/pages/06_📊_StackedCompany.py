# src/pages/StackedCompany.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from components.layout.MetricsSummary import MetricsSummary
from state.session import SessionState
from special_functions.context_util import get_analysis_data, show_context_info
from components.layout.ContextSelector import ContextSelector

st.set_page_config(layout="wide")

def StackedCompany():
    ContextSelector()

    SessionState.initialize_state()

    # Show context information if available
    show_context_info()
    
    # Get data either from context or filters
    df, source = get_analysis_data()
    
    if df is None:
        st.info("No context data loaded. Use the Context Manager to add collections for analysis.")
    else:
        # Using context data
        st.info(f"📊 Analyzing data from: {source}")

    if df is not None and not df.empty:
        st.markdown("### Company Distribution")

        # Add controls
        col1, col2, col3 = st.columns(3)
        with col1:
            time_period = st.selectbox(
                "Time Period",
                ["Year", "Quarter", "Month"]
            )
        with col2:
            num_companies = st.slider(
                "Number of Companies to Show",
                min_value=5,
                max_value=30,
                value=10
            )

        # Process data based on selected time period
        # Convert transaction_date to datetime if it's not already
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        
        if time_period == "Year":
            df['time_group'] = df['transaction_date'].dt.year
        elif time_period == "Quarter":
            # Create a sortable quarter format (YYYY-Q)
            df['time_group'] = (df['transaction_date'].dt.year.astype(str) + "-Q" + 
                            df['transaction_date'].dt.quarter.astype(str))
        else:
            # Create a sortable month format (YYYY-MM)
            df['time_group'] = df['transaction_date'].dt.strftime('%Y-%m')

        # Get top companies by total value
        top_companies = df.groupby('winner')['sum_price_agree'].sum().nlargest(num_companies).index

        # Filter for top companies and sort by time_group
        company_data = df[df['winner'].isin(top_companies)].groupby(['time_group', 'winner']).agg({
            'sum_price_agree': 'sum',
            'project_id': 'count'
        }).reset_index()

        # Sort by time_group to ensure chronological order
        company_data = company_data.sort_values('time_group')

        company_data['sum_price_agree'] = company_data['sum_price_agree'] / 1e6

        # Create stacked bar chart
        fig2 = go.Figure()

        for company in top_companies:
            company_subset = company_data[company_data['winner'] == company]
            fig2.add_trace(go.Bar(
                name=company,
                x=company_subset['time_group'],
                y=company_subset['sum_price_agree'],
                text=company_subset['project_id'],
                textposition='inside',
                hovertemplate="Company: %{fullData.name}<br>" +
                                f"{time_period}: " + "%{x}<br>" +
                                "Value: %{y:.0f}M฿<br>" +
                                "Projects: %{text}<extra></extra>"
            ))

        fig2.update_layout(
            barmode='stack',
            title=f'Project Distribution by Company ({time_period})',
            xaxis_title=time_period,
            yaxis_title='Total Value (Million Baht)',
            height=600,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=1.05
            )
        )

        st.plotly_chart(fig2, use_container_width=True)

        st.markdown("### Quarterly Project Analysis")
        
        # Add quarter column
        df['quarter'] = df['transaction_date'].dt.to_period('Q')
        quarterly_data = df.groupby('quarter').agg({
            'sum_price_agree': 'sum',
            'project_id': 'count'
        }).reset_index()
        
        # Convert quarters to string format and price to millions
        quarterly_data['quarter'] = quarterly_data['quarter'].astype(str)
        quarterly_data['sum_price_agree'] = quarterly_data['sum_price_agree'] / 1e6

        fig = go.Figure()

        # Bar chart for values
        fig.add_trace(go.Bar(
            x=quarterly_data['quarter'],
            y=quarterly_data['sum_price_agree'],
            name='Total Value',
            text=quarterly_data['sum_price_agree'].round(0).astype(str) + ' MB',
            textposition='outside',
            yaxis='y',
            marker_color='#2563eb'
        ))

        # Line chart for project count
        fig.add_trace(go.Scatter(
            x=quarterly_data['quarter'], 
            y=quarterly_data['project_id'],
            name='Project Count',
            text=quarterly_data['project_id'].astype(str),
            textposition='top center',
            mode='lines+markers+text',
            yaxis='y2',
            line=dict(color='#dc2626', width=2),
            marker=dict(size=8)
        ))

        fig.update_layout(
            title='Project Values and Counts by Quarter',
            xaxis_title='Quarter',
            yaxis=dict(
                title='Total Value (Million Baht)',
                titlefont=dict(color='#2563eb'),
                tickfont=dict(color='#2563eb')
            ),
            yaxis2=dict(
                title='Number of Projects',
                titlefont=dict(color='#dc2626'),
                tickfont=dict(color='#dc2626'),
                overlaying='y',
                side='right'
            ),
            showlegend=True,
            height=600,
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

        # Quarterly comparison metrics
        if len(quarterly_data) >= 2:
            col1, col2 = st.columns(2)
            with col1:
                latest_q = quarterly_data['quarter'].iloc[-1]
                prev_q = quarterly_data['quarter'].iloc[-2]
                current_value = quarterly_data['sum_price_agree'].iloc[-1]
                prev_value = quarterly_data['sum_price_agree'].iloc[-2]
                value_change = ((current_value - prev_value) / prev_value) * 100
                st.metric(
                    f"Value Change ({prev_q} to {latest_q})", 
                    f"{value_change:.1f}%", 
                    delta=f"{value_change:.1f}%"
                )

            with col2:
                current_count = quarterly_data['project_id'].iloc[-1]
                prev_count = quarterly_data['project_id'].iloc[-2]
                count_change = ((current_count - prev_count) / prev_count) * 100
                st.metric(
                    f"Project Count Change ({prev_q} to {latest_q})", 
                    f"{count_change:.1f}%", 
                    delta=f"{count_change:.1f}%"
                )

    else:
        st.warning("No projects found. Please adjust your filters or add collections to the context.")

if __name__ == "__main__":
    StackedCompany()