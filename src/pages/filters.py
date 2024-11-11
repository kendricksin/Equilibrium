# src/pages/filters.py

import streamlit as st
import pandas as pd
from datetime import datetime

def get_filtered_data(conn, filters):
    """Get data based on selected filters."""
    try:
        # Build the WHERE clause based on filters
        conditions = []
        params = []

        if filters['dept_name']:
            conditions.append("dept_name = %s")
            params.append(filters['dept_name'])

        conditions.append("transaction_date BETWEEN %s AND %s")
        params.extend([filters['date_start'], filters['date_end']])

        conditions.append("sum_price_agree BETWEEN %s AND %s")
        params.extend([filters['min_price'] * 1e6, filters['max_price'] * 1e6])

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"SELECT * FROM projects WHERE {where_clause}"
        
        df = pd.read_sql(query, conn, params=params)
        return df

    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return None

def calculate_metrics(df):
    """Calculate key metrics from the filtered dataset."""
    metrics = {
        'total_projects': len(df),
        'unique_winners': df['winner'].nunique(),
        'total_value': df['sum_price_agree'].sum() / 1e6,  # Convert to millions
        'avg_project_value': (df['sum_price_agree'].mean() / 1e6) if len(df) > 0 else 0,
        # 'avg_price_cut': df['price_cut'].mean() if len(df) > 0 else 0,
    }
    return metrics

def load_page(get_db_connection):
    """Load the Filters Analysis Page."""
    st.title("Project Analysis Dashboard")

    # Sidebar filters
    st.sidebar.header("Filters")
    dept_name = st.sidebar.text_input("Department")
    date_start = st.sidebar.date_input("Start Date", datetime(2019, 1, 1))
    date_end = st.sidebar.date_input("End Date", datetime(2024, 12, 31))
    price_range = st.sidebar.slider("Price Range (Million Baht)", 0, 2000, (0, 2000))

    filters = {
        'dept_name': dept_name,
        'date_start': date_start,
        'date_end': date_end,
        'min_price': price_range[0],
        'max_price': price_range[1]
    }

    # Apply filters and fetch data
    if st.sidebar.button("Apply Filters"):
        with st.spinner("Fetching data..."):
            conn = get_db_connection()
            df = get_filtered_data(conn, filters)
            conn.close()

            if df is not None and not df.empty:
                # Calculate and display metrics
                metrics = calculate_metrics(df)
                st.write("### Key Metrics")
                col1, col2 = st.columns(2)
                
                col1.metric("Total Projects", f"{metrics['total_projects']}")
                col1.metric("Unique Winners", f"{metrics['unique_winners']}")
                col2.metric("Total Value (MB)", f"{metrics['total_value']:.2f}")
                col2.metric("Average Project Value (MB)", f"{metrics['avg_project_value']:.2f}")
                # st.metric("Average Price Cut %", f"{metrics['avg_price_cut']:.2%}")
                
                # Display filtered data
                st.write("### Filtered Data")
                st.dataframe(df)
            else:
                st.warning("No data found for the selected filters.")
