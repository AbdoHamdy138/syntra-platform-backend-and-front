import psycopg
from psycopg.rows import dict_row
from contextlib import contextmanager
from typing import Generator, Any, List, Optional, Dict
from app.config import settings

@contextmanager
def get_db_connection() -> Generator[psycopg.Connection, None, None]:
    conn = psycopg.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        dbname=settings.DB_NAME,
        autocommit=True
    )
    try:
        yield conn
    finally:
        conn.close()

def query_all(sql: str, params: Optional[List[Any] | tuple] = None) -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()

def query_one(sql: str, params: Optional[List[Any] | tuple] = None) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params or ())
            return cur.fetchone()

def execute(sql: str, params: Optional[List[Any] | tuple] = None) -> int:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.rowcount

