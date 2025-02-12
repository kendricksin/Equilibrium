# src/components/layout/ContextSelector.py

import streamlit as st
from typing import Optional, List, Dict, Any
from services.database.collections_manager import get_collections, get_collection_df, save_collection
import pandas as pd
from datetime import datetime, timedelta

def handle_duplicate_projects(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate projects based on project_id if it exists"""
    if 'project_id' in df.columns:
        return df.drop_duplicates(subset=['project_id'], keep='first')
    return df

def get_current_results() -> Optional[pd.DataFrame]:
    """Safely get current results from session state"""
    if 'filtered_results' in st.session_state:
        df = st.session_state.filtered_results
        if isinstance(df, pd.DataFrame) and not df.empty:
            return df
            
    if 'search_results' in st.session_state:
        df = st.session_state.search_results
        if isinstance(df, pd.DataFrame) and not df.empty:
            return df
            
    return None

def ContextSelector():
    """Sidebar component for context selection and collection management"""
    
    # Initialize session state
    if 'context_collections' not in st.session_state:
        st.session_state.context_collections = []
    if 'context_df' not in st.session_state:
        st.session_state.context_df = None
        
    with st.sidebar:
        st.markdown("### 📚 Analysis Context")
        
        # Display current context
        if st.session_state.context_df is not None:
            df = st.session_state.context_df
            deduped_df = handle_duplicate_projects(df.copy())
            
            st.markdown(f"""
            **Active Collections:** {len(st.session_state.context_collections)}  
            **Projects:** {len(deduped_df):,}
            """)
            
            # Show collection names
            if st.session_state.context_collections:
                with st.expander("Active Collections", expanded=True):
                    for coll in st.session_state.context_collections:
                        st.markdown(f"- {coll['name']}")
            
            if st.button("🔄 Reset Context", key="sidebar_reset_context"):
                st.session_state.context_collections = []
                st.session_state.context_df = None
                st.rerun()
        
        st.divider()
        
        # Save current results section (if results exist)
        current_results = get_current_results()
        if current_results is not None:
            st.markdown("### 💾 Save Current Results")
            
            # Collection name input
            name = st.text_input(
                "Collection Name",
                key="sidebar_collection_name",
                placeholder="Enter collection name"
            )
            
            # Optional description
            with st.expander("Add Description", expanded=False):
                description = st.text_area(
                    "Description",
                    key="sidebar_collection_desc",
                    placeholder="Describe this collection",
                    height=100
                )
                
                tags = st.text_input(
                    "Tags (comma-separated)",
                    key="sidebar_collection_tags",
                    placeholder="tag1, tag2, tag3"
                )
            
            col1, col2 = st.columns(2)
            with col1:
                save_button = st.button(
                    "Save",
                    type="primary",
                    key="sidebar_save",
                    use_container_width=True
                )
            with col2:
                save_and_use = st.button(
                    "Save & Use",
                    type="secondary",
                    key="sidebar_save_use",
                    use_container_width=True
                )
                
            if save_button or save_and_use:
                if not name:
                    st.error("Please enter a collection name")
                else:
                    try:
                        # Process tags
                        tag_list = [tag.strip() for tag in tags.split(",")] if tags else []
                        
                        # Save collection
                        collection_info = save_collection(
                            current_results,
                            name,
                            description,
                            tag_list,
                            source="search_results"
                        )
                        
                        if collection_info:
                            st.success(f"Saved '{name}'")
                            
                            # Handle Save & Use
                            if save_and_use:
                                if collection_info['name'] not in [c['name'] for c in st.session_state.context_collections]:
                                    st.session_state.context_collections.append(collection_info)
                                    if st.session_state.context_df is None:
                                        st.session_state.context_df = current_results
                                    else:
                                        combined_df = pd.concat(
                                            [st.session_state.context_df, current_results],
                                            ignore_index=True
                                        )
                                        st.session_state.context_df = handle_duplicate_projects(combined_df)
                                    st.success("Added to context!")
                                    st.rerun()
                        else:
                            st.error(f"Collection '{name}' already exists")
                            
                    except Exception as e:
                        st.error(f"Error saving collection: {str(e)}")
            
            st.divider()
        
        # Quick add existing collections
        st.markdown("### Quick Add Collection")
        
        # Get available collections
        collections = get_collections()
        available_collections = [
            c for c in collections 
            if c['name'] not in [x['name'] for x in st.session_state.context_collections]
        ]
        
        if available_collections:
            # Create formatted options
            collection_options = {
                f"{c['name']} ({c['row_count']:,} projects)": c 
                for c in available_collections
            }
            
            selected = st.selectbox(
                "Select Collection",
                options=[""] + list(collection_options.keys()),
                key="sidebar_collection_select"
            )
            
            if selected:
                collection = collection_options[selected]
                if st.button("➕ Add to Context", key="sidebar_add_context"):
                    new_df = get_collection_df(collection['name'])
                    
                    if new_df is not None:
                        # Add to collections list
                        st.session_state.context_collections.append(collection)
                        
                        # Update context DataFrame
                        if st.session_state.context_df is None:
                            st.session_state.context_df = new_df
                        else:
                            combined_df = pd.concat(
                                [st.session_state.context_df, new_df],
                                ignore_index=True
                            )
                            # Remove duplicates when combining
                            st.session_state.context_df = handle_duplicate_projects(combined_df)
                        
                        st.success(f"Added '{collection['name']}' to context")
                        st.rerun()
        else:
            st.info("No collections available")
        
        # Link to context manager
        st.markdown("---")
        if st.button("📚 Open Context Manager", use_container_width=True):
            st.session_state.current_page = 'context_manager'
            st.rerun()