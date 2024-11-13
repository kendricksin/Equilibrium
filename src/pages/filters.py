# src/pages/filters.py

import streamlit as st
import pandas as pd
from datetime import datetime

def get_row_count(conn, filters):
    """Get the count of rows that match the filter criteria."""
    try:
        conditions = []
        params = []

        if filters['dept_name']:
            conditions.append("dept_name = %s")
            params.append(filters['dept_name'])

        conditions.append("transaction_date BETWEEN %s AND %s")
        params.extend([filters['date_start'], filters['date_end']])

        price_conditions = []
        for price_range in filters['price_ranges']:
            if price_range == '>500':
                price_conditions.append("sum_price_agree > %s")
                params.append(500 * 1e6)
            else:
                min_price, max_price = map(float, price_range.replace('>','').split('-'))
                price_conditions.append("(sum_price_agree BETWEEN %s AND %s)")
                params.extend([min_price * 1e6, max_price * 1e6])

        if price_conditions:
            conditions.append(f"({' OR '.join(price_conditions)})")

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT COUNT(*) as count FROM projects WHERE {where_clause}"
        
        df = pd.read_sql(query, conn, params=params)
        return df['count'].iloc[0]

    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return None

def get_filtered_data(conn, filters):
    """Get data based on selected filters."""
    try:
        conditions = []
        params = []

        if filters['dept_name']:
            conditions.append("dept_name = %s")
            params.append(filters['dept_name'])

        conditions.append("transaction_date BETWEEN %s AND %s")
        params.extend([filters['date_start'], filters['date_end']])

        price_conditions = []
        for price_range in filters['price_ranges']:
            if price_range == '>500':
                price_conditions.append("sum_price_agree > %s")
                params.append(500 * 1e6)
            else:
                min_price, max_price = map(float, price_range.replace('>','').split('-'))
                price_conditions.append("(sum_price_agree BETWEEN %s AND %s)")
                params.extend([min_price * 1e6, max_price * 1e6])

        if price_conditions:
            conditions.append(f"({' OR '.join(price_conditions)})")

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
    
    # Price range multi-select
    price_ranges = ['0-10', '10-50', '50-100', '100-200', '200-500', '>500']
    selected_price_ranges = st.sidebar.multiselect(
        "Price Range (Million Baht)",
        options=price_ranges,
        default=[]
    )

    filters = {
        'dept_name': dept_name,
        'date_start': date_start,
        'date_end': date_end,
        'price_ranges': selected_price_ranges
    }

    # Apply filters and fetch data
    if st.sidebar.button("Apply Filters"):
        with st.spinner("Checking row count..."):
            conn = get_db_connection()
            row_count = get_row_count(conn, filters)
            
            if row_count is None:
                st.error("Error checking row count")
                return
            
            st.write(f"Number of matching rows: {row_count}")
            
            if row_count == 0:
                st.warning("No data found for the selected filters.")
                conn.close()
                return
            
            if row_count > 1000:
                proceed = st.button("Proceed with large query?", 
                                  help=f"This query will return {row_count} rows. Click to proceed or adjust filters to reduce the result set.")
                reset = st.button("Reset Filters")
                
                if reset:
                    st.experimental_rerun()
                if not proceed:
                    conn.close()
                    return
            
            # Proceed with main query if row count <= 1000 or user confirmed
            with st.spinner("Fetching data..."):
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
                    
                    # Display filtered data
                    st.write("### Filtered Data")
                    st.dataframe(df)
