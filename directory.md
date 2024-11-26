Equilibrium/
│
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── layout/
│   │   │   ├── Sidebar.py          # Enhanced sidebar with all filters
│   │   │   ├── Header.py           # Header component
│   │   │   └── MetricsSummary.py   # Enhanced metrics with purchase methods & types
│   │   │
│   │   ├── filters/
│   │   │   ├── DepartmentFilter.py    # Department and sub-department filter
│   │   │   ├── DatePriceFilter.py     # Date range and price range filter
│   │   │   └── PurchaseTypeFilter.py  # Purchase method and project type filter
│   │   │
│   │   ├── tables/
│   │   │   ├── CompanyTable.py
│   │   │   └── ProjectsTable.py
│   │   │
│   │   └── charts/
│   │       ├── TimeSeriesChart.py
│   │       ├── ValueDistribution.py
│   │       └── DepartmentDistribution.py
│   │
│   ├── pages/              # Main application pages
│   │   ├── Home.py              # Enhanced home page with new metrics
│   │   ├── Dashboard.py
│   │   └── CompanySelection.py
│   │
│   ├── services/           # Business logic and data services
│   │   ├── cache/
│   │   │   ├── cache_manager.py       # Generic cache management
│   │   │   ├── department_cache.py    # Department caching
│   │   │   ├── purchase_type_cache.py # Purchase method & type caching
│   │   │   └── filter_cache.py        # Enhanced filter caching
│   │   │
│   │   ├── database/
│   │   │   └── mongodb.py        # Enhanced with purchase method & type queries
│   │   │
│   │   └── analytics/
│   │       ├── analytics_service.py  # Enhanced with purchase method & type analysis
│   │       └── insights_service.py   # Enhanced insights
│   │
│   ├── utils/             # Helper functions and utilities
│   │   ├── date_utils.py
│   │   ├── format_utils.py
│   │   └── validation.py
│   │
│   ├── state/            # State management
│   │   ├── session.py     # Enhanced with new filter states
│   │   └── filters.py     # Enhanced filter management
│   │
│   └── config/           # Configuration files
│       ├── logging_config.py
│       └── app_config.py
│
└── app.py               # Main application entry point
