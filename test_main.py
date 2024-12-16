import os
import pymongo
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime

def create_aggregation_collection(db):
    """Create and populate the department distribution aggregation collection"""
    # Drop existing collection if it exists
    if "department_distribution" in db.list_collection_names():
        db.department_distribution.drop()
    
    pipeline = [
        # Department aggregation
        {
            "$group": {
                "_id": {
                    "dept": "$dept_name",
                    "subdept": "$dept_sub_name"
                },
                "count": {"$sum": 1},
                "total_value": {"$sum": "$price_build"}  # Changed to price_build
            }
        },
        # Calculate totals and store results
        {
            "$merge": {
                "into": "department_distribution",
                "whenMatched": "replace",
                "whenNotMatched": "insert"
            }
        }
    ]
    
    # Run the aggregation
    db.projects.aggregate(pipeline)
    
    # Add metadata
    total_docs = db.projects.count_documents({})
    total_value = db.projects.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$price_build"}}}  # Changed to price_build
    ]).next()["total"]
    
    db.department_distribution.insert_one({
        "_id": "metadata",
        "last_updated": datetime.utcnow(),
        "total_projects": total_docs,
        "total_value": total_value
    })
    
    return True
def get_department_distribution(collection):
    """Get department distribution from the aggregation collection"""
    # Get metadata
    metadata = collection.find_one({"_id": "metadata"})
    total_docs = metadata["total_projects"]
    total_value = metadata["total_value"]
    
    # Get department distribution
    dept_pipeline = [
        {
            "$match": {
                "_id": {"$ne": "metadata"}
            }
        },
        {
            "$group": {
                "_id": "$_id.dept",
                "count": {"$sum": "$count"},
                "value": {"$sum": "$total_value"}
            }
        },
        {
            "$project": {
                "department": "$_id",
                "count": 1,
                "count_percentage": {
                    "$multiply": [{"$divide": ["$count", total_docs]}, 100]
                },
                "value": 1,
                "value_percentage": {
                    "$multiply": [{"$divide": ["$value", total_value]}, 100]
                }
            }
        },
        {"$sort": {"count": -1}}
    ]
    
    all_depts = list(collection.aggregate(dept_pipeline))
    
    # Split into top 10 and others for both metrics
    dept_results = all_depts[:10]
    if len(all_depts) > 10:
        others_count = sum(d["count"] for d in all_depts[10:])
        others_value = sum(d["value"] for d in all_depts[10:])
        dept_results.append({
            "department": "Others",
            "count": others_count,
            "count_percentage": (others_count / total_docs) * 100,
            "value": others_value,
            "value_percentage": (others_value / total_value) * 100
        })
    
    # Get sub-department distribution
    subdept_pipeline = [
        {
            "$match": {
                "_id": {"$ne": "metadata"}
            }
        },
        {
            "$group": {
                "_id": "$_id.subdept",
                "count": {"$sum": "$count"},
                "value": {"$sum": "$total_value"}
            }
        },
        {
            "$project": {
                "subdepartment": "$_id",
                "count": 1,
                "count_percentage": {
                    "$multiply": [{"$divide": ["$count", total_docs]}, 100]
                },
                "value": 1,
                "value_percentage": {
                    "$multiply": [{"$divide": ["$value", total_value]}, 100]
                }
            }
        },
        {"$sort": {"count": -1}}
    ]
    
    all_subdepts = list(collection.aggregate(subdept_pipeline))
    
    # Split into top 10 and others for both metrics
    subdept_results = all_subdepts[:10]
    if len(all_subdepts) > 10:
        others_count = sum(d["count"] for d in all_subdepts[10:])
        others_value = sum(d["value"] for d in all_subdepts[10:])
        subdept_results.append({
            "subdepartment": "Others",
            "count": others_count,
            "count_percentage": (others_count / total_docs) * 100,
            "value": others_value,
            "value_percentage": (others_value / total_value) * 100
        })
    
    return {
        "departments": dept_results,
        "subdepartments": subdept_results,
        "total_projects": total_docs,
        "total_value": total_value,
        "last_updated": metadata["last_updated"]
    }

def create_distribution_charts(data):
    """Create pie charts for count and value distributions"""
    # Process department data
    dept_labels = [d["department"] for d in data["departments"]]
    dept_counts = [d["count_percentage"] for d in data["departments"]]
    dept_values = [d["value_percentage"] for d in data["departments"]]
    
    # Process sub-department data
    subdept_labels = [d["subdepartment"] for d in data["subdepartments"]]
    subdept_counts = [d["count_percentage"] for d in data["subdepartments"]]
    subdept_values = [d["value_percentage"] for d in data["subdepartments"]]
    
    # Create figure with 2x2 subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Departments by Project Count',
            'Sub-departments by Project Count',
            'Departments by Project Value',
            'Sub-departments by Project Value'
        ),
        specs=[[{'type': 'pie'}, {'type': 'pie'}],
               [{'type': 'pie'}, {'type': 'pie'}]]
    )
    
    # Add department count pie chart
    fig.add_trace(
        go.Pie(
            labels=dept_labels,
            values=dept_counts,
            textinfo='label+percent',
            textposition='inside',
            name="Dept Count"
        ),
        row=1, col=1
    )
    
    # Add sub-department count pie chart
    fig.add_trace(
        go.Pie(
            labels=subdept_labels,
            values=subdept_counts,
            textinfo='label+percent',
            textposition='inside',
            name="Subdept Count"
        ),
        row=1, col=2
    )
    
    # Add department value pie chart
    fig.add_trace(
        go.Pie(
            labels=dept_labels,
            values=dept_values,
            textinfo='label+percent',
            textposition='inside',
            name="Dept Value"
        ),
        row=2, col=1
    )
    
    # Add sub-department value pie chart
    fig.add_trace(
        go.Pie(
            labels=subdept_labels,
            values=subdept_values,
            textinfo='label+percent',
            textposition='inside',
            name="Subdept Value"
        ),
        row=2, col=2
    )
    
    # Update layout
    fig.update_layout(
        height=800,
        showlegend=False,
        title={
            'text': 'Project Distribution by Count and Value',
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        }
    )
    
    return fig

def main():
    st.set_page_config(layout="wide", page_title="Project Distribution")
    st.title("Project Distribution Test")
    
    try:
        # Connect to MongoDB
        client = pymongo.MongoClient(os.getenv("MONGO_URI"))
        db = client[os.getenv("MONGO_DB")]
        
        # Force refresh on first run to ensure we have the new schema
        refresh_data = True
        st.info("Forcing refresh to update aggregation schema...")
        
        if refresh_data:
            with st.spinner("Aggregating department distribution..."):
                # Debug logging
                st.write("Dropping existing collection...")
                if "department_distribution" in db.list_collection_names():
                    db.department_distribution.drop()
                
                st.write("Creating new aggregation...")
                create_aggregation_collection(db)
                
                # Verify metadata
                metadata = db.department_distribution.find_one({"_id": "metadata"})
                st.write("New metadata:", metadata)
        
        # Get aggregated data
        with st.spinner("Fetching distribution data..."):
            distribution_data = get_department_distribution(db.department_distribution)
            
        # Display metrics
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.markdown(f"Total Projects: **{distribution_data['total_projects']:,}**")
        with col2:
            st.markdown(f"Total Value: **฿{distribution_data['total_value']/1e6:,.2f}M**")
        with col3:
            st.markdown(f"Last Updated: **{distribution_data['last_updated'].strftime('%Y-%m-%d %H:%M UTC')}**")
        
        # Create and display charts
        fig = create_distribution_charts(distribution_data)
        st.plotly_chart(fig, use_container_width=True)
        
        # Option to view raw data
        if st.checkbox("Show Raw Distribution Data"):
            tab1, tab2 = st.tabs(["By Count", "By Value"])
            
            with tab1:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Department Distribution")
                    for dept in distribution_data["departments"]:
                        st.write(f"{dept['department']}: {dept['count']:,} ({dept['count_percentage']:.1f}%)")
                with col2:
                    st.subheader("Sub-department Distribution")
                    for subdept in distribution_data["subdepartments"]:
                        st.write(f"{subdept['subdepartment']}: {subdept['count']:,} ({subdept['count_percentage']:.1f}%)")
            
            with tab2:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Department Distribution")
                    for dept in distribution_data["departments"]:
                        st.write(f"{dept['department']}: ฿{dept['value']/1e6:,.2f}M ({dept['value_percentage']:.1f}%)")
                with col2:
                    st.subheader("Sub-department Distribution")
                    for subdept in distribution_data["subdepartments"]:
                        st.write(f"{subdept['subdepartment']}: ฿{subdept['value']/1e6:,.2f}M ({subdept['value_percentage']:.1f}%)")
        
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        raise e

if __name__ == "__main__":
    main()