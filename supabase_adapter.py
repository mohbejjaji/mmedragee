import psycopg2
from psycopg2.extras import DictCursor
from urllib.parse import quote_plus
from sqlalchemy import create_engine

class CursorWrapper:
    def __init__(self, cursor):
        self.cursor = cursor
        self.lastrowid = None
        
    def execute(self, sql, params=()):
        if isinstance(params, (list, tuple)) and '?' in sql:
            # Simple replace '?' to '%s' 
            # Note: handle cases where '?' might be in quotes if it occurs, but typical queries don't have this.
            sql = sql.replace('?', '%s')
        
        self.cursor.execute(sql, params)
        
        if sql.lstrip().upper().startswith("INSERT"):
            try:
                self.cursor.execute("SELECT LASTVAL()")
                last_id = self.cursor.fetchone()[0]
                self.lastrowid = last_id
            except Exception:
                pass
        return self
        
    def fetchall(self): return self.cursor.fetchall()
    def fetchmany(self, size=None): return self.cursor.fetchmany(size)
    def fetchone(self): return self.cursor.fetchone()
    def close(self): self.cursor.close()

    @property
    def description(self):
        return self.cursor.description
        
    def __iter__(self):
        return iter(self.cursor)

class SupabaseAdapter:
    def __init__(self):
        import streamlit as st
        self.dsn = st.secrets["DB_URL"]
        self.pg_conn = psycopg2.connect(self.dsn, cursor_factory=DictCursor)
        self.engine = create_engine(self.dsn)
        self.row_factory = None

    def cursor(self):
        return CursorWrapper(self.pg_conn.cursor())

    def execute(self, sql, params=()):
        c = self.cursor()
        c.execute(sql, params)
        return c

    def commit(self):
        self.pg_conn.commit()

    def rollback(self):
        self.pg_conn.rollback()

    def close(self):
        self.pg_conn.close()
        self.engine.dispose()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
            
    def __getattr__(self, name):
        # Fallback to engine so pandas could theoretically use it, even though pandas does ducktyping
        return getattr(self.engine, name)
