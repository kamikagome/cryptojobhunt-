"""
Unit tests for Company CRUD operations.

=== MENTOR NOTES ===

The AAA Pattern (Arrange-Act-Assert)
------------------------------------
Every good test follows this structure:

1. ARRANGE: Set up the test data and preconditions
2. ACT: Execute the code you're testing
3. ASSERT: Verify the results are what you expected

Example:
    def test_addition():
        # Arrange
        a = 2
        b = 3

        # Act
        result = add(a, b)

        # Assert
        assert result == 5

Why Test CRUD Operations?
-------------------------
CRUD = Create, Read, Update, Delete

These are the fundamental database operations. Testing them ensures:
- Data is saved correctly
- Data can be retrieved correctly
- Updates modify the right fields
- Edge cases are handled (like duplicates, missing records)

Test Naming Convention
----------------------
Use descriptive names: test_<what>_<condition>_<expected_result>
Examples:
- test_create_company_returns_id
- test_get_company_not_found_returns_none
- test_update_company_changes_all_fields

===================
"""

import pytest
from src.db.models import Company
from src.db.queries import (
    create_company,
    get_company,
    get_company_by_name,
    list_companies,
    update_company,
)


class TestCreateCompany:
    """Tests for the create_company function."""

    def test_create_company_returns_positive_id(self, mock_get_db, sample_company):
        """
        Test that creating a company returns a valid ID.

        ARRANGE: We have a sample_company from our fixture
        ACT: Call create_company()
        ASSERT: The returned ID should be a positive integer
        """
        # Act
        company_id = create_company(sample_company)

        # Assert
        assert company_id is not None
        assert company_id > 0

    def test_create_company_stores_all_fields(self, mock_get_db, sample_company):
        """
        Test that all company fields are stored correctly.

        This is a more thorough test - we create a company, then
        read it back and verify every field matches.
        """
        # Act
        company_id = create_company(sample_company)

        # Assert - fetch the company and check all fields
        saved = get_company(company_id)
        assert saved is not None
        assert saved.name == sample_company.name
        assert saved.website == sample_company.website
        assert saved.sector == sample_company.sector
        assert saved.chain_focus == sample_company.chain_focus
        assert saved.size == sample_company.size
        assert saved.notes == sample_company.notes

    def test_create_company_with_minimal_data(self, mock_get_db):
        """
        Test that a company can be created with only required fields.

        This tests the "happy path minimum" - the simplest valid input.
        """
        # Arrange - company with only the required name field
        company = Company(name="Minimal Corp")

        # Act
        company_id = create_company(company)

        # Assert
        assert company_id > 0
        saved = get_company(company_id)
        assert saved.name == "Minimal Corp"
        assert saved.website is None
        assert saved.sector is None

    def test_create_duplicate_company_raises_error(self, mock_get_db, sample_company):
        """
        Test that creating a duplicate company name raises an error.

        This tests a CONSTRAINT - the schema says company names must be unique.
        We use pytest.raises() to verify an exception is raised.
        """
        # Arrange - create first company
        create_company(sample_company)

        # Act & Assert - second company with same name should fail
        import sqlite3
        with pytest.raises(sqlite3.IntegrityError):
            create_company(sample_company)


class TestGetCompany:
    """Tests for the get_company function."""

    def test_get_company_returns_correct_company(self, mock_get_db, sample_company):
        """Test that get_company returns the right company by ID."""
        # Arrange
        company_id = create_company(sample_company)

        # Act
        result = get_company(company_id)

        # Assert
        assert result is not None
        assert result.id == company_id
        assert result.name == sample_company.name

    def test_get_company_not_found_returns_none(self, mock_get_db):
        """
        Test that get_company returns None for non-existent ID.

        Testing the "not found" case is important - your code should
        handle missing data gracefully, not crash.
        """
        # Act
        result = get_company(99999)

        # Assert
        assert result is None


class TestGetCompanyByName:
    """Tests for the get_company_by_name function."""

    def test_get_company_by_name_exact_match(self, mock_get_db, sample_company):
        """Test finding a company by exact name."""
        # Arrange
        create_company(sample_company)

        # Act
        result = get_company_by_name(sample_company.name)

        # Assert
        assert result is not None
        assert result.name == sample_company.name

    def test_get_company_by_name_case_insensitive(self, mock_get_db, sample_company):
        """
        Test that name search is case-insensitive.

        This tests a specific behavior from the SQL query: LOWER(name) = LOWER(?)
        """
        # Arrange
        create_company(sample_company)

        # Act - search with different casing
        result = get_company_by_name(sample_company.name.upper())

        # Assert
        assert result is not None
        assert result.name == sample_company.name

    def test_get_company_by_name_not_found(self, mock_get_db):
        """Test that searching for non-existent name returns None."""
        # Act
        result = get_company_by_name("NonExistent Company")

        # Assert
        assert result is None


class TestListCompanies:
    """Tests for the list_companies function."""

    def test_list_companies_empty_database(self, mock_get_db):
        """Test that list_companies returns empty list when no companies exist."""
        # Act
        result = list_companies()

        # Assert
        assert result == []

    def test_list_companies_returns_all(self, mock_get_db):
        """Test that list_companies returns all created companies."""
        # Arrange - create multiple companies
        companies = [
            Company(name="Company A", sector="DeFi"),
            Company(name="Company B", sector="NFT"),
            Company(name="Company C", sector="Infrastructure"),
        ]
        for c in companies:
            create_company(c)

        # Act
        result = list_companies()

        # Assert
        assert len(result) == 3

    def test_list_companies_sorted_by_name(self, mock_get_db):
        """
        Test that list_companies returns results sorted by name.

        Testing the ORDER BY behavior - this is part of the function's contract.
        """
        # Arrange - create companies in non-alphabetical order
        create_company(Company(name="Zebra Corp"))
        create_company(Company(name="Alpha Inc"))
        create_company(Company(name="Middle LLC"))

        # Act
        result = list_companies()

        # Assert - should be alphabetically sorted
        names = [c.name for c in result]
        assert names == ["Alpha Inc", "Middle LLC", "Zebra Corp"]


class TestUpdateCompany:
    """Tests for the update_company function."""

    def test_update_company_changes_fields(self, mock_get_db, sample_company):
        """Test that update_company modifies the company correctly."""
        # Arrange - create a company
        company_id = create_company(sample_company)
        company = get_company(company_id)

        # Act - modify and update
        company.sector = "NFT"
        company.size = "large"
        company.notes = "Updated notes"
        update_company(company)

        # Assert - fetch again and verify changes
        updated = get_company(company_id)
        assert updated.sector == "NFT"
        assert updated.size == "large"
        assert updated.notes == "Updated notes"
        # Original fields should be unchanged
        assert updated.name == sample_company.name

    def test_update_company_can_set_null(self, mock_get_db, sample_company):
        """
        Test that fields can be set to None/NULL.

        This is an edge case - sometimes you want to clear a field.
        """
        # Arrange
        company_id = create_company(sample_company)
        company = get_company(company_id)

        # Act - clear the website field
        company.website = None
        update_company(company)

        # Assert
        updated = get_company(company_id)
        assert updated.website is None
