import streamlit as st
from pymongo import MongoClient
import logging
from datetime import datetime
from special_functions.metrics import display_metrics_dashboard
from special_functions.filter_cache import get_filtered_data
from special_functions.department_cache import get_departments, get_sub_department
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
        'dept_name': '',
        'dept_sub_name': '',
        'date_start': datetime(2022, 1, 1).date(),
        'date_end': datetime(2023, 12, 31).date(),
        'price_start': None,
        'price_end': None
    }
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    unique_depts = get_departments()
    logger.info(f"Found {len(unique_depts)} unique departments")

    # Department filter
    dept_options = [""] + unique_depts
    filters['dept_name'] = st.sidebar.selectbox(
        "Department",
        options=dept_options
    )

    # Sub-department filter
    if filters['dept_name']:
        unique_sub_depts = get_sub_department(filters['dept_name'])
        logger.info(f"Found {len(unique_sub_depts)} sub-departments")
        
        sub_dept_options = [""] + unique_sub_depts
        filters['dept_sub_name'] = st.sidebar.selectbox(
            "Sub-Department",
            options=sub_dept_options
        )
            
        # Date filters
        filters['date_start'] = st.sidebar.date_input("Start Date", value=filters['date_start'])
        filters['date_end'] = st.sidebar.date_input("End Date", value=filters['date_end'])
        
        # Price range filter with numeric inputs and default values
        st.sidebar.subheader("Price Range (Million Baht)")
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            filters['price_start'] = st.number_input(
                "From", 
                min_value=0.0,
                max_value=10000.0,
                value=0.0,  # Default start value
                step=10.0,
                format="%.1f"
            )
                
        with col2:
            filters['price_end'] = st.number_input(
                "To",
                min_value=0.0,
                max_value=20000.0,
                value=200.0,  # Default end value
                step=10.0,
                format="%.1f"
            )
                
        # Validate price range
        if filters['price_start'] > filters['price_end']:
            st.sidebar.error("Start price should be less than end price")
            return


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
            else:
                st.warning("No data available for the selected filters")

if __name__ == "__main__":
    load_page()