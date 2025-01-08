src/
├── app.py                  # Main application entry point with department analysis
├── components/            
│   ├── filters/           # Filter-related components
│   │   ├── KeywordFilter.py    # Keyword-based search with include/exclude functionality
│   │   └── TableFilter.py      # Generic table filter utility for project data
│   ├── layout/
│   │   └── MetricsSummary.py   # Enhanced metrics summary with configurable styles
│   └── tables/
│       ├── CompanyTable.py     # Company information display with selection capability
│       └── ProjectsTable.py    # Project information display with search/sort
│
├── pages/
│   ├── ProjectSearch.py        # Project search page with keyword filtering
│   └── CompanySearch.py        # Company search and comparison functionality
│
├── services/
│   ├── analytics/
│   │   ├── company_comparison.py  # Service for analyzing and comparing companies
│   │   └── treemap_service.py     # Service for creating treemap visualizations
│   ├── cache/
│   │   ├── cache_manager.py       # File-based caching management
│   │   └── department_cache.py    # Department-specific caching service
│   └── database/
│       └── mongodb.py             # MongoDB service with connection management
│
└── state/
    ├── data_state.py         # Application data state and caching management
    ├── filters.py            # Filter state management and operations
    └── session.py            # Streamlit session state management