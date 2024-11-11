# src/app.py

import streamlit as st
from dotenv import load_dotenv
import mysql.connector
import os

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

def main():
    # Set up Streamlit page configuration
    st.set_page_config(page_title="Projects Database Viewer", page_icon="📊", layout="wide")

    # Page selection
    page = st.sidebar.selectbox("Choose a Page", ["Home", "Filters Analysis"])

    if page == "Home":
        st.title("Projects Database Viewer")
        st.write("Welcome to the Projects Database Viewer app. Use the sidebar to navigate to different pages.")
    elif page == "Filters Analysis":
        # Import and load the filters page
        from pages import filters
        filters.load_page(get_db_connection)

if __name__ == "__main__":
    main()
