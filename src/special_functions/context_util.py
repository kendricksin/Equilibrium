# src/utils/context_utils.py

import streamlit as st
import pandas as pd
from typing import Optional, Tuple

def get_analysis_data() -> Tuple[Optional[pd.DataFrame], str]:
    """
    Get data for analysis, either from context or regular flow
    
    Returns:
        Tuple of (DataFrame or None, source description)
    """
    # Check if we have context data
    if 'context_df' in st.session_state and st.session_state.context_df is not None:
        collections = st.session_state.context_collections
        collection_names = [c['name'] for c in collections]
        return st.session_state.context_df, f"Context: {', '.join(collection_names)}"
    
    return None, ""

def show_context_info():
    """Display current context information"""
    if 'context_df' in st.session_state and st.session_state.context_df is not None:
        collections = st.session_state.context_collections
        
        with st.expander("📚 Current Context", expanded=False):
            st.markdown(f"Analyzing {len(st.session_state.context_df):,} records from:")
            for coll in collections:
                st.markdown(f"- {coll['name']} ({coll['row_count']:,} rows)")
            
            if st.button("🔄 Reset Context", key="reset_context_button"):
                st.session_state.context_collections = []
                st.session_state.context_df = None
                st.rerun()
    else:
        st.info("No context data loaded. Use the Context Manager to add collections for analysis.")