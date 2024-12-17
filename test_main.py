import os
import pymongo
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime

def create_aggregation_collection(db):
    """Create and populate the department distribution aggregation collection"""
    if "department_distribution" in db.list_collection_names():
        db.department_distribution.drop()
    
    pipeline = [
        {
            "$group": {
                "_id": {
                    "dept": "$dept_name",
                    "subdept": "$dept_sub_name"
                },
                "count": {"$sum": 1},
                "total_value": {"$sum": "$price_build"}
            }
        },
        {
            "$project": {
                "_id": 1,
                "count": 1,
                "total_value": 1,
                "parent_dept": "$_id.dept"
            }
        },
        {
            "$merge": {
                "into": "department_distribution",
                "whenMatched": "replace",
                "whenNotMatched": "insert"
            }
        }
    ]
    
    db.projects.aggregate(pipeline)
    
    total_docs = db.projects.count_documents({})
    total_value = db.projects.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$price_build"}}}
    ]).next()["total"]
    
    db.department_distribution.insert_one({
        "_id": "metadata",
        "last_updated": datetime.now(),
        "total_projects": total_docs,
        "total_value": total_value
    })
    
    return True

def get_department_distribution(collection):
    """Get department distribution from the aggregation collection"""
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
    
    # Get sub-departments by department
    subdept_by_dept = {}
    for dept in all_depts[:10]:  # Only get subdepts for top 10 departments
        subdept_pipeline = [
            {
                "$match": {
                    "_id.dept": dept["department"]
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
                        "$multiply": [{"$divide": ["$count", dept["count"]]}, 100]
                    },
                    "value": 1,
                    "value_percentage": {
                        "$multiply": [{"$divide": ["$value", dept["value"]]}, 100]
                    }
                }
            },
            {"$sort": {"count": -1}}
        ]
        
        subdept_by_dept[dept["department"]] = list(collection.aggregate(subdept_pipeline))
    
    return {
        "departments": dept_results,
        "subdepartments_by_dept": subdept_by_dept,
        "total_projects": total_docs,
        "total_value": total_value,
        "last_updated": metadata["last_updated"]
    }

def create_department_charts(data):
    """Create department distribution pie charts"""
    dept_labels = [d["department"] for d in data["departments"]]
    dept_counts = [d["count_percentage"] for d in data["departments"]]
    dept_values = [d["value_percentage"] for d in data["departments"]]
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            'Project Count Distribution',
            'Project Value Distribution'
        ),
        specs=[[{'type': 'pie'}, {'type': 'pie'}]]
    )
    
    # Add project count pie chart
    fig.add_trace(
        go.Pie(
            labels=dept_labels,
            values=dept_counts,
            textinfo='label+percent',
            textposition='inside',
            hovertemplate="<b>%{label}</b><br>" +
                         "Projects: %{percent:.1f}%<br>" +
                         "Click department selector below for details<extra></extra>"
        ),
        row=1, col=1
    )
    
    # Add project value pie chart
    fig.add_trace(
        go.Pie(
            labels=dept_labels,
            values=dept_values,
            textinfo='label+percent',
            textposition='inside',
            hovertemplate="<b>%{label}</b><br>" +
                         "Value: %{percent:.1f}%<br>" +
                         "Click department selector below for details<extra></extra>"
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        height=500,
        showlegend=False,
        title={
            'text': 'Department Distribution',
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        }
    )
    
    return fig

def create_subdepartment_chart(subdepts, dept_name, metric="count"):
    """Create pie chart for sub-departments of selected department"""
    if not subdepts:
        return None
    
    labels = [d["subdepartment"] for d in subdepts]
    values = [d[f"{metric}_percentage"] for d in subdepts]
    
    fig = go.Figure(data=[
        go.Pie(
            labels=labels,
            values=values,
            textinfo='label+percent',
            textposition='inside',
            hovertemplate="<b>%{label}</b><br>" +
                         f"{'Count' if metric == 'count' else 'Value'}: " +
                         "%{percent:.1f}%<extra></extra>"
        )
    ])
    
    fig.update_layout(
        height=500,
        showlegend=False,
        title={
            'text': f'{dept_name} Sub-departments by {"Project Count" if metric == "count" else "Project Value"}',
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        }
    )
    
    return fig

def main():
    st.set_page_config(layout="wide", page_title="Project Distribution")
    st.title("Project Distribution Analysis")
    
    try:
        # Connect to MongoDB
        client = pymongo.MongoClient(os.getenv("MONGO_URI"))
        db = client[os.getenv("MONGO_DB")]
        
        # Check if we need to create/update the aggregation collection
        refresh_data = False
        if "department_distribution" not in db.list_collection_names():
            refresh_data = True
            st.info("Creating aggregation collection...")
        elif st.button("🔄 Refresh Data"):
            refresh_data = True
        
        if refresh_data:
            with st.spinner("Aggregating department distribution..."):
                create_aggregation_collection(db)
        
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
            st.markdown(f"Last Updated: **{distribution_data['last_updated'].strftime('%Y-%m-%d %H:%M')}**")
        
        # Create and display department charts
        dept_fig = create_department_charts(distribution_data)
        st.plotly_chart(dept_fig, use_container_width=True)
        
        # Department selection
        st.markdown("---")
        dept_options = [d["department"] for d in distribution_data["departments"] if d["department"] != "Others"]
        selected_dept = st.selectbox(
            "Select Department to View Sub-departments",
            options=[""] + dept_options
        )
        
        if selected_dept:
            metric = st.radio(
                "View by",
                options=["count", "value"],
                format_func=lambda x: "Project Count" if x == "count" else "Project Value",
                horizontal=True
            )
            
            subdepts = distribution_data["subdepartments_by_dept"].get(selected_dept, [])
            subdept_fig = create_subdepartment_chart(subdepts, selected_dept, metric)
            
            if subdept_fig:
                st.plotly_chart(subdept_fig, use_container_width=True)
                
                # Show raw data in expandable section
                with st.expander("View Data"):
                    if metric == "count":
                        for subdept in subdepts:
                            st.write(f"{subdept['subdepartment']}: {subdept['count']:,} projects ({subdept['count_percentage']:.1f}%)")
                    else:
                        for subdept in subdepts:
                            st.write(f"{subdept['subdepartment']}: ฿{subdept['value']/1e6:,.2f}M ({subdept['value_percentage']:.1f}%)")
            else:
                st.info("No sub-departments found for this department")
        
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        raise e

if __name__ == "__main__":
    main()