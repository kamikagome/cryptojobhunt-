"""
Unit tests for Skills and JobSkills operations.

=== MENTOR NOTES ===

Many-to-Many Relationships
--------------------------
Jobs and Skills have a many-to-many (M:M) relationship:
- One job can require many skills
- One skill can be required by many jobs

This is implemented with a "junction table" (job_skills) that has:
- job_id (foreign key to jobs)
- skill_id (foreign key to skills)
- importance (required vs nice-to-have)

Testing Junction Tables
-----------------------
We need to test:
1. Adding skills to jobs
2. Removing skills from jobs
3. Retrieving all skills for a job
4. The "importance" metadata on the relationship

Seed Data Testing
-----------------
The database has pre-seeded skills from seed.sql. Our tests use
the fresh in-memory database which also runs seed.sql, so we can
verify those skills exist.

===================
"""

import pytest
from src.db.models import Company, Job, Skill
from src.db.queries import (
    add_skill_to_job,
    create_company,
    create_job,
    create_skill,
    get_job_skills,
    get_skill,
    get_skill_by_name,
    list_skills,
    remove_skill_from_job,
)


def create_test_job_for_skills(mock_db) -> int:
    """Helper to create a company and job for skill testing."""
    company = Company(name="Skill Test Company")
    company_id = create_company(company)
    job = Job(company_id=company_id, title="Skill Test Job")
    return create_job(job)


class TestSkillsCRUD:
    """Tests for basic Skill operations."""

    def test_seed_skills_exist(self, mock_get_db):
        """
        Test that seed data skills are present.

        This verifies that seed.sql runs correctly during test setup.
        """
        # Act
        skills = list_skills()

        # Assert - check the seeded SQL skill exists
        skill_names = [s.name for s in skills]
        assert "SQL" in skill_names

    def test_list_skills_filter_by_category(self, mock_get_db):
        """Test filtering skills by category."""
        # Act
        sql_skills = list_skills(category="SQL")

        # Assert
        assert len(sql_skills) > 0
        assert all(s.category == "SQL" for s in sql_skills)

    def test_create_skill_returns_id(self, mock_get_db, sample_skill):
        """Test that creating a new skill returns a valid ID."""
        # Act
        skill_id = create_skill(sample_skill)

        # Assert
        assert skill_id > 0

    def test_create_skill_stores_correctly(self, mock_get_db, sample_skill):
        """Test that skill fields are stored correctly."""
        # Act
        skill_id = create_skill(sample_skill)

        # Assert
        saved = get_skill(skill_id)
        assert saved.name == sample_skill.name
        assert saved.category == sample_skill.category

    def test_get_skill_by_name_exact(self, mock_get_db):
        """Test finding a skill by exact name."""
        # Act - use a seeded skill
        result = get_skill_by_name("SQL")

        # Assert
        assert result is not None
        assert result.name == "SQL"
        assert result.category == "SQL"

    def test_get_skill_by_name_case_insensitive(self, mock_get_db):
        """Test that skill name search is case-insensitive."""
        # Act
        result = get_skill_by_name("sql")  # lowercase

        # Assert
        assert result is not None
        assert result.name == "SQL"

    def test_get_skill_not_found(self, mock_get_db):
        """Test that get_skill returns None for non-existent skill."""
        # Act
        result = get_skill(99999)

        # Assert
        assert result is None

    def test_create_duplicate_skill_raises_error(self, mock_get_db):
        """Test that duplicate skill names are rejected."""
        # Arrange - "SQL" already exists from seed data

        # Act & Assert
        import sqlite3
        with pytest.raises(sqlite3.IntegrityError):
            create_skill(Skill(name="SQL", category="SQL"))


class TestJobSkills:
    """Tests for the job_skills junction table operations."""

    def test_add_skill_to_job(self, mock_get_db):
        """Test adding a skill to a job."""
        # Arrange
        job_id = create_test_job_for_skills(mock_get_db)
        sql_skill = get_skill_by_name("SQL")

        # Act
        add_skill_to_job(job_id, sql_skill.id, importance="required")

        # Assert
        skills = get_job_skills(job_id)
        assert len(skills) == 1
        assert skills[0][0].name == "SQL"
        assert skills[0][1] == "required"  # importance

    def test_remove_skill_from_job(self, mock_get_db):
        """Test removing a skill from a job."""
        # Arrange
        job_id = create_test_job_for_skills(mock_get_db)
        sql_skill = get_skill_by_name("SQL")

        add_skill_to_job(job_id, sql_skill.id)

        # Act
        remove_skill_from_job(job_id, sql_skill.id)

        # Assert
        skills = get_job_skills(job_id)
        assert len(skills) == 0

    def test_get_job_skills_empty(self, mock_get_db):
        """Test that a job with no skills returns empty list."""
        # Arrange
        job_id = create_test_job_for_skills(mock_get_db)

        # Act
        skills = get_job_skills(job_id)

        # Assert
        assert skills == []

    def test_add_skill_replace_importance(self, mock_get_db):
        """
        Test that re-adding a skill updates the importance.

        The query uses INSERT OR REPLACE, so adding the same skill
        with different importance should update, not fail.
        """
        # Arrange
        job_id = create_test_job_for_skills(mock_get_db)
        sql_skill = get_skill_by_name("SQL")

        # Act - add as required, then change to nice-to-have
        add_skill_to_job(job_id, sql_skill.id, importance="required")
        add_skill_to_job(job_id, sql_skill.id, importance="nice-to-have")

        # Assert - should have only one entry with updated importance
        skills = get_job_skills(job_id)
        assert len(skills) == 1
        assert skills[0][1] == "nice-to-have"

