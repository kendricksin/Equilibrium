src/
├── pages/                      # Streamlit pages
│   ├── 01_🔍_ProjectSearch.py
│   ├── 02_🏢_CompanySearch.py
│   ├── 03_🏛️_DepartmentSearch.py
│   ├── 04_📚_ContextManager.py
│   ├── 05_📈_MatrixAnalysis.py
│   ├── 06_📊_StackedCompany.py
│   └── 07_📊_HHIAnalysis.py
├── services/
│   ├── database/              # Database services
│   │   ├── postgres.py        # PostgreSQL connection & core queries
│   │   └── migrations/        # SQL migration scripts
│   ├── analytics/             # Analytics services
│   │   ├── price_analysis.py
│   │   ├── company_analysis.py
│   │   ├── project_analysis.py
│   │   └── department_analysis.py
│   └── cache/                 # Caching services
│       ├── cache_manager.py
│       └── data_cache.py
├── components/                # Reusable UI components
│   ├── filters/
│   │   ├── KeywordFilter.py
│   │   └── TableFilter.py
│   ├── tables/
│   │   ├── ProjectsTable.py
│   │   └── CompanyTable.py
│   └── layout/
│       ├── MetricsSummary.py
│       └── ContextSelector.py
└── utils/                     # Utility functions
    ├── data_utils.py
    └── visualization_utils.py


src/
└── services/
    └── analytics/
        ├── company_analysis.py        # Combined from company_comparison.py and company_projects.py
        │   - Market share analysis
        │   - Company competition metrics
        │   - Project distribution analysis
        │   - Company performance metrics
        │
        ├── price_analysis.py          # From price_cut_trend.py
        │   - Price cut trends
        │   - Value distribution analysis
        │   - Price competition metrics
        │
        ├── project_analysis.py        # New consolidation of project-related analytics
        │   - Project distribution
        │   - Project timeline analysis
        │   - Project type analysis
        │   - Procurement method analysis
        │
        ├── department_analysis.py     # From subdept_projects.py
        │   - Department distribution
        │   - Sub-department analysis
        │   - Department performance metrics
        │
        └── visualization.py           # From treemap_service.py and other visualization logic
            - Treemap visualizations
            - Heatmaps
            - Network graphs
            - Distribution charts