"""
Pytest configuration and fixtures for the crypto jobs database tests.

=== MENTOR NOTES ===

What is conftest.py?
--------------------
This is a special file that pytest automatically discovers. Any fixtures defined
here are available to ALL test files in this directory and subdirectories.

What is a Fixture?
------------------
A fixture is a function that provides test data or setup. It runs BEFORE each
test that requests it. This follows the "Arrange-Act-Assert" pattern:
  - Arrange: Set up test data (fixtures do this)
  - Act: Run the code being tested
  - Assert: Check the results

Why use a temporary database?
-----------------------------
Using a temporary file database for each test. Benefits:
  1. Isolated - each test gets a clean database
  2. Safe - never touches your real data
  3. Supports the open/close pattern in queries.py

The Challenge: Connection Management
------------------------------------
The original queries.py opens and closes a connection for each operation:
    conn = get_db()
    # ... do stuff ...
    conn.close()

SOLUTION: Create a temporary database file for each test, and mock
get_db() to point to that file instead of the real database.

===================
"""

import os
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


# Path to the SQL files in your project
SQL_DIR = Path(__file__).parent.parent / "src" / "db"


@pytest.fixture
def test_db_path():
    """
    Create a temporary database file for each test.

    This fixture creates a unique temporary file that will be
    automatically cleaned up after the test completes.
    """
    # Create a temporary file
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)  # Close the file descriptor, we'll use sqlite to access it

    yield Path(db_path)

    # Cleanup: remove the temporary file
    try:
        os.unlink(db_path)
    except OSError:
        pass  # File might already be deleted


@pytest.fixture
def db_connection(test_db_path):
    """
    Create a fresh database for each test.

    This fixture:
    1. Creates a new SQLite database in a temp file
    2. Runs the schema.sql to create tables
    3. Runs seed.sql to add initial skills data
    4. Yields the connection to the test
    5. Closes the connection after the test finishes
    """
    # Create database connection
    conn = sqlite3.connect(test_db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    # Load and execute schema
    schema_path = SQL_DIR / "schema.sql"
    with open(schema_path, "r") as f:
        conn.executescript(f.read())

    # Load and execute seed data (skills)
    seed_path = SQL_DIR / "seed.sql"
    with open(seed_path, "r") as f:
        conn.executescript(f.read())

    conn.commit()

    yield conn

    conn.close()


def make_get_db_factory(db_path):
    """
    Factory function that creates a get_db replacement.

    This returns a function that behaves like the real get_db(),
    but connects to our test database instead.
    """
    def test_get_db():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    return test_get_db


@pytest.fixture
def mock_get_db(db_connection, test_db_path):
    """
    Mock the get_db function to return connections to our test database.

    WHY DO WE NEED THIS?
    --------------------
    The queries.py functions call `get_db()` to get a database connection.
    By default, get_db() connects to the real `crypto_jobs.db` file.

    We need to intercept those calls and return our test database instead.
    This is called "mocking" or "patching".

    HOW IT WORKS:
    -------------
    1. db_connection fixture creates and initializes the test database
    2. We create a factory function that returns connections to that database
    3. patch() replaces get_db with our factory
    4. Each query.py function gets a fresh connection to our test database
    5. The data persists because all connections point to the same file

    Usage in tests:
        def test_create_company(mock_get_db):
            # Now any code that calls get_db() will get the test database
            company_id = create_company(Company(name="Test"))
    """
    test_get_db = make_get_db_factory(test_db_path)

    with patch("src.db.queries.get_db", side_effect=test_get_db):
        yield db_connection


@pytest.fixture
def sample_company():
    """
    Provide a sample Company object for tests.

    Fixtures can return any Python object. This is a "data fixture" -
    it just provides test data rather than doing setup.
    """
    from src.db.models import Company
    return Company(
        name="Uniswap Labs",
        website="https://uniswap.org",
        sector="DeFi",
        chain_focus="Ethereum",
        size="medium",
        notes="Leading DEX"
    )


@pytest.fixture
def sample_job(sample_company):
    """
    Provide a sample Job object for tests.

    FIXTURE DEPENDENCY:
    Notice this fixture takes `sample_company` as a parameter.
    Pytest automatically runs sample_company first and passes its result here.
    This is called "fixture composition" - fixtures can depend on other fixtures.
    """
    from src.db.models import Job
    return Job(
        company_id=1,  # Will be set after company is created
        title="Senior SQL Developer",
        url="https://uniswap.org/jobs/sql-dev",
        salary_min=150000,
        salary_max=200000,
        remote_status="remote",
        date_posted="2024-01-15",
        status="open",
        source="careers page",
        notes="Great opportunity"
    )


@pytest.fixture
def sample_application():
    """Provide a sample Application object for tests."""
    from src.db.models import Application
    return Application(
        job_id=1,  # Will be set after job is created
        date_applied="2024-01-20",
        resume_version="v2.1",
        cover_letter_sent=True,
        status="applied",
        notes="Applied via website"
    )


@pytest.fixture
def sample_interview():
    """Provide a sample Interview object for tests."""
    from src.db.models import Interview
    return Interview(
        application_id=1,  # Will be set after application is created
        scheduled_at="2024-01-25 10:00:00",
        type="technical",
        notes="SQL coding challenge",
        outcome="pending"
    )


@pytest.fixture
def sample_skill():
    """Provide a sample Skill object for tests."""
    from src.db.models import Skill
    return Skill(
        name="dbt",
        category="SQL"
    )


@pytest.fixture
def sample_discovered_job():
    """Provide a sample DiscoveredJob object for tests."""
    from src.db.models import DiscoveredJob
    return DiscoveredJob(
        title="Data Engineer",
        company_name="Chainlink",
        url="https://chainlink.com/jobs/data-eng",
        requirements_raw="SQL, Python, Airflow",
        source="perplexity",
        raw_response='{"jobs": [...]}',
        status="pending"
    )
