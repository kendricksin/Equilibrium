# src/pages/DepartmentMagicQuadrant.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from services.database.mongodb import MongoDBService
import logging

logger = logging.getLogger(__name__)

def get_project_size_ranges() -> Dict[str, Tuple[float, float]]:
    """Define project size ranges in millions of baht"""
    return {
        "Small (10-50M฿)": (10, 50),
        "Medium (50-100M฿)": (50, 100),
        "Large (100-300M฿)": (100, 300),
        "Extra Large (>300M฿)": (300, float('inf')),
        "Custom Range": None
    }

def calculate_department_metrics(
    min_value: float,
    max_value: float,
    min_projects: int,
    max_projects: Optional[int] = None
) -> pd.DataFrame:
    """Calculate department-level metrics using MongoDB aggregation"""
    try:
        mongo = MongoDBService()
        collection = mongo.get_collection("projects")
        
        # Convert to base unit (baht from millions)
        min_value_baht = min_value * 1e6
        max_value_baht = max_value * 1e6
        
        pipeline = [
            # Match only valid documents within price range
            {
                "$match": {
                    "dept_name": {"$exists": True, "$ne": ""},
                    "winner": {"$exists": True, "$ne": ""},
                    "sum_price_agree": {
                        "$exists": True,
                        "$ne": None,
                        "$gte": min_value_baht,
                        "$lte": max_value_baht
                    },
                    "price_build": {
                        "$exists": True,
                        "$ne": None,
                        "$gt": 0
                    }
                }
            },
            # Calculate price cut and filter outliers
            {
                "$addFields": {
                    "price_cut_pct": {
                        "$multiply": [
                            {"$subtract": [
                                {"$divide": ["$sum_price_agree", "$price_build"]},
                                1
                            ]},
                            100
                        ]
                    }
                }
            },
            # Filter out invalid price cuts (positive or extreme negative)
            {
                "$match": {
                    "price_cut_pct": {
                        "$lt": 0,  # Only negative price cuts
                        "$gt": -50  # Filter extreme outliers
                    }
                }
            },
            # Group by department and company
            {
                "$group": {
                    "_id": {
                        "dept": "$dept_name",
                        "company": "$winner"
                    },
                    "company_value": {"$sum": "$sum_price_agree"},
                    "total_projects": {"$sum": 1},
                    "price_cut_sum": {"$sum": "$price_cut_pct"}
                }
            },
            # Group by department
            {
                "$group": {
                    "_id": "$_id.dept",
                    "total_value": {"$sum": "$company_value"},
                    "total_projects": {"$sum": "$total_projects"},
                    "avg_price_cut": {"$avg": "$price_cut_sum"},
                    "company_values": {
                        "$push": {
                            "company": "$_id.company",
                            "value": "$company_value"
                        }
                    },
                    "unique_companies": {"$sum": 1}
                }
            },
            # Filter departments by project count
            {
                "$match": {
                    "$and": [
                        {"total_projects": {"$gte": min_projects}},
                        {"total_projects": {"$lte": max_projects}} if max_projects else {"total_projects": {"$gte": 0}}
                    ]
                }
            },
            # Calculate HHI
            {
                "$project": {
                    "department": "$_id",
                    "total_value": 1,
                    "total_projects": 1,
                    "avg_price_cut": 1,
                    "unique_companies": 1,
                    "hhi": {
                        "$reduce": {
                            "input": "$company_values",
                            "initialValue": 0,
                            "in": {
                                "$add": [
                                    "$$value",
                                    {
                                        "$pow": [
                                            {
                                                "$multiply": [
                                                    {"$divide": ["$$this.value", "$total_value"]},
                                                    100
                                                ]
                                            },
                                            2
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        ]
        
        results = list(collection.aggregate(pipeline))
        if not results:
            return pd.DataFrame()
            
        df = pd.DataFrame(results)
        
        # Calculate competition metrics
        df['avg_value_per_project'] = df['total_value'] / df['total_projects']
        df['projects_per_company'] = df['total_projects'] / df['unique_companies']
        
        # Calculate quadrant labels
        df['quadrant'] = df.apply(
            lambda x: determine_quadrant(x['hhi'], x['avg_price_cut']),
            axis=1
        )
        
        return df
        
    except Exception as e:
        logger.error(f"Error calculating department metrics: {e}")
        raise

def determine_quadrant(hhi: float, price_cut: float) -> str:
    """Determine which quadrant a department belongs to"""
    # HHI thresholds: <1500 is competitive, >2500 is concentrated
    # Price cut thresholds: <-5% is competitive, >-2% is less competitive
    
    if hhi <= 1500:
        if price_cut < -5:
            return "High Competition"
        else:
            return "Price Sensitive"
    else:
        if price_cut < -5:
            return "Selective Competition"
        else:
            return "Limited Competition"

def create_magic_quadrant(df: pd.DataFrame) -> go.Figure:
    """Create magic quadrant visualization"""
    # Calculate medians for quadrant lines
    hhi_median = df['hhi'].median()
    price_cut_median = df['avg_price_cut'].median()
    
    # Create scatter plot
    fig = go.Figure()
    
    # Add quadrant lines
    fig.add_hline(y=price_cut_median, line_dash="dash", line_color="gray")
    fig.add_vline(x=hhi_median, line_dash="dash", line_color="gray")
    
    # Color mapping for quadrants
    colors = {
        "High Competition": "green",
        "Price Sensitive": "blue",
        "Selective Competition": "orange",
        "Limited Competition": "red"
    }
    
    # Add scatter points
    for quadrant in colors:
        mask = df['quadrant'] == quadrant
        fig.add_trace(go.Scatter(
            x=df[mask]['hhi'],
            y=df[mask]['avg_price_cut'],
            mode='markers+text',
            name=quadrant,
            text=df[mask]['department'],
            textposition="top center",
            marker=dict(
                size=df[mask]['total_projects'] / df['total_projects'].max() * 80,  # Increased max size
                color=colors[quadrant],
                opacity=0.7,
                line=dict(width=1, color='white')  # Add white border for better visibility
            ),
            hovertemplate=(
                "<b>%{text}</b><br>" +
                "HHI: %{x:.0f}<br>" +
                "Price Cut: %{y:.1f}%<br>" +
                "Projects: %{marker.size:.0f}<br>" +
                "<extra></extra>"
            )
        ))
    
    # Update layout
    fig.update_layout(
        title="Department Magic Quadrant",
        xaxis_title="Market Concentration (HHI)",
        yaxis_title="Average Price Cut (%)",
        height=800,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99
        ),
        # Add quadrant labels
        annotations=[
            dict(
                x=hhi_median/2, y=price_cut_median/2,
                text="High Competition",
                showarrow=False,
                font=dict(size=14, color="green")
            ),
            dict(
                x=hhi_median*1.5, y=price_cut_median/2,
                text="Selective Competition",
                showarrow=False,
                font=dict(size=14, color="orange")
            ),
            dict(
                x=hhi_median/2, y=price_cut_median*1.5,
                text="Price Sensitive",
                showarrow=False,
                font=dict(size=14, color="blue")
            ),
            dict(
                x=hhi_median*1.5, y=price_cut_median*1.5,
                text="Limited Competition",
                showarrow=False,
                font=dict(size=14, color="red")
            )
        ]
    )
    
    return fig

def main():
    """Main function for the Magic Quadrant page"""
    st.set_page_config(layout="wide")
    
    st.title("🎯 Department Magic Quadrant Analysis")
    
    # Project size selection
    st.markdown("### 📊 Analysis Parameters")
    
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.markdown("##### Project Size Filter")
        # Project size range selection
        ranges = get_project_size_ranges()
        selected_range = st.selectbox(
            "Project Size Range",
            options=list(ranges.keys()),
            index=2  # Default to Large projects
        )
        
        if selected_range == "Custom Range":
            min_value = st.number_input(
                "Minimum Value (M฿)",
                value=100.0,
                min_value=0.0
            )
            max_value = st.number_input(
                "Maximum Value (M฿)",
                value=300.0,
                min_value=min_value
            )
        else:
            min_value, max_value = ranges[selected_range]
            
        st.markdown("##### Department Size Filter")
        # Get project count range for the selected value range
        with st.spinner("Calculating project count range..."):
            mongo = MongoDBService()
            collection = mongo.get_collection("projects")
            
            # Query to get project counts per department for the selected value range
            pipeline = [
                {
                    "$match": {
                        "sum_price_agree": {
                            "$gte": min_value * 1e6,
                            "$lte": max_value * 1e6 if max_value != float('inf') else None
                        }
                    }
                },
                {
                    "$group": {
                        "_id": "$dept_name",
                        "count": {"$sum": 1}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "min": {"$min": "$count"},
                        "max": {"$max": "$count"},
                        "counts": {"$push": "$count"}
                    }
                }
            ]
            
            result = list(collection.aggregate(pipeline))
            if result:
                min_count = result[0]['min']
                max_count = result[0]['max']
                p25 = int(np.percentile(result[0]['counts'], 25))
                p75 = int(np.percentile(result[0]['counts'], 75))
            else:
                min_count, max_count = 0, 100
                p25, p75 = 25, 75
        
        # Project count range slider
        min_projects, max_projects = st.slider(
            "Project Count Range",
            min_value=min_count,
            max_value=max_count,
            value=(p25, p75),  # Default to interquartile range
            help="Filter departments by their number of projects"
        )
    
    with col2:
        st.markdown("""
        This analysis plots departments based on two key metrics:
        - **Market Concentration (HHI)**: Measures how concentrated the market is among companies
            - Lower values (<1500) indicate more competition
            - Higher values (>2500) indicate market concentration
        - **Price Cut**: Average percentage reduction from budget to final price
            - Lower (more negative) values indicate more competitive pricing
            - Higher values indicate less price competition
        
        *Note: Only includes departments with at least 5 projects in the selected size range.*
        """)
    
    try:
        # Calculate metrics
        with st.spinner("Calculating department metrics..."):
            df = calculate_department_metrics(min_value, max_value, min_projects, max_projects)
        
        if df.empty:
            st.error("No data available for the selected project size range")
            return
        
        # Create visualization
        fig = create_magic_quadrant(df)
        st.plotly_chart(fig, use_container_width=True)
        
        # Add metrics table
        st.markdown("### Department Metrics")
        
        # Format DataFrame for display
        display_df = df[[
            'department', 'quadrant', 'total_projects', 'unique_companies',
            'total_value', 'avg_value_per_project', 'hhi', 'avg_price_cut',
            'projects_per_company'
        ]].copy()
        
        # Convert values to millions
        display_df['total_value'] = display_df['total_value'] / 1e6
        display_df['avg_value_per_project'] = display_df['avg_value_per_project'] / 1e6
        
        st.dataframe(
            display_df,
            column_config={
                "department": "Department",
                "quadrant": "Quadrant",
                "total_projects": st.column_config.NumberColumn(
                    "Total Projects",
                    format="%d"
                ),
                "unique_companies": st.column_config.NumberColumn(
                    "Unique Companies",
                    format="%d"
                ),
                "total_value": st.column_config.NumberColumn(
                    "Total Value (M฿)",
                    format="%.2f"
                ),
                "avg_value_per_project": st.column_config.NumberColumn(
                    "Avg Project Value (M฿)",
                    format="%.2f"
                ),
                "hhi": st.column_config.NumberColumn(
                    "HHI",
                    format="%.0f",
                    help="Herfindahl-Hirschman Index - measures market concentration"
                ),
                "avg_price_cut": st.column_config.NumberColumn(
                    "Avg Price Cut (%)",
                    format="%.2f"
                ),
                "projects_per_company": st.column_config.NumberColumn(
                    "Projects per Company",
                    format="%.1f"
                )
            },
            hide_index=True
        )
        
        # Add download button
        csv = display_df.to_csv(index=False)
        st.download_button(
            "📥 Download Analysis Data",
            csv,
            "department_magic_quadrant.csv",
            "text/csv",
            key="download-dept-analysis"
        )
        
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()