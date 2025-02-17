import os
import logging
from typing import Optional, Dict, Any, List
import pandas as pd
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from functools import wraps
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def retry_on_connection_error(max_retries: int = 3, delay: float = 1.0):
    """Decorator for retrying on PostgreSQL connection errors"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except psycopg2.OperationalError as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(delay)
                        logger.warning(f"Retrying connection (attempt {attempt + 2}/{max_retries})")
            raise last_error
        return wrapper
    return decorator

class PostgresService:
    """Service class for PostgreSQL operations"""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        load_dotenv(override=True)
        self.db_params = {
            'dbname': os.getenv('POSTGRES_DB', 'projects'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', '5432')
        }
        self._conn = None
        self._cur = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    @retry_on_connection_error()
    def connect(self):
        """Establish connection to PostgreSQL"""
        try:
            if self._conn is None or self._conn.closed:
                self._conn = psycopg2.connect(**self.db_params)
                self._conn.autocommit = True
                
            if self._cur is None or self._cur.closed:
                self._cur = self._conn.cursor(cursor_factory=RealDictCursor)
                
            logger.info(f"Successfully connected to PostgreSQL database: {self.db_params['dbname']}")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    def disconnect(self):
        """Close PostgreSQL connection"""
        try:
            if self._cur is not None:
                self._cur.close()
            if self._conn is not None:
                self._conn.close()
                self._conn = None
            logger.info("Disconnected from PostgreSQL")
        except Exception as e:
            logger.error(f"Error disconnecting from PostgreSQL: {e}")

    def get_department_summary(self, view_by: str = "count", limit: Optional[int] = None) -> List[Dict]:
        """Get department summary with sorting and pre-calculated metrics"""
        try:
            self.connect()
            sort_field = "count" if view_by == "count" else "total_value"
            
            sql = """
                WITH dept_stats AS (
                    SELECT 
                        dept_name as department,
                        COUNT(*) as count,
                        SUM(sum_price_agree) as total_value,
                        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as count_percentage,
                        SUM(sum_price_agree) * 100.0 / SUM(SUM(sum_price_agree)) OVER () as value_percentage,
                        COUNT(DISTINCT winner) as unique_companies
                    FROM public_data.thai_govt_project
                    WHERE dept_name IS NOT NULL
                    GROUP BY dept_name
                )
                SELECT 
                    department,
                    count,
                    total_value,
                    count_percentage,
                    value_percentage,
                    unique_companies,
                    total_value / 1000000 as total_value_millions
                FROM dept_stats
                ORDER BY {} DESC
            """.format(sort_field)
            
            if limit:
                sql += f" LIMIT {limit}"
            
            self._cur.execute(sql)
            results = self._cur.fetchall()
            
            # Convert RealDictRow objects to regular dictionaries
            return [
                {
                    'department': row['department'],
                    'count': row['count'],
                    'total_value': row['total_value'],
                    'count_percentage': row['count_percentage'],
                    'value_percentage': row['value_percentage'],
                    'unique_companies': row['unique_companies'],
                    'total_value_millions': row['total_value_millions']
                }
                for row in results
            ]
            
        except Exception as e:
            logger.error(f"Error getting department summary: {e}")
            raise

    def get_subdepartment_data(self, department: str, limit: Optional[int] = None) -> List[Dict]:
        """Get sub-department data for a specific department"""
        try:
            self.connect()
            sql = """
                WITH dept_totals AS (
                    SELECT 
                        SUM(sum_price_agree) as dept_total_value,
                        COUNT(*) as dept_total_count
                    FROM public_data.thai_govt_project 
                    WHERE dept_name = %s
                ),
                subdept_stats AS (
                    SELECT 
                        dept_sub_name as subdepartment,
                        COUNT(*) as count,
                        SUM(sum_price_agree) as total_value,
                        COUNT(DISTINCT winner) as unique_companies,
                        COUNT(*) * 100.0 / dt.dept_total_count as count_percentage,
                        SUM(sum_price_agree) * 100.0 / dt.dept_total_value as value_percentage
                    FROM public_data.thai_govt_project p, dept_totals dt
                    WHERE dept_name = %s AND dept_sub_name IS NOT NULL
                    GROUP BY dept_sub_name, dt.dept_total_count, dt.dept_total_value
                )
                SELECT 
                    subdepartment,
                    count,
                    total_value,
                    unique_companies,
                    count_percentage,
                    value_percentage,
                    total_value / 1000000 as total_value_millions
                FROM subdept_stats
                ORDER BY count DESC
            """
            
            if limit:
                sql += f" LIMIT {limit}"
            
            self._cur.execute(sql, (department, department))
            results = self._cur.fetchall()
            
            # Convert RealDictRow objects to regular dictionaries
            return [
                {
                    'subdepartment': row['subdepartment'],
                    'count': row['count'],
                    'total_value': row['total_value'],
                    'unique_companies': row['unique_companies'],
                    'count_percentage': row['count_percentage'],
                    'value_percentage': row['value_percentage'],
                    'total_value_millions': row['total_value_millions']
                }
                for row in results
            ]
            
        except Exception as e:
            logger.error(f"Error getting subdepartment data: {e}")
            raise

    def get_projects(self, query: Dict[str, Any], max_documents: int = 10000) -> pd.DataFrame:
        """Fetch projects based on query parameters"""
        try:
            self.connect()
            where_clause, params = self._build_sql_where(query)
            
            sql = """
                SELECT *
                FROM public_data.thai_govt_project
                WHERE 1=1
            """
            
            if where_clause:
                sql += f" AND {where_clause}"
                
            sql += f" LIMIT {max_documents}"
            
            self._cur.execute(sql, params)
            results = self._cur.fetchall()
            
            if not results:
                return pd.DataFrame()
            
            df = pd.DataFrame(results)
            
            # Convert date columns
            date_columns = ['announce_date', 'transaction_date', 'contract_date']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col])
            
            # Convert numeric columns
            numeric_columns = ['sum_price_agree', 'price_build', 'project_money']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching projects: {e}")
            raise

    def _build_sql_where(self, query: Dict[str, Any]) -> tuple[str, list]:
        """Convert MongoDB-style query to SQL WHERE clause"""
        conditions = []
        params = []
        
        if not query:
            return "", []
            
        for key, value in query.items():
            if key == "$and":
                # Handle $and operator
                and_conditions = []
                for condition in value:
                    sub_where, sub_params = self._build_sql_where(condition)
                    if sub_where:
                        and_conditions.append(sub_where)
                        params.extend(sub_params)
                if and_conditions:
                    conditions.append(f"({' AND '.join(and_conditions)})")
            
            elif key == "$or":
                # Handle $or operator
                or_conditions = []
                for condition in value:
                    sub_where, sub_params = self._build_sql_where(condition)
                    if sub_where:
                        or_conditions.append(sub_where)
                        params.extend(sub_params)
                if or_conditions:
                    conditions.append(f"({' OR '.join(or_conditions)})")
            
            elif isinstance(value, dict):
                # Handle operators like $gt, $lt, etc.
                for op, val in value.items():
                    if op == "$regex":
                        conditions.append(f"{key} ~* %s")
                        params.append(val)
                    elif op == "$gte":
                        conditions.append(f"{key} >= %s")
                        params.append(val)
                    elif op == "$lte":
                        conditions.append(f"{key} <= %s")
                        params.append(val)
            else:
                # Simple equality
                conditions.append(f"{key} = %s")
                params.append(value)
        
        return " AND ".join(conditions), params