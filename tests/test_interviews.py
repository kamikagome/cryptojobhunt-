"""
Unit tests for Interview CRUD operations.

=== MENTOR NOTES ===

The Full Dependency Chain
-------------------------
Interviews have the deepest dependency chain:
  Interview → Application → Job → Company

This requires 4 database inserts before we can test interviews!
That's why we use helper functions to hide this complexity.

Testing Datetime Strings
------------------------
SQLite stores datetimes as TEXT. We test that:
- Datetime strings are stored exactly as provided
- The format is preserved through save/load cycles

Test Organization
-----------------
Notice how each test file follows the same pattern:
- TestCreate* - tests for creating records
- TestGet* - tests for reading single records
- TestList* - tests for reading multiple records
- TestUpdate* - tests for modifying records

This consistency makes the test suite easy to navigate.

===================
"""

import uuid

import pytest

from src.db.models import Application, Company, Interview, Job
from src.db.queries import (
    create_application,
    create_company,
    create_interview,
    create_job,
    get_interview,
    list_interviews,
    update_interview,
)


def create_test_application(mock_db) -> int:
    """
    Helper function to create the full chain: Company → Job → Application.

    Returns the application_id so tests can create interviews.

    NOTE: We use uuid to generate unique names because some tests
    call this helper multiple times, and company names must be unique.
    """
    unique_id = str(uuid.uuid4())[:8]
    company = Company(name=f"Test Interview Company {unique_id}")
    company_id = create_company(company)

    job = Job(company_id=company_id, title="Test Interview Job")
    job_id = create_job(job)

    application = Application(job_id=job_id, status="interview")
    app_id = create_application(application)

    return app_id


class TestCreateInterview:
    """Tests for the create_interview function."""

    def test_create_interview_returns_positive_id(self, mock_get_db, sample_interview):
        """Test that creating an interview returns a valid ID."""
        # Arrange
        app_id = create_test_application(mock_get_db)
        sample_interview.application_id = app_id

        # Act
        interview_id = create_interview(sample_interview)

        # Assert
        assert interview_id is not None
        assert interview_id > 0

    def test_create_interview_stores_all_fields(self, mock_get_db, sample_interview):
        """Test that all interview fields are stored correctly."""
        # Arrange
        app_id = create_test_application(mock_get_db)
        sample_interview.application_id = app_id

        # Act
        interview_id = create_interview(sample_interview)

        # Assert
        saved = get_interview(interview_id)
        assert saved is not None
        assert saved.application_id == app_id
        assert saved.scheduled_at == sample_interview.scheduled_at
        assert saved.type == sample_interview.type
        assert saved.notes == sample_interview.notes
        assert saved.outcome == sample_interview.outcome

    def test_create_interview_with_minimal_data(self, mock_get_db):
        """Test creating an interview with only required fields."""
        # Arrange
        app_id = create_test_application(mock_get_db)
        interview = Interview(application_id=app_id)

        # Act
        interview_id = create_interview(interview)

        # Assert
        saved = get_interview(interview_id)
        assert saved.application_id == app_id
        assert saved.scheduled_at is None
        assert saved.type is None
        assert saved.outcome is None

    def test_create_interview_invalid_application_raises_error(self, mock_get_db, sample_interview):
        """Test that creating an interview with invalid application_id fails."""
        # Arrange
        sample_interview.application_id = 99999

        # Act & Assert
        import sqlite3
        with pytest.raises(sqlite3.IntegrityError):
            create_interview(sample_interview)


class TestGetInterview:
    """Tests for the get_interview function."""

    def test_get_interview_returns_correct_interview(self, mock_get_db, sample_interview):
        """Test that get_interview returns the right interview by ID."""
        # Arrange
        app_id = create_test_application(mock_get_db)
        sample_interview.application_id = app_id
        interview_id = create_interview(sample_interview)

        # Act
        result = get_interview(interview_id)

        # Assert
        assert result is not None
        assert result.id == interview_id
        assert result.type == sample_interview.type

    def test_get_interview_not_found_returns_none(self, mock_get_db):
        """Test that get_interview returns None for non-existent ID."""
        # Act
        result = get_interview(99999)

        # Assert
        assert result is None


class TestListInterviews:
    """Tests for the list_interviews function."""

    def test_list_interviews_empty_database(self, mock_get_db):
        """Test that list_interviews returns empty list when no interviews exist."""
        # Act
        result = list_interviews()

        # Assert
        assert result == []

    def test_list_interviews_returns_all(self, mock_get_db):
        """Test that list_interviews returns all created interviews."""
        # Arrange
        app_id = create_test_application(mock_get_db)
        interview_types = ["recruiter", "technical", "culture"]
        for itype in interview_types:
            interview = Interview(application_id=app_id, type=itype)
            create_interview(interview)

        # Act
        result = list_interviews()

        # Assert
        assert len(result) == 3

    def test_list_interviews_filter_by_application(self, mock_get_db):
        """
        Test that list_interviews can filter by application_id.

        This is useful when viewing all interviews for a specific application.
        """
        # Arrange - create two applications with different interviews
        app_id_1 = create_test_application(mock_get_db)
        app_id_2 = create_test_application(mock_get_db)

        # App 1 has 2 interviews
        create_interview(Interview(application_id=app_id_1, type="recruiter"))
        create_interview(Interview(application_id=app_id_1, type="technical"))

        # App 2 has 1 interview
        create_interview(Interview(application_id=app_id_2, type="final"))

        # Act
        app1_interviews = list_interviews(application_id=app_id_1)
        app2_interviews = list_interviews(application_id=app_id_2)
        all_interviews = list_interviews()

        # Assert
        assert len(app1_interviews) == 2
        assert len(app2_interviews) == 1
        assert len(all_interviews) == 3


class TestUpdateInterview:
    """Tests for the update_interview function."""

    def test_update_interview_changes_outcome(self, mock_get_db, sample_interview):
        """
        Test updating interview outcome.

        This is the typical workflow: interview is scheduled (pending),
        then updated with the outcome (passed/failed).
        """
        # Arrange
        app_id = create_test_application(mock_get_db)
        sample_interview.application_id = app_id
        sample_interview.outcome = "pending"
        interview_id = create_interview(sample_interview)

        # Act - update outcome after interview
        interview = get_interview(interview_id)
        interview.outcome = "passed"
        interview.notes = "Great technical discussion, SQL skills impressive"
        update_interview(interview)

        # Assert
        updated = get_interview(interview_id)
        assert updated.outcome == "passed"
        assert "SQL skills impressive" in updated.notes

    def test_update_interview_reschedule(self, mock_get_db):
        """Test rescheduling an interview (changing scheduled_at)."""
        # Arrange
        app_id = create_test_application(mock_get_db)
        interview = Interview(
            application_id=app_id,
            scheduled_at="2024-01-25 10:00:00",
            type="technical"
        )
        interview_id = create_interview(interview)

        # Act - reschedule
        saved = get_interview(interview_id)
        saved.scheduled_at = "2024-01-27 14:00:00"
        update_interview(saved)

        # Assert
        updated = get_interview(interview_id)
        assert updated.scheduled_at == "2024-01-27 14:00:00"
