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

    # Initialize filters state
    if 'filters' not in st.session_state:
        st.session_state.filters = {
            'dept_name': '',
            'date_start': None,
            'date_end': None,
            'price_ranges': []
        }

    # Page selection
    page = st.sidebar.selectbox("Choose a Page", ["Filters Analysis", "Dashboards"])

    if page == "Filters Analysis":
        # Import and load the filters page
        from pages import filters
        filters.load_page(get_db_connection, st.session_state.filters)
    elif page == "Dashboards":
        # Load the dashboards page
        from pages import dashboard1
        dashboard1.load_dashboards(get_db_connection, st.session_state.filters)

if __name__ == "__main__":
    main()
