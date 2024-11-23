import streamlit as st
import pandas as pd
from datetime import datetime
from bson.codec_options import CodecOptions

def initialize_filters():
    """Initialize default filters if they don't exist in session state"""
    if 'filters' not in st.session_state:
        st.session_state.filters = {
            'dept_name': '',
            'date_start': datetime(2022, 1, 1),
            'date_end': datetime(2023, 12, 31),
            'price_ranges': []
        }
    return st.session_state.filters

def get_unique_departments(db, collection_name="projects"):
    """Fetch unique department names from MongoDB."""
    try:
        if db is None:
            st.error("Database connection is not available")
            return []
        return sorted(db[collection_name].distinct("dept_name"))
    except Exception as e:
        st.error(f"Error fetching departments: {str(e)}")
        return []

def get_filtered_data(db, filters, collection_name="projects"):
    """Fetch filtered data from MongoDB."""
    try:
        if db is None:
            st.error("Database connection is not available")
            return None

        query = {}

        # Add department filter if selected
        if filters.get('dept_name'):
            query['dept_name'] = filters['dept_name']

        # Add date range filter if dates are selected
        if filters.get('date_start') and filters.get('date_end'):
            start_date = datetime.combine(filters['date_start'], datetime.min.time())
            end_date = datetime.combine(filters['date_end'], datetime.max.time())
            query['transaction_date'] = {
                "$gte": start_date,
                "$lte": end_date
            }

        # Add price range filters
        if filters.get('price_ranges'):
            price_conditions = []
            for price_range in filters['price_ranges']:
                if price_range == '>500':
                    price_conditions.append({"price": {"$gt": 500}})
                elif '-' in price_range:
                    low, high = map(float, price_range.split('-'))
                    price_conditions.append({"price": {"$gte": low, "$lte": high}})
            if price_conditions:
                query["$or"] = price_conditions

        # Set timezone-aware options
        collection = db[collection_name].with_options(
            codec_options=CodecOptions(tz_aware=True)
        )

        # Execute query with progress indicator
        with st.spinner("Fetching data..."):
            data = list(collection.find(query))
            if not data:
                st.warning("No data found for the selected filters.")
                return None

            df = pd.DataFrame(data)
            if '_id' in df.columns:
                df['_id'] = df['_id'].astype(str)
            return df

    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return None

def calculate_metrics(df):
    """Calculate metrics from the filtered DataFrame."""
    if df is None or df.empty:
        return {
            "total_projects": 0,
            "unique_winners": 0,
            "total_value": 0,
            "avg_project_value": 0,
            "avg_price_cut": 0
        }

    return {
        "total_projects": len(df),
        "unique_winners": df['winner'].nunique() if 'winner' in df.columns else 0,
        "total_value": df['price'].sum() if 'price' in df.columns else 0,
        "avg_project_value": df['price'].mean() if 'price' in df.columns else 0,
        "avg_price_cut": df['price_cut'].mean() if 'price_cut' in df.columns else 0,
    }

def load_page(get_db_connection):
    st.title("Project Analysis Dashboard")
    
    # Initialize filters and session state
    filters = initialize_filters()
    
    if 'show_confirm_buttons' not in st.session_state:
        st.session_state.show_confirm_buttons = False
    if 'execute_query' not in st.session_state:
        st.session_state.execute_query = False

    # Get database connection
    db = get_db_connection()
    if db is None:
        st.error("Unable to connect to database. Please check your connection settings.")
        return

    # Fetch unique departments
    unique_depts = get_unique_departments(db)
    
    # Sidebar filters
    with st.sidebar:
        st.header("Filters")
        
        # Department filter
        dept_options = [""] + unique_depts
        dept_index = dept_options.index(filters['dept_name']) if filters['dept_name'] in dept_options else 0
        dept_name = st.selectbox(
            "Department",
            options=dept_options,
            index=dept_index
        )
        
        # Date filters
        date_start = st.date_input(
            "Start Date", 
            value=filters['date_start']
        )
        date_end = st.date_input(
            "End Date", 
            value=filters['date_end']
        )
        
        # Price range filter
        price_ranges = ['0-10', '10-50', '50-100', '100-200', '200-500', '>500']
        selected_price_ranges = st.multiselect(
            "Price Range (Million Baht)",
            options=price_ranges,
            default=filters['price_ranges']
        )

        # Apply filters button
        if st.button("Apply Filters"):
            st.session_state.filters.update({
                'dept_name': dept_name,
                'date_start': date_start,
                'date_end': date_end,
                'price_ranges': selected_price_ranges
            })
            st.session_state.show_confirm_buttons = True
            st.session_state.execute_query = True

    # Display data and metrics
    if st.session_state.execute_query:
        df = get_filtered_data(db, st.session_state.filters)
        
        if df is not None and not df.empty:
            metrics = calculate_metrics(df)
            
            st.write("### Key Metrics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Projects", f"{metrics['total_projects']}")
                st.metric("Unique Winners", f"{metrics['unique_winners']}")
            with col2:
                st.metric("Total Value (MB)", f"{metrics['total_value']:.2f}")
                st.metric("Average Project Value (MB)", f"{metrics['avg_project_value']:.2f}")
            with col3:
                st.metric("Average Price Cut (%)", f"{metrics['avg_price_cut']:.2f}%")
            
            st.write("### Filtered Data")
            st.dataframe(df)

    # Reset filters button
    if st.session_state.show_confirm_buttons:
        if st.button("Reset Filters"):
            st.session_state.clear()
            st.experimental_rerun()