# src/components/layout/SaveCollection.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List
from services.database.collections_manager import save_collection

def SaveCollection(
    df: pd.DataFrame,
    source: str,
    key_prefix: str = "",
    allow_use_collection: bool = True
):
    """
    Enhanced component for saving dataframes as collections with option to use immediately
    
    Args:
        df (pd.DataFrame): DataFrame to save
        source (str): Source of the data (e.g., 'project_search', 'company_comparison')
        key_prefix (str): Prefix for component keys
        allow_use_collection (bool): Whether to show "Save and Use" option
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
            
            # Action buttons
            save_button = st.button(
                "Save Collection",
                type="primary",
                key=f"{key_prefix}save_collection",
                use_container_width=True
            )
            
            if allow_use_collection:
                save_and_use = st.button(
                    "Save & Use Collection",
                    type="secondary",
                    key=f"{key_prefix}save_and_use",
                    use_container_width=True
                )
            else:
                save_and_use = False
        
        if save_button or save_and_use:
            if not name:
                st.error("Please enter a collection name")
                return None
                
            try:
                # Restore original values before saving
                save_df = df.copy()
                if 'sum_price_agree' in save_df.columns:
                    save_df['sum_price_agree'] = save_df['sum_price_agree'] * 1e6
                if 'price_build' in save_df.columns:
                    save_df['price_build'] = save_df['price_build'] * 1e6
                
                # Process tags
                tag_list = [
                    tag.strip() 
                    for tag in tags.split(",") 
                    if tag.strip()
                ] if tags else []
                
                # Save collection
                collection_info = save_collection(save_df, name, description, tag_list, source)
                if collection_info:
                    st.success(f"Collection '{name}' saved successfully!")
                    
                    # Handle "Save and Use" functionality
                    if save_and_use:
                        # Initialize session state if needed
                        if 'context_collections' not in st.session_state:
                            st.session_state.context_collections = []
                        if 'context_df' not in st.session_state:
                            st.session_state.context_df = None
                            
                        # Add to context
                        st.session_state.context_collections.append(collection_info)
                        if st.session_state.context_df is None:
                            st.session_state.context_df = df
                        else:
                            st.session_state.context_df = pd.concat(
                                [st.session_state.context_df, df],
                                ignore_index=True
                            )
                        st.success("Collection added to analysis context!")
                        return collection_info
                else:
                    st.error(f"Collection '{name}' already exists")
                
            except Exception as e:
                st.error(f"Error saving collection: {str(e)}")
            
            return None