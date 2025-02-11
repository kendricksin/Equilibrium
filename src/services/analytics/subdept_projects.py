import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Any
import streamlit as st
import math

class SubDepartmentProjectsService:
    """Service for analyzing project distribution across sub-departments"""
    
    # Safe, light colors for year differentiation
    SAFE_COLORS = [
        '#FFB6C1',  # lightpink
        '#98FB98',  # palegreen
        '#87CEFA',  # lightskyblue
        '#DDA0DD',  # plum
        '#F0E68C',  # khaki
        '#E6E6FA',  # lavender
        '#FFA07A',  # lightsalmon
        '#B0E0E6',  # powderblue
        '#FFE4B5',  # moccasin
    ]
    
    VALUE_RANGES = [
        {'name': '>300M', 'min': 300, 'max': float('inf'), 'color': '#87CEFA'},
        {'name': '100-300M', 'min': 100, 'max': 300, 'color': '#FFB6C1'},
        {'name': '50-100M', 'min': 50, 'max': 100, 'color': '#98FB98'},
        {'name': '10-50M', 'min': 10, 'max': 50, 'color': '#DDA0DD'},
        {'name': '0-10M', 'min': 0, 'max': 10, 'color': '#F0E68C'}
    ]
    
    @staticmethod
    def prepare_data(df: pd.DataFrame, top_n: int = 15) -> Dict[str, pd.DataFrame]:
        """Prepare data for sub-department projects visualization by value range"""
        # Convert to millions
        df = df.copy()
        df['value_millions'] = df['sum_price_agree'] / 1e6
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        
        # Replace missing sub-departments with 'Other'
        df['dept_sub_name'] = df['dept_sub_name'].fillna('Other')
        
        # Split data by value ranges
        range_data = {}
        for value_range in SubDepartmentProjectsService.VALUE_RANGES:
            # Filter for value range
            range_df = df[
                (df['value_millions'] >= value_range['min']) &
                (df['value_millions'] < value_range['max'])
            ].copy()
            
            if not range_df.empty:
                # Get top sub-departments for this range
                subdept_totals = range_df.groupby('dept_sub_name')['value_millions'].sum()
                top_subdepts = subdept_totals.sort_values(ascending=False).head(top_n).index
                
                # Filter for top sub-departments and sort
                range_df = range_df[range_df['dept_sub_name'].isin(top_subdepts)]
                range_df = range_df.sort_values(['dept_sub_name', 'transaction_date'])
                
                range_data[value_range['name']] = range_df
        
        return range_data

    @staticmethod
    def create_chart_for_range(df: pd.DataFrame, range_name: str, color: str) -> go.Figure:
        """Create individual chart for a value range"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Creating chart for range: {range_name}")
        logger.info(f"Input DataFrame shape: {df.shape}")
        
        if df.empty:
            logger.error(f"Empty DataFrame for range {range_name}")
            raise ValueError(f"Empty DataFrame for range {range_name}")
        
        # Get sub-departments sorted by total value
        subdept_totals = df.groupby('dept_sub_name')['value_millions'].sum()
        subdepts = subdept_totals.sort_values(ascending=False).index
        
        # Calculate project counts per sub-department
        project_counts = df.groupby('dept_sub_name').size()
        
        fig = go.Figure()
        
        # Create a color map for years
        years = sorted(df['transaction_date'].dt.year.unique())
        year_colors = {
            year: SubDepartmentProjectsService.SAFE_COLORS[i % len(SubDepartmentProjectsService.SAFE_COLORS)]
            for i, year in enumerate(years)
        }
        
        # Add bars for each project
        for _, row_data in df.iterrows():
            # Calculate price cut percentage with validation
            try:
                if row_data['price_build'] == 0:
                    logger.error(f"Zero price_build value found for project {row_data['project_name']}")
                    price_cut = 0
                else:
                    price_cut = ((row_data['sum_price_agree'] / row_data['price_build']) - 1) * 100
            except Exception as e:
                logger.error(f"Error calculating price cut for project {row_data['project_name']}: {str(e)}")
                price_cut = 0
            
            # Get year and its assigned color
            year = row_data['transaction_date'].year
            year_color = year_colors[year]

            # Only show in legend if it's the first occurrence of this year
            show_in_legend = str(year) not in [trace.name for trace in fig.data]

            fig.add_trace(
                go.Bar(
                    name=str(year),
                    x=[row_data['dept_sub_name']],
                    y=[row_data['value_millions']],
                    orientation='v',
                    showlegend=show_in_legend,
                    marker=dict(
                        color=year_color,
                        line=dict(color='rgb(50, 50, 50)', width=1)
                    ),
                    customdata=[[
                        row_data['project_name'],
                        row_data['winner'],
                        row_data['value_millions'],
                        row_data['transaction_date'].strftime('%Y-%m-%d'),
                        price_cut,
                        row_data.get('dept_name', 'N/A')
                    ]],
                    hovertemplate=(
                        "<b>%{customdata[0]}</b><br>" +
                        "Company: %{customdata[1]}<br>" +
                        "฿%{customdata[2]:.1f}M | %{customdata[3]}<br>" +
                        "Price Cut: %{customdata[4]:.1f}%<br>" +
                        "Department: %{customdata[5]}" +
                        "<extra></extra>"
                    ),
                    hoverlabel=dict(
                        bgcolor="rgba(255, 255, 255, 0.7)",
                        bordercolor="rgba(0, 0, 0, 0.1)",
                        font_size=12,
                        font_family="Arial",
                        namelength=-1
                    )
                )
            )
        
        # Add project count annotations at the top of each bar stack
        for subdept in subdepts:
            total_value = subdept_totals[subdept]
            project_count = project_counts[subdept]
            
            fig.add_annotation(
                x=subdept,
                y=total_value,
                text=f"{project_count} projects",
                showarrow=False,
                yshift=10,
                font=dict(size=10),
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0, 0, 0, 0.1)",
                borderwidth=1,
                borderpad=4
            )
        
        # Update layout
        fig.update_layout(
            title=f"Sub-department Projects {range_name}",
            height=600,  # Slightly taller for better readability
            showlegend=True,
            legend=dict(
                title="Transaction Year",
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            barmode='stack',
            bargap=0.2,
            margin=dict(t=40, l=20, r=20, b=120),  # More bottom margin for labels
            xaxis=dict(
                categoryorder='array',
                categoryarray=subdepts,
                title='Sub-department',
                tickangle=45,
                tickfont=dict(size=10)  # Smaller font for long names
            ),
            yaxis=dict(
                title='Project Value (Million ฿)'
            )
        )
        
        return fig
    
    @staticmethod
    def get_range_statistics(range_data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        """Calculate statistics for each value range"""
        stats = []
        for value_range in SubDepartmentProjectsService.VALUE_RANGES:
            range_name = value_range['name']
            if range_name in range_data:
                df = range_data[range_name]
                stats.append({
                    'range': range_name,
                    'total_projects': len(df),
                    'total_subdepts': len(df['dept_sub_name'].unique()),
                    'total_value': df['value_millions'].sum(),
                    'avg_value': df['value_millions'].mean(),
                    'color': value_range['color']
                })
            else:
                stats.append({
                    'range': range_name,
                    'total_projects': 0,
                    'total_subdepts': 0,
                    'total_value': 0,
                    'avg_value': 0,
                    'color': value_range['color']
                })
        return stats
    
def display_subdepartment_distribution(display_df: Any):
    """Display sub-department distribution analysis with value range charts"""
    try:
        # Initial data preparation
        range_data = SubDepartmentProjectsService.prepare_data(display_df)
        stats = SubDepartmentProjectsService.get_range_statistics(range_data)
        
        # Create container for visualization
        with st.expander("### 📊 Sub-department Project Distribution Analysis", expanded=True):
            
            # Show statistics grid
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Summary metrics
                total_projects = sum(stat['total_projects'] for stat in stats)
                total_value = sum(stat['total_value'] for stat in stats)
                total_subdepts = sum(stat['total_subdepts'] for stat in stats)
                
                st.markdown(f"""
                ### Overall Summary
                - **Total Projects**: {total_projects:,}
                - **Total Value**: ฿{total_value:,.1f}M
                - **Sub-departments**: {total_subdepts:,}
                """)
            
            with col2:
                # Value range breakdown
                st.markdown("### Value Range Breakdown")
                for stat in stats:
                    if stat['total_projects'] > 0:  # Only show non-empty ranges
                        with st.container():
                            st.markdown(
                                f"""<div style='padding: 8px; border-radius: 5px; background-color: {stat['color']}20;'>
                                {stat['range']}: {stat['total_projects']} projects (฿{stat['total_value']:.1f}M)
                                </div>""",
                                unsafe_allow_html=True
                            )
        
        # Charts section
        st.markdown("### Sub-dept Distribution Charts")
        
        # Create tabs for different value ranges
        if any(range_name in range_data for range_name in [r['name'] for r in SubDepartmentProjectsService.VALUE_RANGES]):
            tabs = st.tabs([r['name'] for r in SubDepartmentProjectsService.VALUE_RANGES])
            
            for tab, value_range in zip(tabs, SubDepartmentProjectsService.VALUE_RANGES):
                range_name = value_range['name']
                
                with tab:
                    if range_name in range_data:
                        df = range_data[range_name]
                        
                        # Show range stats
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Projects", f"{len(df):,}")
                        with col2:
                            st.metric("Total Value", f"฿{df['value_millions'].sum():,.1f}M")
                        with col3:
                            st.metric("Sub-departments", f"{len(df['dept_sub_name'].unique()):,}")
                        
                        # Create and display chart
                        fig = SubDepartmentProjectsService.create_chart_for_range(
                            df,
                            range_name,
                            value_range['color']
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info(f"No projects found in the {range_name} range")
        else:
            st.warning("No data available for visualization")
                    
    except Exception as e:
        st.error(f"Error creating sub-department distribution charts: {str(e)}")
        if st.development:
            st.exception(e)
