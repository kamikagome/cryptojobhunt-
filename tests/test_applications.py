"""
Unit tests for Application CRUD operations.

=== MENTOR NOTES ===

Multi-Level Dependencies
------------------------
Applications have a chain of dependencies:
  Application → Job → Company

To create an Application, you need:
1. A Company (for the Job's foreign key)
2. A Job (for the Application's foreign key)
3. Then the Application

This models real-world data relationships and shows why
good test setup is important.

Testing Boolean Fields
----------------------
SQLite stores booleans as integers (0/1). Our code converts them:
- On save: True → 1, False → 0
- On load: 1 → True, 0 → False

We test both directions to ensure the conversion works correctly.

Helper Functions in Tests
-------------------------
When setup becomes repetitive, you can create helper functions
within the test file. This keeps tests readable without bloating
the conftest.py with very specific fixtures.

===================
"""

import pytest
from src.db.models import Application, Company, Job
from src.db.queries import (
    create_application,
    create_company,
    create_job,
    get_application,
    list_applications,
    update_application,
)


def create_test_job(mock_db) -> int:
    """
    Helper function to create a company and job for testing.

    Returns the job_id so tests can create applications.

    This is a "test helper" - not a fixture, just a regular function
    that reduces repetition in tests.
    """
    company = Company(name="Test Company")
    company_id = create_company(company)

    job = Job(company_id=company_id, title="Test Job")
    job_id = create_job(job)

    return job_id


class TestCreateApplication:
    """Tests for the create_application function."""

    def test_create_application_returns_positive_id(self, mock_get_db, sample_application):
        """Test that creating an application returns a valid ID."""
        # Arrange
        job_id = create_test_job(mock_get_db)
        sample_application.job_id = job_id

        # Act
        app_id = create_application(sample_application)

        # Assert
        assert app_id is not None
        assert app_id > 0

    def test_create_application_stores_all_fields(self, mock_get_db, sample_application):
        """Test that all application fields are stored correctly."""
        # Arrange
        job_id = create_test_job(mock_get_db)
        sample_application.job_id = job_id

        # Act
        app_id = create_application(sample_application)

        # Assert
        saved = get_application(app_id)
        assert saved is not None
        assert saved.job_id == job_id
        assert saved.date_applied == sample_application.date_applied
        assert saved.resume_version == sample_application.resume_version
        assert saved.status == sample_application.status
        assert saved.notes == sample_application.notes

    def test_create_application_boolean_conversion(self, mock_get_db):
        """
        Test that boolean cover_letter_sent is stored and retrieved correctly.

        This tests the Python bool ↔ SQLite integer conversion.
        """
        # Arrange
        job_id = create_test_job(mock_get_db)

        # Test True
        app_with_cover = Application(
            job_id=job_id,
            cover_letter_sent=True,
            status="applied"
        )
        app_id_with = create_application(app_with_cover)

        # Test False
        app_without_cover = Application(
            job_id=job_id,
            cover_letter_sent=False,
            status="applied"
        )
        app_id_without = create_application(app_without_cover)

        # Assert
        saved_with = get_application(app_id_with)
        saved_without = get_application(app_id_without)

        assert saved_with.cover_letter_sent is True
        assert saved_without.cover_letter_sent is False
        # Verify they're actual booleans, not integers
        assert isinstance(saved_with.cover_letter_sent, bool)
        assert isinstance(saved_without.cover_letter_sent, bool)

    def test_create_application_invalid_job_raises_error(self, mock_get_db, sample_application):
        """Test that creating an application with invalid job_id fails."""
        # Arrange
        sample_application.job_id = 99999

        # Act & Assert
        import sqlite3
        with pytest.raises(sqlite3.IntegrityError):
            create_application(sample_application)


class TestGetApplication:
    """Tests for the get_application function."""

    def test_get_application_returns_correct_application(self, mock_get_db, sample_application):
        """Test that get_application returns the right application by ID."""
        # Arrange
        job_id = create_test_job(mock_get_db)
        sample_application.job_id = job_id
        app_id = create_application(sample_application)

        # Act
        result = get_application(app_id)

        # Assert
        assert result is not None
        assert result.id == app_id
        assert result.job_id == job_id

    def test_get_application_not_found_returns_none(self, mock_get_db):
        """Test that get_application returns None for non-existent ID."""
        # Act
        result = get_application(99999)

        # Assert
        assert result is None


class TestListApplications:
    """Tests for the list_applications function."""

    def test_list_applications_empty_database(self, mock_get_db):
        """Test that list_applications returns empty list when no applications exist."""
        # Act
        result = list_applications()

        # Assert
        assert result == []

    def test_list_applications_returns_all(self, mock_get_db):
        """Test that list_applications returns all created applications."""
        # Arrange
        job_id = create_test_job(mock_get_db)
        for i in range(3):
            app = Application(job_id=job_id, status="applied", resume_version=f"v{i}")
            create_application(app)

        # Act
        result = list_applications()

        # Assert
        assert len(result) == 3

    def test_list_applications_filter_by_status(self, mock_get_db):
        """Test that list_applications can filter by status."""
        # Arrange
        job_id = create_test_job(mock_get_db)
        create_application(Application(job_id=job_id, status="applied"))
        create_application(Application(job_id=job_id, status="interview"))
        create_application(Application(job_id=job_id, status="applied"))
        create_application(Application(job_id=job_id, status="rejected"))

        # Act
        applied = list_applications(status="applied")
        interview = list_applications(status="interview")
        rejected = list_applications(status="rejected")

        # Assert
        assert len(applied) == 2
        assert len(interview) == 1
        assert len(rejected) == 1


class TestUpdateApplication:
    """Tests for the update_application function."""

    def test_update_application_changes_status(self, mock_get_db, sample_application):
        """
        Test the typical workflow of updating application status.

        This tests a real-world scenario: application goes through
        different stages (applied → interview → offer).
        """
        # Arrange
        job_id = create_test_job(mock_get_db)
        sample_application.job_id = job_id
        app_id = create_application(sample_application)

        # Act - progress through stages
        app = get_application(app_id)
        app.status = "screening"
        update_application(app)

        app = get_application(app_id)
        app.status = "interview"
        update_application(app)

        # Assert
        final = get_application(app_id)
        assert final.status == "interview"

    def test_update_application_changes_boolean(self, mock_get_db):
        """Test updating the cover_letter_sent boolean field."""
        # Arrange
        job_id = create_test_job(mock_get_db)
        app = Application(job_id=job_id, cover_letter_sent=False)
        app_id = create_application(app)

        # Act - update boolean field
        saved_app = get_application(app_id)
        saved_app.cover_letter_sent = True
        update_application(saved_app)

        # Assert
        updated = get_application(app_id)
        assert updated.cover_letter_sent is True
