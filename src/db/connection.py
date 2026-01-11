"""Database connection and initialization utilities."""

import sqlite3
from pathlib import Path

# Default database path (project root)
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "crypto_jobs.db"

# Path to SQL files
SQL_DIR = Path(__file__).parent


def get_db(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """
    Get a database connection with row factory enabled.

    Returns rows as sqlite3.Row objects, which allow both
    index-based and name-based access to columns.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # Enable foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    """
    Initialize the database by running schema.sql and seed.sql.

    Safe to run multiple times - uses IF NOT EXISTS and INSERT OR IGNORE.
    """
    conn = get_db(db_path)

    # Read and execute schema
    schema_path = SQL_DIR / "schema.sql"
    with open(schema_path, "r") as f:
        conn.executescript(f.read())

    # Read and execute seed data
    seed_path = SQL_DIR / "seed.sql"
    with open(seed_path, "r") as f:
        conn.executescript(f.read())

    conn.commit()
    conn.close()

    print(f"Database initialized at: {db_path}")
