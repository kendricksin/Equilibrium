# src/app.py

import streamlit as st
from dotenv import load_dotenv
import mysql.connector
import os
import random
import pandas as pd

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASS'),
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME')
}

def get_db_connection():
    """Create and return a database connection."""
    return mysql.connector.connect(**DB_CONFIG)

def get_random_data():
    """Fetch random rows and columns from the database"""
    try:
        # Create database connection
        conn = get_db_connection()
        
        # Get all column names from the projects table
        cursor = conn.cursor()
        cursor.execute("SHOW COLUMNS FROM projects")
        all_columns = [column[0] for column in cursor.fetchall()]
        
        # Randomly select 5 columns (always include project_id)
        available_columns = [col for col in all_columns if col != 'project_id']
        random_columns = random.sample(available_columns, 4)
        selected_columns = ['project_id'] + random_columns
        
        # Create the SQL query for random rows
        columns_str = ', '.join(selected_columns)
        query = f"""
        SELECT {columns_str}
        FROM projects
        ORDER BY RAND()
        LIMIT 10
        """
        
        # Execute query and get results
        df = pd.read_sql(query, conn)
        
        # Close connections
        cursor.close()
        conn.close()
        
        return df
        
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return None

def main():
    # Set up Streamlit page configuration
    st.set_page_config(page_title="Projects Database Viewer", page_icon="📊", layout="wide")

    # Page selection
    page = st.sidebar.selectbox("Choose a Page", ["Home", "Filters Analysis"])

    if page == "Home":
        # Title
        st.title("Projects Database Random Sample")
        st.write("Displaying 10 random rows with 5 random columns")
        
        # Container for refresh button and last refresh time
        col1, col2 = st.columns([1, 4])
        
        with col1:
            refresh = st.button("🔄 Refresh Data")
        
        # If refresh button is clicked or it's the first load
        if refresh or 'data' not in st.session_state:
            with st.spinner('Fetching random data...'):
                df = get_random_data()
                if df is not None:
                    st.session_state.data = df
        
        # Display data if available
        if 'data' in st.session_state:
            # Show the random selection info
            st.write("#### Selected Columns:")
            st.write(", ".join(st.session_state.data.columns.tolist()))
            
            # Display the data with formatting
            st.dataframe(
                st.session_state.data,
                use_container_width=True,
                hide_index=True
            )
            
            # Display basic statistics
            st.write("#### Basic Statistics")
            numeric_cols = st.session_state.data.select_dtypes(include=['float64', 'int64']).columns
            if len(numeric_cols) > 0:
                st.dataframe(
                    st.session_state.data[numeric_cols].describe(),
                    use_container_width=True
                )
        else:
            st.warning("No data available. Please check your database connection.")
    
    elif page == "Filters Analysis":
        # Import and load the filters page
        from pages import filters
        filters.load_page(get_db_connection)

if __name__ == "__main__":
    main()
