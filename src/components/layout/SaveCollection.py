# src/components/layout/SaveCollection.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List
from services.database.collections import save_collection

def SaveCollection(
    df: pd.DataFrame,
    source: str,
    key_prefix: str = ""
):
    """
    Component for saving dataframes as collections to local storage
    
    Args:
        df (pd.DataFrame): DataFrame to save
        source (str): Source of the data (e.g., 'project_search', 'company_comparison')
        key_prefix (str): Prefix for component keys
    """
    with st.expander("💾 Save as Collection"):
        # Show expiry info
        st.info("Collections are automatically removed after 30 days")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            name = st.text_input(
                "Collection Name",
                key=f"{key_prefix}collection_name",
                placeholder="Enter a name for this collection"
            )
            
            description = st.text_area(
                "Description",
                key=f"{key_prefix}collection_description",
                placeholder="Describe what this collection contains"
            )
            
            # Tag input - comma separated
            tags = st.text_input(
                "Tags (comma-separated)",
                key=f"{key_prefix}collection_tags",
                placeholder="tag1, tag2, tag3"
            )
            
        with col2:
            st.markdown("#### Summary")
            st.markdown(f"**Rows:** {len(df):,}")
            st.markdown(f"**Columns:** {len(df.columns):,}")
            st.markdown(f"**Expires:** {(datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')}")
            
            save_button = st.button(
                "Save Collection",
                type="primary",
                key=f"{key_prefix}save_collection",
                use_container_width=True
            )
        
        if save_button:
            if not name:
                st.error("Please enter a collection name")
                return
                
            try:
                # Process tags
                tag_list = [
                    tag.strip() 
                    for tag in tags.split(",") 
                    if tag.strip()
                ] if tags else []
                
                # Save collection
                if save_collection(df, name, description, tag_list, source):
                    st.success(f"Collection '{name}' saved successfully!")
                else:
                    st.error(f"Collection '{name}' already exists")
                
            except Exception as e:
                st.error(f"Error saving collection: {str(e)}")