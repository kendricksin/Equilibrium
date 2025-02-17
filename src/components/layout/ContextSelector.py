# src/components/layout/ContextSelector.py

import streamlit as st
import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime
from services.database.collections_manager import get_collections, get_collection_df

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
    """
    Streamlit sidebar component for managing analysis context and collections
    """
    # Initialize session state
    if 'context_collections' not in st.session_state:
        st.session_state.context_collections = []
    if 'context_df' not in st.session_state:
        st.session_state.context_df = None
    
    with st.sidebar:
        st.markdown("### 📚 Analysis Context")
        
        # Display current context overview
        if st.session_state.context_df is not None:
            df = st.session_state.context_df
            deduped_df = handle_duplicate_projects(df.copy())
            
            # Context metrics
            st.info(f"""
            **Active Collections:** {len(st.session_state.context_collections)}  
            **Total Projects:** {len(deduped_df):,}  
            **Unique Companies:** {deduped_df['winner'].nunique():,}  
            **Departments:** {deduped_df['dept_name'].nunique():,}
            """)
            
            # Show active collections
            if st.session_state.context_collections:
                with st.expander("📋 Active Collections", expanded=True):
                    for collection in st.session_state.context_collections:
                        st.markdown(f"""
                        **{collection['name']}**  
                        {collection['row_count']:,} projects
                        """)
            
            # Reset context button
            if st.button("🔄 Reset Context", use_container_width=True):
                st.session_state.context_collections = []
                st.session_state.context_df = None
                st.rerun()
        
        st.divider()
        
        # Save current results section
        current_results = get_current_results()
        if current_results is not None:
            st.markdown("### 💾 Save Current Results")
            
            # Quick save form
            name = st.text_input(
                "Collection Name",
                key="quick_save_name",
                placeholder="Enter collection name"
            )
            
            with st.expander("Add Details", expanded=False):
                description = st.text_area(
                    "Description",
                    key="quick_save_desc",
                    placeholder="Describe this collection",
                    height=100
                )
                
                tags = st.text_input(
                    "Tags",
                    key="quick_save_tags",
                    placeholder="tag1, tag2, tag3"
                )
            
            # Save buttons
            col1, col2 = st.columns(2)
            with col1:
                save_button = st.button(
                    "💾 Save",
                    type="primary",
                    key="quick_save",
                    use_container_width=True
                )
            with col2:
                save_and_use = st.button(
                    "📌 Save & Use",
                    type="secondary",
                    key="quick_save_use",
                    use_container_width=True
                )
        
        st.divider()
        
        # Quick add existing collections
        st.markdown("### ➕ Quick Add Collection")
        
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
            
            # Collection selector
            selected = st.selectbox(
                "Select Collection",
                options=[""] + list(collection_options.keys()),
                key="quick_add_collection",
                help="Choose a collection to add to the current context"
            )
            
            if selected:
                collection = collection_options[selected]
                if st.button("➕ Add to Context", use_container_width=True):
                    # Load collection data
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
                            st.session_state.context_df = handle_duplicate_projects(combined_df)
                        
                        st.success(f"Added '{collection['name']}' to context")
                        st.rerun()
        else:
            st.info("No collections available to add")
        
        # Link to context manager
        st.markdown("---")
        if st.button("📚 Open Context Manager", use_container_width=True):
            st.session_state.current_page = 'context_manager'
            st.rerun()