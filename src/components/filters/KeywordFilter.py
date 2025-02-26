# src/components/filters/KeywordFilter.py

import streamlit as st
from typing import List, Dict, Any, Optional
import re
import logging

logger = logging.getLogger(__name__)

class KeywordFilter:
    """Enhanced keyword filter component with include/exclude functionality"""
    
    def __init__(
        self,
        key_prefix: str = "",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize KeywordFilter
        
        Args:
            key_prefix: Prefix for component keys
            config: Filter configuration
        """
        self.key_prefix = key_prefix
        self.config = self._get_default_config()
        if config:
            self.config.update(config)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'min_keyword_length': 2,
            'max_keywords': 10,
            'case_sensitive': False,
            'show_advanced': True,
            'default_search_fields': ['project_name', 'winner', 'dept_name']
        }
    
    def render(
        self,
        search_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Render keyword filter controls
        
        Args:
            search_fields: Optional list of fields to search
            
        Returns:
            Dictionary of filter parameters
        """
        filter_params = {
            'include_keywords': [],
            'exclude_keywords': [],
            'search_fields': search_fields or self.config['default_search_fields'],
            'case_sensitive': False
        }
        
        # Main keyword input
        keywords = st.text_input(
            "🔍 Search Keywords",
            key=f"{self.key_prefix}_keywords",
            help="Enter keywords separated by spaces. Use - before a word to exclude it."
        )
        
        # Advanced options
        if self.config['show_advanced']:
            with st.expander("Advanced Search Options"):
                # Case sensitivity
                filter_params['case_sensitive'] = st.checkbox(
                    "Case Sensitive",
                    key=f"{self.key_prefix}_case_sensitive"
                )
                
                # Search fields selection
                if search_fields:
                    # Create a mapping for display names
                    field_display_names = {
                        'project_name': 'Project Name',
                        'winner': 'Company',
                        'dept_name': 'Department',
                        'purchase_method_name': 'Purchase Method'
                    }
                    
                    filter_params['search_fields'] = st.multiselect(
                        "Search Fields",
                        options=search_fields,
                        default=filter_params['search_fields'],
                        format_func=lambda x: field_display_names.get(x, x),
                        key=f"{self.key_prefix}_fields"
                    )
        
        # Process keywords
        if keywords:
            words = keywords.split()
            for word in words:
                if len(word) >= self.config['min_keyword_length']:
                    if word.startswith('-'):
                        filter_params['exclude_keywords'].append(word[1:])
                    else:
                        filter_params['include_keywords'].append(word)
            
            # Validate keyword count
            total_keywords = len(filter_params['include_keywords']) + \
                           len(filter_params['exclude_keywords'])
            if total_keywords > self.config['max_keywords']:
                st.warning(f"Maximum {self.config['max_keywords']} keywords allowed")
                return None
        
        return filter_params
    
    def build_query(self, filter_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build MongoDB query from filter parameters
        
        Args:
            filter_params: Filter parameters from render()
            
        Returns:
            MongoDB query dictionary
        """
        try:
            if not filter_params:
                return {}
            
            query = {"$and": []}
            
            # Include keywords
            if filter_params['include_keywords']:
                include_conditions = []
                for field in filter_params['search_fields']:
                    for keyword in filter_params['include_keywords']:
                        pattern = re.escape(keyword)
                        if not filter_params['case_sensitive']:
                            include_conditions.append({
                                field: {"$regex": pattern, "$options": "i"}
                            })
                        else:
                            include_conditions.append({
                                field: {"$regex": pattern}
                            })
                if include_conditions:
                    query["$and"].append({"$or": include_conditions})
            
            # Exclude keywords
            if filter_params['exclude_keywords']:
                exclude_conditions = []
                for field in filter_params['search_fields']:
                    for keyword in filter_params['exclude_keywords']:
                        pattern = re.escape(keyword)
                        if not filter_params['case_sensitive']:
                            exclude_conditions.append({
                                field: {"$not": {"$regex": pattern, "$options": "i"}}
                            })
                        else:
                            exclude_conditions.append({
                                field: {"$not": {"$regex": pattern}}
                            })
                if exclude_conditions:
                    query["$and"].extend(exclude_conditions)
            
            return query if query["$and"] else {}
            
        except Exception as e:
            logger.error(f"Error building query: {e}")
            return {}