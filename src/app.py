import streamlit as st
from pymongo import MongoClient
import logging
from datetime import datetime
from special_functions.metrics import display_metrics_dashboard
from special_functions.filter_cache import get_filtered_data
from special_functions.department_cache import get_departments, get_sub_department, render_sidebar_filters
# from pages.price_cut import price_cut_vis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def connect_to_mongodb(mongo_uri):
    """Connect to MongoDB with detailed logging"""
    try:
        logger.info(f"Attempting to connect to MongoDB at {datetime.now()}")
        client = MongoClient(mongo_uri)
        
        # Test the connection
        client.admin.command('ping')
        logger.info("Successfully connected to MongoDB server")
        
        db = client["projects"]
        collection = db["projects"]
        
        # Log collection stats
        stats = db.command("collstats", "projects")
        logger.info(f"Connected to collection 'projects'. Documents count: {stats.get('count', 0)}")
        
        return collection
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        st.error(f"Error connecting to MongoDB: {str(e)}")
        return None
def load_page():
    st.title("Project Analysis Dashboard")
    
    # Initialize filters
    filters = {
        'dept_name': st.session_state.get('dept_name', ''),
        'dept_sub_name': st.session_state.get('dept_sub_name', ''),
        'date_start': st.session_state.get('date_start', datetime(2022, 1, 1).date()),
        'date_end': st.session_state.get('date_end', datetime(2023, 12, 31).date()),
        'price_start': st.session_state.get('price_start', 0.0),
        'price_end': st.session_state.get('price_end', 200.0)
    }
    
    filters = render_sidebar_filters()

    # Apply filters button
    if st.sidebar.button("Apply Filters"):
        with st.spinner("Fetching and analyzing data..."):
            df = get_filtered_data(filters)
            
            if df is not None and not df.empty:
                # Display metrics dashboard
                display_metrics_dashboard(df)
                
                # Display filtered data
                # st.subheader("Filtered Data")
                # st.dataframe(df)

if __name__ == "__main__":
    load_page()