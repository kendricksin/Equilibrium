import streamlit as st
from pymongo import MongoClient
import logging
from datetime import datetime

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

def get_filtered_data(collection, filters):
    """Fetch filtered data with logging"""
    try:
        logger.info(f"Attempting to fetch data with filters: {filters}")
        
        query = {}
        
        # Add department filter if selected
        if filters.get('dept_name'):
            query['dept_name'] = filters['dept_name']
            logger.info(f"Added department filter: {filters['dept_name']}")

        # Add date range filter if dates are selected
        if filters.get('date_start') and filters.get('date_end'):
            start_date = datetime.combine(filters['date_start'], datetime.min.time())
            end_date = datetime.combine(filters['date_end'], datetime.max.time())
            query['transaction_date'] = {
                "$gte": start_date,
                "$lte": end_date
            }
            logger.info(f"Added date range filter: {start_date} to {end_date}")

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
            logger.info(f"Added price range filters: {filters['price_ranges']}")

        logger.info(f"Final query: {query}")
        
        # Execute query
        cursor = collection.find(query)
        data = list(cursor)
        logger.info(f"Query returned {len(data)} documents")
        
        if not data:
            logger.warning("No data found for the given filters")
            st.warning("No data found for the selected filters.")
            return None
            
        # Sample first document for debugging
        if data:
            logger.info(f"Sample document fields: {list(data[0].keys())}")
            
        return data
        
    except Exception as e:
        logger.error(f"Error fetching data: {str(e)}")
        st.error(f"Error fetching data: {str(e)}")
        return None

def load_page():
    st.title("Project Analysis Dashboard")
    
    # Connect to MongoDB
    mongo_uri = "mongodb://localhost:27017/"  # Replace with your MongoDB URI
    collection = connect_to_mongodb(mongo_uri)
    
    if collection is None:
        st.error("Failed to connect to database. Check the logs for details.")
        return
        
    # Initialize filters
    filters = {
        'dept_name': '',
        'date_start': datetime(2022, 1, 1),
        'date_end': datetime(2023, 12, 31),
        'price_ranges': []
    }
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    try:
        # Get unique departments
        logger.info("Fetching unique departments")
        unique_depts = sorted(collection.distinct("dept_name"))
        logger.info(f"Found {len(unique_depts)} unique departments")
        
        # Department filter
        dept_options = [""] + unique_depts
        filters['dept_name'] = st.sidebar.selectbox(
            "Department",
            options=dept_options
        )
        
        # Date filters
        filters['date_start'] = st.sidebar.date_input("Start Date", value=filters['date_start'])
        filters['date_end'] = st.sidebar.date_input("End Date", value=filters['date_end'])
        
        # Price range filter
        price_ranges = ['0-10', '10-50', '50-100', '100-200', '200-500', '>500']
        filters['price_ranges'] = st.sidebar.multiselect(
            "Price Range (Million Baht)",
            options=price_ranges
        )
        
    except Exception as e:
        logger.error(f"Error setting up filters: {str(e)}")
        st.error(f"Error setting up filters: {str(e)}")
        return

    # Apply filters button
    if st.sidebar.button("Apply Filters"):
        logger.info("Apply Filters button clicked")
        with st.spinner("Fetching data..."):
            data = get_filtered_data(collection, filters)
            
            if data:
                # Display data (add your visualization code here)
                st.write("### Filtered Data")
                st.write(f"Found {len(data)} records")
                st.dataframe(data)
            else:
                logger.warning("No data to display")
                st.warning("No data available for the selected filters")

if __name__ == "__main__":
    load_page()