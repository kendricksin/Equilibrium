project_root/
│
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── layout/
│   │   │   ├── Sidebar.py          # Sidebar component with filters
│   │   │   ├── Header.py           # Header component if needed
│   │   │   └── MetricsSummary.py   # Top metrics container
│   │   │
│   │   ├── filters/
│   │   │   ├── DepartmentFilter.py
│   │   │   ├── DateFilter.py
│   │   │   └── PriceFilter.py
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
│   │   ├── Home.py
│   │   ├── Dashboard.py
│   │   └── CompanySelection.py
│   │
│   ├── services/           # Business logic and data services
│   │   ├── cache/
│   │   │   ├── department_cache.py
│   │   │   └── filter_cache.py
│   │   │
│   │   ├── database/
│   │   │   └── mongodb.py
│   │   │
│   │   └── analytics/
│   │       └── metrics.py
│   │
│   ├── utils/             # Helper functions and utilities
│   │   ├── date_utils.py
│   │   ├── format_utils.py
│   │   └── validation.py
│   │
│   └── state/            # State management
│       ├── session.py
│       └── filters.py
│
├── config/               # Configuration files
│   ├── logging_config.py
│   └── app_config.py
│
└── app.py               # Main application entry point