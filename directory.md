src/
├── analytics/
│   ├── company/
│   │   ├── comparison.py        # Company comparison logic
│   │   └── metrics.py          # Company metrics calculations
│   ├── department/
│   │   ├── aggregation.py      # Department aggregation logic
│   │   └── distribution.py     # Department distribution analysis
│   └── projects/
│       ├── filters.py          # Project filtering logic
│       └── metrics.py          # Project metrics calculations
│
├── components/
│   ├── charts/
│   │   ├── TreemapChart.py     # Reusable treemap component
│   │   └── ComparisonChart.py  # Company comparison charts
│   ├── filters/
│   │   ├── DateRangeFilter.py  # Date range selector
│   │   └── SearchFilter.py     # Search input with options
│   ├── tables/
│   │   ├── DataTable.py        # Base table component
│   │   └── SortableTable.py    # Table with sorting capabilities
│   └── common/
│       ├── MetricCard.py       # Reusable metric display card
│       └── LoadingState.py     # Loading indicators
│
├── services/
│   ├── cache/                  # Your existing cache services
│   └── database/              # Your existing database services
│
├── pages/                     # Streamlit pages
│
└── utils/
    ├── formatters.py          # Data formatting utilities
    └── validators.py          # Input validation utilities