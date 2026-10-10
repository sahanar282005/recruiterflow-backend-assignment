"""Database connection and initialization module using Python's built-in sqlite3."""

import os
import sqlite3
from typing import Optional

# Path to the default SQLite database file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "recruiter.db"))
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")


def get_db_path(custom_path: Optional[str] = None) -> str:
    """Return the active database file path."""
    return custom_path or DEFAULT_DB_PATH


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Create and return a configured sqlite3 connection.
    
    Configured with sqlite3.Row for dictionary-like column access
    and foreign key enforcement enabled.
    """
    path = get_db_path(db_path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Execute schema.sql using raw handwritten DDL to initialize tables."""
    path = get_db_path(db_path)
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = get_db_connection(path)
    try:
        with conn:
            conn.executescript(schema_sql)
    finally:
        conn.close()
