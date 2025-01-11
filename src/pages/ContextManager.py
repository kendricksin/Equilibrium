# src/pages/ContextManager.py

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, Any
from services.database.collections import (
    get_collections,
    get_collection_df,
    delete_collection
)
from components.layout.PageLayout import PageLayout

def display_collection_card(collection: Dict[str, Any], on_add_to_context):
    """Display a collection as a card with actions"""
    with st.container():
        # Add border and padding
        st.markdown("""
        <style>
        .collection-card {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("<div class='collection-card'>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"#### {collection['name']}")
            if collection.get('description'):
                st.markdown(collection['description'])
            
            # Display tags
            if collection.get('tags'):
                st.markdown("**Tags:** " + ", ".join(collection['tags']))
            
            # Display metadata
            created_at = datetime.fromisoformat(collection['created_at'])
            expires_at = datetime.fromisoformat(collection['expires_at'])
            
            st.markdown(f"""
            **Source:** {collection['source']}  
            **Created:** {created_at.strftime('%Y-%m-%d %H:%M')}  
            **Expires:** {expires_at.strftime('%Y-%m-%d')}  
            **Size:** {collection['row_count']:,} rows × {collection['column_count']} columns
            """)
        
        with col2:
            # Action buttons
            if st.button("➕ Add to Context", key=f"add_{collection['name']}"):
                on_add_to_context(collection)
            
            if st.button("🗑️ Delete", key=f"delete_{collection['name']}"):
                if delete_collection(collection['name']):
                    st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)

def ContextManager():
    """Context Manager page for managing saved collections and context"""
    
    # Initialize session state for context if not exists
    if 'context_collections' not in st.session_state:
        st.session_state.context_collections = []
    if 'context_df' not in st.session_state:
        st.session_state.context_df = None
    
    st.title("📚 Context Manager")
    
    # Context Section
    st.header("Current Context")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.session_state.context_df is not None:
            st.markdown(f"""
            **Active Collections:** {len(st.session_state.context_collections)}  
            **Total Rows:** {len(st.session_state.context_df):,}  
            **Total Columns:** {len(st.session_state.context_df.columns)}
            """)
        else:
            st.info("No collections added to context")
    
    with col2:
        if st.button("🔄 Reset Context", use_container_width=True):
            st.session_state.context_collections = []
            st.session_state.context_df = None
            st.rerun()
    
    # Display current context collections
    if st.session_state.context_collections:
        st.markdown("### Active Collections")
        for coll in st.session_state.context_collections:
            st.markdown(f"- {coll['name']} ({coll['row_count']:,} rows)")
    
    # Saved Collections Section
    st.markdown("---")
    st.header("Saved Collections")
    
    # Filter controls
    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input(
            "🔍 Search collections",
            placeholder="Search by name, description, or tags"
        )
    with col2:
        sort_by = st.selectbox(
            "Sort by",
            ["Newest", "Oldest", "Name", "Size"],
            key="sort_collections"
        )
    
    # Map sort options to service parameters
    sort_mapping = {
        "Newest": ("created_at", False),
        "Oldest": ("created_at", True),
        "Name": ("name", True),
        "Size": ("row_count", False)
    }
    sort_field, ascending = sort_mapping[sort_by]
    
    # Get collections from local storage
    collections = get_collections(
        search=search,
        sort_by=sort_field,
        ascending=ascending
    )
    
    # Display collections
    def add_to_context(collection):
        if collection['name'] not in [c['name'] for c in st.session_state.context_collections]:
            # Get collection data
            new_df = get_collection_df(collection['name'])
            
            if new_df is not None:
                # Add to context collections list
                st.session_state.context_collections.append(collection)
                
                # Update context DataFrame
                if st.session_state.context_df is None:
                    st.session_state.context_df = new_df
                else:
                    st.session_state.context_df = pd.concat(
                        [st.session_state.context_df, new_df],
                        ignore_index=True
                    )
                
                st.success(f"Added '{collection['name']}' to context")
                st.rerun()
            else:
                st.error(f"Error loading data for '{collection['name']}'")
        else:
            st.warning(f"'{collection['name']}' is already in context")
    
    for collection in collections:
        display_collection_card(collection, add_to_context)
    
    if not collections:
        st.info("No collections found. Save some data from the analysis pages to get started!")

if __name__ == "__main__":
    PageLayout(ContextManager)