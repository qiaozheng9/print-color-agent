"""Database connection management and initialization."""

import os
import sqlite3
from pathlib import Path


def get_db_path() -> Path:
    """Resolve database path from environment variable with default."""
    db_name = os.getenv("DB_PATH", "data.db")
    return Path(db_name)


def get_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite database.

    Enables WAL mode, foreign keys, and returns Row factory for dict-like access.
    """
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA encoding='UTF-8'")
    return conn


def init_db() -> None:
    """Execute schema.sql to create all tables if they do not exist."""
    schema_path = Path(__file__).parent / "schema.sql"
    conn = get_connection()
    try:
        conn.executescript(schema_path.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()
