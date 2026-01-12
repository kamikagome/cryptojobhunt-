"""
Unit tests for Job CRUD operations.

=== MENTOR NOTES ===

Testing with Foreign Keys
-------------------------
Jobs reference companies via `company_id`. This means:
1. We must create a company BEFORE creating a job
2. Foreign key constraint will reject invalid company_ids
3. Tests need more setup, but this tests real-world scenarios

Test Independence
-----------------
Each test should be INDEPENDENT - it shouldn't rely on other tests running first.
That's why we create fresh companies in each test that needs one, even though
it seems repetitive. This ensures:
- Tests can run in any order
- One failing test doesn't cascade failures
- Tests are easier to debug in isolation

Testing Edge Cases
------------------
Good tests cover:
- Happy path (normal usage)
- Edge cases (empty lists, null values, boundaries)
- Error cases (invalid data, constraint violations)

===================
"""

import pytest
from src.db.models import Company, Job
from src.db.queries import (
    create_company,
    create_job,
    get_job,
    list_jobs,
    update_job,
)


class TestCreateJob:
    """Tests for the create_job function."""

    def test_create_job_returns_positive_id(self, mock_get_db, sample_company, sample_job):
        """Test that creating a job returns a valid ID."""
        # Arrange - must create company first (foreign key requirement)
        company_id = create_company(sample_company)
        sample_job.company_id = company_id

        # Act
        job_id = create_job(sample_job)

        # Assert
        assert job_id is not None
        assert job_id > 0

    def test_create_job_stores_all_fields(self, mock_get_db, sample_company, sample_job):
        """Test that all job fields are stored correctly."""
        # Arrange
        company_id = create_company(sample_company)
        sample_job.company_id = company_id

        # Act
        job_id = create_job(sample_job)

        # Assert
        saved = get_job(job_id)
        assert saved is not None
        assert saved.company_id == company_id
        assert saved.title == sample_job.title
        assert saved.url == sample_job.url
        assert saved.salary_min == sample_job.salary_min
        assert saved.salary_max == sample_job.salary_max
        assert saved.remote_status == sample_job.remote_status
        assert saved.status == sample_job.status

    def test_create_job_with_minimal_data(self, mock_get_db, sample_company):
        """Test creating a job with only required fields."""
        # Arrange
        company_id = create_company(sample_company)
        job = Job(company_id=company_id, title="Minimal Job")

        # Act
        job_id = create_job(job)

        # Assert
        saved = get_job(job_id)
        assert saved.title == "Minimal Job"
        assert saved.url is None
        assert saved.salary_min is None
        assert saved.status == "open"  # Default value

    def test_create_job_invalid_company_raises_error(self, mock_get_db, sample_job):
        """
        Test that creating a job with invalid company_id fails.

        This tests the FOREIGN KEY constraint - the database should
        reject references to non-existent companies.
        """
        # Arrange - set an invalid company_id
        sample_job.company_id = 99999

        # Act & Assert
        import sqlite3
        with pytest.raises(sqlite3.IntegrityError):
            create_job(sample_job)

    def test_create_duplicate_url_raises_error(self, mock_get_db, sample_company, sample_job):
        """Test that duplicate job URLs are rejected."""
        # Arrange
        company_id = create_company(sample_company)
        sample_job.company_id = company_id
        create_job(sample_job)

        # Act & Assert - same URL should fail
        duplicate_job = Job(
            company_id=company_id,
            title="Different Title",
            url=sample_job.url  # Same URL
        )
        import sqlite3
        with pytest.raises(sqlite3.IntegrityError):
            create_job(duplicate_job)


class TestGetJob:
    """Tests for the get_job function."""

    def test_get_job_returns_correct_job(self, mock_get_db, sample_company, sample_job):
        """Test that get_job returns the right job by ID."""
        # Arrange
        company_id = create_company(sample_company)
        sample_job.company_id = company_id
        job_id = create_job(sample_job)

        # Act
        result = get_job(job_id)

        # Assert
        assert result is not None
        assert result.id == job_id
        assert result.title == sample_job.title

    def test_get_job_not_found_returns_none(self, mock_get_db):
        """Test that get_job returns None for non-existent ID."""
        # Act
        result = get_job(99999)

        # Assert
        assert result is None


class TestListJobs:
    """Tests for the list_jobs function."""

    def test_list_jobs_empty_database(self, mock_get_db):
        """Test that list_jobs returns empty list when no jobs exist."""
        # Act
        result = list_jobs()

        # Assert
        assert result == []

    def test_list_jobs_returns_all(self, mock_get_db, sample_company):
        """Test that list_jobs returns all created jobs."""
        # Arrange
        company_id = create_company(sample_company)
        jobs = [
            Job(company_id=company_id, title="Job 1", url="https://example.com/1"),
            Job(company_id=company_id, title="Job 2", url="https://example.com/2"),
            Job(company_id=company_id, title="Job 3", url="https://example.com/3"),
        ]
        for j in jobs:
            create_job(j)

        # Act
        result = list_jobs()

        # Assert
        assert len(result) == 3

    def test_list_jobs_filter_by_status(self, mock_get_db, sample_company):
        """
        Test that list_jobs can filter by status.

        This tests the optional parameter behavior.
        """
        # Arrange
        company_id = create_company(sample_company)
        create_job(Job(company_id=company_id, title="Open Job", status="open", url="https://a.com"))
        create_job(Job(company_id=company_id, title="Closed Job", status="closed", url="https://b.com"))
        create_job(Job(company_id=company_id, title="Another Open", status="open", url="https://c.com"))

        # Act
        open_jobs = list_jobs(status="open")
        closed_jobs = list_jobs(status="closed")

        # Assert
        assert len(open_jobs) == 2
        assert len(closed_jobs) == 1
        assert all(j.status == "open" for j in open_jobs)
        assert all(j.status == "closed" for j in closed_jobs)


class TestUpdateJob:
    """Tests for the update_job function."""

    def test_update_job_changes_fields(self, mock_get_db, sample_company, sample_job):
        """Test that update_job modifies the job correctly."""
        # Arrange
        company_id = create_company(sample_company)
        sample_job.company_id = company_id
        job_id = create_job(sample_job)
        job = get_job(job_id)

        # Act - modify and update
        job.status = "closed"
        job.salary_max = 250000
        job.notes = "Position filled"
        update_job(job)

        # Assert
        updated = get_job(job_id)
        assert updated.status == "closed"
        assert updated.salary_max == 250000
        assert updated.notes == "Position filled"
        # Original fields unchanged
        assert updated.title == sample_job.title

    def test_update_job_salary_range(self, mock_get_db, sample_company):
        """Test updating salary range from None to values."""
        # Arrange
        company_id = create_company(sample_company)
        job = Job(company_id=company_id, title="No Salary Job")
        job_id = create_job(job)

        # Act
        saved_job = get_job(job_id)
        saved_job.salary_min = 100000
        saved_job.salary_max = 150000
        update_job(saved_job)

        # Assert
        updated = get_job(job_id)
        assert updated.salary_min == 100000
        assert updated.salary_max == 150000
