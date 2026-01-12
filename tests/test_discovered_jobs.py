"""
Unit tests for DiscoveredJob operations.

=== MENTOR NOTES ===

What are Discovered Jobs?
-------------------------
The discovered_jobs table is a "staging area" for jobs found via the
Perplexity API. Jobs go through this workflow:

  API Response → discovered_jobs (pending)
                       ↓
        User reviews and either:
        - Promotes to main jobs table
        - Dismisses (marks as not interested)

Testing Status Transitions
--------------------------
Unlike other entities, DiscoveredJobs have a specific lifecycle:
  pending → promoted (moved to jobs table)
          → dismissed (not interested)
          → saved (keeping for later)

We test these transitions to ensure the workflow works correctly.

URL Deduplication
-----------------
Both discovered_jobs and jobs use URL as a unique key to prevent
duplicates. We test both:
- discovered_job_exists() - checks discovered_jobs table
- job_url_exists() - checks jobs table

===================
"""

import pytest
from src.db.models import Company, DiscoveredJob, Job
from src.db.queries import (
    create_company,
    create_discovered_job,
    create_job,
    discovered_job_exists,
    get_discovered_job,
    job_url_exists,
    list_discovered_jobs,
    update_discovered_job_status,
)


class TestCreateDiscoveredJob:
    """Tests for the create_discovered_job function."""

    def test_create_discovered_job_returns_id(self, mock_get_db, sample_discovered_job):
        """Test that creating a discovered job returns a valid ID."""
        # Act
        job_id = create_discovered_job(sample_discovered_job)

        # Assert
        assert job_id is not None
        assert job_id > 0

    def test_create_discovered_job_stores_all_fields(self, mock_get_db, sample_discovered_job):
        """Test that all discovered job fields are stored correctly."""
        # Act
        job_id = create_discovered_job(sample_discovered_job)

        # Assert
        saved = get_discovered_job(job_id)
        assert saved is not None
        assert saved.title == sample_discovered_job.title
        assert saved.company_name == sample_discovered_job.company_name
        assert saved.url == sample_discovered_job.url
        assert saved.requirements_raw == sample_discovered_job.requirements_raw
        assert saved.source == sample_discovered_job.source
        assert saved.raw_response == sample_discovered_job.raw_response
        assert saved.status == "pending"  # Default status

    def test_create_discovered_job_with_minimal_data(self, mock_get_db):
        """Test creating a discovered job with minimal data."""
        # Arrange
        job = DiscoveredJob(
            title="Minimal Job",
            url="https://example.com/minimal"
        )

        # Act
        job_id = create_discovered_job(job)

        # Assert
        saved = get_discovered_job(job_id)
        assert saved.title == "Minimal Job"
        assert saved.company_name is None
        assert saved.status == "pending"

    def test_create_duplicate_url_raises_error(self, mock_get_db, sample_discovered_job):
        """Test that duplicate URLs are rejected."""
        # Arrange
        create_discovered_job(sample_discovered_job)

        # Act & Assert
        import sqlite3
        with pytest.raises(sqlite3.IntegrityError):
            create_discovered_job(sample_discovered_job)


class TestGetDiscoveredJob:
    """Tests for the get_discovered_job function."""

    def test_get_discovered_job_returns_correct_job(self, mock_get_db, sample_discovered_job):
        """Test that get_discovered_job returns the right job by ID."""
        # Arrange
        job_id = create_discovered_job(sample_discovered_job)

        # Act
        result = get_discovered_job(job_id)

        # Assert
        assert result is not None
        assert result.id == job_id
        assert result.title == sample_discovered_job.title

    def test_get_discovered_job_not_found_returns_none(self, mock_get_db):
        """Test that get_discovered_job returns None for non-existent ID."""
        # Act
        result = get_discovered_job(99999)

        # Assert
        assert result is None


class TestListDiscoveredJobs:
    """Tests for the list_discovered_jobs function."""

    def test_list_discovered_jobs_empty(self, mock_get_db):
        """Test that list_discovered_jobs returns empty list when none exist."""
        # Act
        result = list_discovered_jobs()

        # Assert
        assert result == []

    def test_list_discovered_jobs_returns_all(self, mock_get_db):
        """Test that list_discovered_jobs returns all discovered jobs."""
        # Arrange
        jobs = [
            DiscoveredJob(title="Job 1", url="https://example.com/1"),
            DiscoveredJob(title="Job 2", url="https://example.com/2"),
            DiscoveredJob(title="Job 3", url="https://example.com/3"),
        ]
        for j in jobs:
            create_discovered_job(j)

        # Act
        result = list_discovered_jobs()

        # Assert
        assert len(result) == 3

    def test_list_discovered_jobs_filter_by_status(self, mock_get_db):
        """Test filtering discovered jobs by status."""
        # Arrange - create a real job for the promoted_to_job_id FK
        company = Company(name="Filter Test Company")
        company_id = create_company(company)
        real_job = Job(company_id=company_id, title="Real Job")
        real_job_id = create_job(real_job)

        job1_id = create_discovered_job(DiscoveredJob(title="Job 1", url="https://a.com"))
        job2_id = create_discovered_job(DiscoveredJob(title="Job 2", url="https://b.com"))
        job3_id = create_discovered_job(DiscoveredJob(title="Job 3", url="https://c.com"))

        # Update statuses
        update_discovered_job_status(job2_id, "dismissed")
        update_discovered_job_status(job3_id, "promoted", promoted_to_job_id=real_job_id)

        # Act
        pending = list_discovered_jobs(status="pending")
        dismissed = list_discovered_jobs(status="dismissed")
        promoted = list_discovered_jobs(status="promoted")

        # Assert
        assert len(pending) == 1
        assert len(dismissed) == 1
        assert len(promoted) == 1


class TestUpdateDiscoveredJobStatus:
    """Tests for the update_discovered_job_status function."""

    def test_update_status_to_dismissed(self, mock_get_db, sample_discovered_job):
        """Test dismissing a discovered job."""
        # Arrange
        job_id = create_discovered_job(sample_discovered_job)

        # Act
        update_discovered_job_status(job_id, "dismissed")

        # Assert
        updated = get_discovered_job(job_id)
        assert updated.status == "dismissed"
        assert updated.promoted_to_job_id is None

    def test_update_status_to_promoted(self, mock_get_db, sample_discovered_job):
        """
        Test promoting a discovered job.

        When promoted, we also record which job it was promoted to
        (the promoted_to_job_id foreign key).
        """
        # Arrange
        disc_job_id = create_discovered_job(sample_discovered_job)

        # Create the actual job it would be promoted to
        company = Company(name=sample_discovered_job.company_name)
        company_id = create_company(company)
        job = Job(company_id=company_id, title=sample_discovered_job.title)
        real_job_id = create_job(job)

        # Act
        update_discovered_job_status(disc_job_id, "promoted", promoted_to_job_id=real_job_id)

        # Assert
        updated = get_discovered_job(disc_job_id)
        assert updated.status == "promoted"
        assert updated.promoted_to_job_id == real_job_id

    def test_update_status_to_saved(self, mock_get_db, sample_discovered_job):
        """Test saving a discovered job for later review."""
        # Arrange
        job_id = create_discovered_job(sample_discovered_job)

        # Act
        update_discovered_job_status(job_id, "saved")

        # Assert
        updated = get_discovered_job(job_id)
        assert updated.status == "saved"


class TestURLExistenceChecks:
    """Tests for URL deduplication functions."""

    def test_discovered_job_exists_true(self, mock_get_db, sample_discovered_job):
        """Test that discovered_job_exists returns True for existing URL."""
        # Arrange
        create_discovered_job(sample_discovered_job)

        # Act
        result = discovered_job_exists(sample_discovered_job.url)

        # Assert
        assert result is True

    def test_discovered_job_exists_false(self, mock_get_db):
        """Test that discovered_job_exists returns False for non-existing URL."""
        # Act
        result = discovered_job_exists("https://nonexistent.com/job")

        # Assert
        assert result is False

    def test_job_url_exists_true(self, mock_get_db):
        """Test that job_url_exists returns True for existing URL in jobs table."""
        # Arrange
        company = Company(name="URL Test Company")
        company_id = create_company(company)
        job = Job(
            company_id=company_id,
            title="URL Test Job",
            url="https://example.com/real-job"
        )
        create_job(job)

        # Act
        result = job_url_exists("https://example.com/real-job")

        # Assert
        assert result is True

    def test_job_url_exists_false(self, mock_get_db):
        """Test that job_url_exists returns False for non-existing URL."""
        # Act
        result = job_url_exists("https://nonexistent.com/job")

        # Assert
        assert result is False

    def test_url_checks_are_independent(self, mock_get_db, sample_discovered_job):
        """
        Test that discovered_jobs and jobs URLs are checked separately.

        A URL in discovered_jobs should not affect job_url_exists, and vice versa.
        """
        # Arrange - create a discovered job
        create_discovered_job(sample_discovered_job)

        # Act & Assert - URL exists in discovered, not in jobs
        assert discovered_job_exists(sample_discovered_job.url) is True
        assert job_url_exists(sample_discovered_job.url) is False

        # Now create a real job with different URL
        company = Company(name="Real Company")
        company_id = create_company(company)
        job = Job(company_id=company_id, title="Real Job", url="https://real.com/job")
        create_job(job)

        # Assert - URL exists in jobs, not in discovered
        assert job_url_exists("https://real.com/job") is True
        assert discovered_job_exists("https://real.com/job") is False
