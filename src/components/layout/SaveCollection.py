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
    Streamlit component for saving dataframes as collections with option to use immediately
    
    Args:
        df (pd.DataFrame): DataFrame to save
        source (str): Source of the data (e.g., 'project_search', 'company_comparison')
        key_prefix (str): Prefix for component keys
        allow_use_collection (bool): Whether to show "Save and Use" option
    """
    with st.expander("💾 Save as Collection", expanded=False):
        # Collection metadata form
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Collection details
            name = st.text_input(
                "Collection Name",
                key=f"{key_prefix}collection_name",
                placeholder="Enter a descriptive name",
                help="Choose a unique name for this collection"
            )
            
            description = st.text_area(
                "Description",
                key=f"{key_prefix}collection_description",
                placeholder="Describe what this collection contains",
                help="Add details about what's included in this collection"
            )
            
            # Tags input with example
            tags = st.text_input(
                "Tags",
                key=f"{key_prefix}collection_tags",
                placeholder="tag1, tag2, tag3",
                help="Comma-separated tags to help organize collections"
            )
        
        with col2:
            # Collection summary
            st.markdown("#### Summary")
            st.markdown(f"**Rows:** {len(df):,}")
            st.markdown(f"**Columns:** {len(df.columns):,}")
            
            # Show expiry date
            expiry_date = datetime.now() + timedelta(days=30)
            st.markdown(f"**Expires:** {expiry_date.strftime('%Y-%m-%d')}")
            
            # Save buttons
            save_button = st.button(
                "💾 Save Collection",
                type="primary",
                key=f"{key_prefix}save_collection",
                use_container_width=True
            )
            
            if allow_use_collection:
                save_and_use = st.button(
                    "📌 Save & Use",
                    type="secondary",
                    key=f"{key_prefix}save_and_use",
                    use_container_width=True,
                    help="Save collection and add to current context"
                )
            else:
                save_and_use = False
        
        # Handle save actions
        if save_button or save_and_use:
            if not name:
                st.error("Please enter a collection name")
                return None
            
            try:
                # Process tags
                tag_list = [tag.strip() for tag in tags.split(",")] if tags else []
                
                # Save collection
                success = save_collection(
                    df=df,
                    name=name,
                    description=description,
                    tags=tag_list,
                    source=source
                )
                
                if success:
                    st.success(f"Collection '{name}' saved successfully!")
                    
                    # Handle Save & Use
                    if save_and_use:
                        if 'context_collections' not in st.session_state:
                            st.session_state.context_collections = []
                        if 'context_df' not in st.session_state:
                            st.session_state.context_df = None
                        
                        # Add to context
                        st.session_state.context_collections.append({
                            'name': name,
                            'description': description,
                            'tags': tag_list,
                            'source': source,
                            'created_at': datetime.now().isoformat(),
                            'row_count': len(df)
                        })
                        
                        # Update context DataFrame
                        if st.session_state.context_df is None:
                            st.session_state.context_df = df
                        else:
                            st.session_state.context_df = pd.concat(
                                [st.session_state.context_df, df],
                                ignore_index=True
                            )
                        
                        st.success("Added to analysis context!")
                        st.rerun()
                else:
                    st.error(f"A collection named '{name}' already exists")
                    
            except Exception as e:
                st.error(f"Error saving collection: {str(e)}")
                return None