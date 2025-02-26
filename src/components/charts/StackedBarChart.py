# src/components/charts/StackedBarChart.py

import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict, Any, Optional
import streamlit as st
import logging

logger = logging.getLogger(__name__)

class StackedBarChart:
    """Reusable stacked bar chart visualization component"""
    
    # Safe, light colors from Plotly's built-in colors
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
        '#F5DEB3',  # wheat
        '#FFDAB9',  # peachpuff
        '#AFEEEE',  # paleturquoise
        '#D8BFD8',  # thistle
        '#DEB887',  # burlywood
        '#FA8072',  # salmon
    ]
    
    def __init__(
        self,
        data: pd.DataFrame,
        x_column: str,
        y_column: str,
        color_column: str,
        title: str = "",
        height: int = 500,
        show_legend: bool = True
    ):
        """
        Initialize StackedBarChart
        
        Args:
            data: DataFrame containing the data
            x_column: Column name for x-axis categories
            y_column: Column name for y-axis values
            color_column: Column name for color grouping
            title: Chart title
            height: Chart height in pixels
            show_legend: Whether to show the legend
        """
        self.data = data
        self.x_column = x_column
        self.y_column = y_column
        self.color_column = color_column
        self.title = title
        self.height = height
        self.show_legend = show_legend
    
    def render(
        self,
        key: Optional[str] = None,
        use_container_width: bool = True,
        show_totals: bool = True
    ):
        """
        Render the stacked bar chart
        
        Args:
            key: Unique key for the component
            use_container_width: Whether to use container width
            show_totals: Whether to show total values on top of bars
        """
        try:
            if len(self.data) == 0:
                st.warning("No data available for visualization")
                return
            
            # Get unique categories for color grouping
            categories = sorted(self.data[self.color_column].unique())
            
            # Create color map
            color_map = {
                cat: self.SAFE_COLORS[i % len(self.SAFE_COLORS)]
                for i, cat in enumerate(categories)
            }
            
            # Initialize figure
            fig = go.Figure()
            
            # Add traces for each category
            for category in categories:
                category_data = self.data[self.data[self.color_column] == category]
                
                # Only show in legend if it's the first occurrence
                show_in_legend = True
                
                fig.add_trace(
                    go.Bar(
                        name=str(category),
                        x=category_data[self.x_column],
                        y=category_data[self.y_column],
                        marker=dict(
                            color=color_map[category],
                            line=dict(color='rgb(50, 50, 50)', width=1)
                        ),
                        showlegend=show_in_legend,
                        hovertemplate=(
                            "<b>%{x}</b><br>" +
                            f"{self.color_column}: {category}<br>" +
                            f"{self.y_column}: %{{y:,.0f}}<br>" +
                            "<extra></extra>"
                        )
                    )
                )
            
            # Add total annotations if requested
            if show_totals:
                # Calculate totals for each x category
                totals = self.data.groupby(self.x_column)[self.y_column].sum()
                
                for x_cat in totals.index:
                    total = totals[x_cat]
                    fig.add_annotation(
                        x=x_cat,
                        y=total,
                        text=f"Total: {total:,.0f}",
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
                title=self.title,
                height=self.height,
                showlegend=self.show_legend,
                legend=dict(
                    title=self.color_column,
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                barmode='stack',
                bargap=0.2,
                margin=dict(t=50, l=25, r=25, b=100),
                xaxis=dict(
                    title=self.x_column,
                    tickangle=45
                ),
                yaxis=dict(
                    title=self.y_column
                ),
                hoverlabel=dict(
                    bgcolor="rgba(255, 255, 255, 0.7)",
                    bordercolor="rgba(0, 0, 0, 0.1)",
                    font_size=12,
                    font_family="Arial",
                    namelength=-1
                )
            )
            
            # Render in Streamlit
            st.plotly_chart(
                fig,
                use_container_width=use_container_width,
                key=key
            )
            
        except Exception as e:
            logger.error(f"Error rendering stacked bar chart: {e}")
            st.error("Error rendering visualization") 

def get_value_range_label(value: float) -> str:
    """Get value range label for a given project value"""
    if value >= 300 * 1e6:
        return "300M+"
    elif value >= 100 * 1e6:
        return "100-300M"
    elif value >= 50 * 1e6:
        return "50-100M"
    elif value >= 10 * 1e6:
        return "10-50M"
    else:
        return "0-10M"

def generate_subdept_charts(df: pd.DataFrame, year_column: str = 'budget_year'):
    """Generate subdepartment charts broken down by value ranges"""
    # Make sure transaction_date is datetime
    if 'transaction_date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['transaction_date']):
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    
    # Add year column if not present
    if year_column not in df.columns and 'transaction_date' in df.columns:
        df[year_column] = df['transaction_date'].dt.year
    
    # Add value range column
    df['value_range'] = df['sum_price_agree'].apply(get_value_range_label)
    
    # Define value ranges for filtering and display
    value_ranges = [
        {"label": "300M+", "min": 300 * 1e6, "max": float('inf')},
        {"label": "100-300M", "min": 100 * 1e6, "max": 300 * 1e6},
        {"label": "50-100M", "min": 50 * 1e6, "max": 100 * 1e6},
        {"label": "10-50M", "min": 10 * 1e6, "max": 50 * 1e6},
        {"label": "0-10M", "min": 0, "max": 10 * 1e6},
    ]
    
    # Create tabs for value ranges
    st.markdown("## Sub-dept Distribution Charts")
    
    # Create tab buttons
    tab_cols = st.columns(len(value_ranges))
    selected_range = None
    
    for i, vrange in enumerate(value_ranges):
        with tab_cols[i]:
            if st.button(vrange["label"], key=f"tab_{vrange['label']}", 
                         use_container_width=True,
                         type="primary" if vrange["label"] == "100-300M" else "secondary"):
                selected_range = vrange["label"]
    
    # Set default if none selected
    if selected_range is None:
        selected_range = "100-300M"
    
    # Filter data for selected range
    range_info = next(r for r in value_ranges if r["label"] == selected_range)
    range_df = df[(df['sum_price_agree'] >= range_info["min"]) & 
                  (df['sum_price_agree'] < range_info["max"])]
    
    # Show summary metrics
    metric_cols = st.columns(3)
    with metric_cols[0]:
        st.metric("Projects", f"{len(range_df)}")
    with metric_cols[1]:
        st.metric("Total Value", f"฿{range_df['sum_price_agree'].sum()/1e6:.1f}M")
    with metric_cols[2]:
        st.metric("Sub-departments", f"{range_df['dept_sub_name'].nunique()}")
    
    # Prepare data for charts - group by subdepartment and year
    if not range_df.empty:
        # First, calculate project counts for each subdepartment
        project_counts = range_df.groupby('dept_sub_name').size().reset_index(name='project_count')
        
        # Group data by subdepartment and year for the stacked bar chart
        subdept_year_data = range_df.groupby(['dept_sub_name', year_column])['sum_price_agree'].sum().reset_index()
        subdept_year_data['sum_price_agree_M'] = subdept_year_data['sum_price_agree'] / 1e6
        
        # Get total by subdepartment for sorting and label creation
        subdept_totals = subdept_year_data.groupby('dept_sub_name')['sum_price_agree'].sum().reset_index()
        subdept_totals = subdept_totals.sort_values('sum_price_agree', ascending=False)  # Sort descending so most value on left
        
        # Add project counts to the totals dataframe
        subdept_totals = pd.merge(subdept_totals, project_counts, on='dept_sub_name')
        
        # Get top 15 subdepartments by value
        top_subdepts = subdept_totals.head(15)['dept_sub_name'].tolist()
        
        # Filter out just the top subdepartments for display
        top_subdepts_data = subdept_totals[subdept_totals['dept_sub_name'].isin(top_subdepts)].copy()
        
        # Create new labels with project counts and total values on a separate line
        top_subdepts_data['display_name'] = top_subdepts_data.apply(
            lambda x: f"{x['dept_sub_name']}\n({x['project_count']} proj, ฿{x['sum_price_agree']/1e6:.0f}M)",
            axis=1
        )
        
        # Create display name mapping
        display_name_map = dict(zip(top_subdepts_data['dept_sub_name'], top_subdepts_data['display_name']))
        
        # Filter for top subdepartments and prepare for chart
        chart_data = subdept_year_data[subdept_year_data['dept_sub_name'].isin(top_subdepts)].copy()
        
        # Replace department names with display names
        chart_data['display_name'] = chart_data['dept_sub_name'].map(display_name_map)
        
        # Create a mapping that maintains the original sort order (by value)
        ordered_subdepts_dict = {dept: i for i, dept in enumerate(top_subdepts)}
        
        # Add a sort key based on the original ordering
        chart_data['sort_key'] = chart_data['dept_sub_name'].map(ordered_subdepts_dict)
        
        # Sort the dataframe
        chart_data = chart_data.sort_values('sort_key')
        
        # Create chart title with subdepartment count
        chart_title = f"Sub-department Projects {selected_range} (Top {len(top_subdepts)})"
        
        # Update the StackedBarChart class to handle pre-sorted data
        class SortedStackedBarChart(StackedBarChart):
            def render(self, key=None, use_container_width=True, show_totals=True):
                try:
                    if len(self.data) == 0:
                        st.warning("No data available for visualization")
                        return
                    
                    # Get unique categories for color grouping
                    categories = sorted(self.data[self.color_column].unique())
                    
                    # Create color map
                    color_map = {
                        cat: self.SAFE_COLORS[i % len(self.SAFE_COLORS)]
                        for i, cat in enumerate(categories)
                    }
                    
                    # Initialize figure
                    fig = go.Figure()
                    
                    # Get unique x values in the order they appear in the dataframe
                    # This preserves the pre-sorting we did
                    unique_x_values = self.data[self.x_column].unique()
                    
                    # Add traces for each category
                    for category in categories:
                        category_data = self.data[self.data[self.color_column] == category]
                        
                        fig.add_trace(
                            go.Bar(
                                name=str(category),
                                x=category_data[self.x_column],
                                y=category_data[self.y_column],
                                marker=dict(
                                    color=color_map[category],
                                    line=dict(color='rgb(50, 50, 50)', width=1)
                                ),
                                showlegend=True,
                                hovertemplate=(
                                    "<b>%{x}</b><br>" +
                                    f"{self.color_column}: {category}<br>" +
                                    f"{self.y_column}: %{{y:,.0f}}<br>" +
                                    "<extra></extra>"
                                )
                            )
                        )
                    
                    # Add total annotations if requested
                    if show_totals:
                        # Calculate totals for each x category
                        totals_df = self.data.groupby(self.x_column)[self.y_column].sum().reset_index()
                        
                        # Maintain original order
                        for x_cat in unique_x_values:
                            total = totals_df[totals_df[self.x_column] == x_cat][self.y_column].values[0]
                            fig.add_annotation(
                                x=x_cat,
                                y=total,
                                text=f"Total: {total:,.0f}",
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
                        title=self.title,
                        height=self.height,
                        showlegend=self.show_legend,
                        legend=dict(
                            title=self.color_column,
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        ),
                        barmode='stack',
                        bargap=0.2,
                        margin=dict(t=50, l=25, r=25, b=100),
                        xaxis=dict(
                            title=self.x_column,
                            tickangle=45,
                            categoryorder='array',
                            categoryarray=unique_x_values
                        ),
                        yaxis=dict(
                            title=self.y_column
                        ),
                        hoverlabel=dict(
                            bgcolor="rgba(255, 255, 255, 0.7)",
                            bordercolor="rgba(0, 0, 0, 0.1)",
                            font_size=12,
                            font_family="Arial",
                            namelength=-1
                        )
                    )
                    
                    # Render in Streamlit
                    st.plotly_chart(
                        fig,
                        use_container_width=use_container_width,
                        key=key
                    )
                    
                except Exception as e:
                    logger.error(f"Error rendering stacked bar chart: {e}")
                    st.error("Error rendering visualization")
        
        # Render using the new sorted chart class
        SortedStackedBarChart(
            data=chart_data,
            x_column='display_name',
            y_column='sum_price_agree_M',
            color_column=year_column,
            title=chart_title,
            height=500,
            show_legend=True
        ).render(key=f"chart_{selected_range}")
    else:
        st.info(f"No projects found in the {selected_range} range")