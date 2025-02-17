# src/services/database/postgres.py

import os
import logging
from typing import Optional, Dict, Any, List
import pandas as pd
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
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
    """Service class for PostgreSQL operations with connection pooling"""
    
    _instance = None
    _pool = None
    
    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the service and connection pool"""
        load_dotenv(override=True)
        self.db_params = {
            'dbname': os.getenv('POSTGRES_DB', 'projects'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', '5432')
        }
        self.table_name = os.getenv('POSTGRES_TABLE', 'public_data.thai_govt_project')
        self._setup_connection_pool()

    def _setup_connection_pool(self, minconn=1, maxconn=10):
        """Set up the connection pool"""
        if self._pool is None:
            try:
                self._pool = SimpleConnectionPool(
                    minconn,
                    maxconn,
                    **self.db_params
                )
                logger.info("Connection pool established")
            except Exception as e:
                logger.error(f"Error setting up connection pool: {e}")
                raise

    @contextmanager
    def get_connection(self):
        """Context manager for getting a connection from the pool"""
        conn = None
        try:
            conn = self._pool.getconn()
            conn.autocommit = True
            yield conn
        finally:
            if conn:
                self._pool.putconn(conn)

    @retry_on_connection_error()
    def get_department_summary(self, view_by: str = "count", limit: Optional[int] = None) -> List[Dict]:
        """Get department summary with sorting and pre-calculated metrics"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    sort_field = "count" if view_by == "count" else "total_value"
                    
                    sql = f"""
                        WITH dept_stats AS (
                            SELECT 
                                dept_name as department,
                                COUNT(*) as count,
                                SUM(sum_price_agree) as total_value,
                                COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as count_percentage,
                                SUM(sum_price_agree) * 100.0 / SUM(SUM(sum_price_agree)) OVER () as value_percentage,
                                COUNT(DISTINCT winner) as unique_companies
                            FROM {self.table_name}
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
                        ORDER BY {sort_field} DESC
                    """
                    
                    if limit:
                        sql += f" LIMIT {limit}"
                    
                    cur.execute(sql)
                    results = cur.fetchall()
                    
                    return [dict(row) for row in results]
                    
        except Exception as e:
            logger.error(f"Error getting department summary: {e}")
            raise

    @retry_on_connection_error()
    def get_subdepartment_data(self, department: str, limit: Optional[int] = None) -> List[Dict]:
        """Get sub-department data for a specific department"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    sql = f"""
                        WITH dept_totals AS (
                            SELECT 
                                SUM(sum_price_agree) as dept_total_value,
                                COUNT(*) as dept_total_count
                            FROM {self.table_name}
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
                            FROM {self.table_name} p, dept_totals dt
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
                    
                    cur.execute(sql, (department, department))
                    results = cur.fetchall()
                    
                    return [dict(row) for row in results]
                    
        except Exception as e:
            logger.error(f"Error getting subdepartment data: {e}")
            raise

    def cleanup(self):
        """Clean up connections and close the pool"""
        if self._pool:
            self._pool.closeall()
            logger.info("Connection pool closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()