"""
Example test data and utilities for CampHub testing
"""

from datetime import datetime, timedelta
from app.models.announcement_model import AnnouncementCategory


class TestDataFactory:
    """Factory class for creating test data."""

    @staticmethod
    def create_user_data(username="testuser", email="test@example.com", role_id=1):
        """Create user signup data."""
        return {
            "username": username,
            "email": email,
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "User",
            "birth_date": "2000-01-01",
            "faculty_id": 1,
            "year_of_study": 3 if role_id == 1 else None,
            "role_id": role_id,
        }

    @staticmethod
    def create_course_data(course_code="CS101", course_name="Test Course"):
        """Create course data."""
        return {
            "course_code": course_code,
            "course_name": course_name,
            "credits": 3,
            "available_seats": 40,
            "description": "Test course description",
            "teacher_ids": [],
        }

    @staticmethod
    def create_announcement_data(
        title="Test Announcement", category=AnnouncementCategory.GENERAL
    ):
        """Create announcement data."""
        now = datetime.now()
        return {
            "title": title,
            "description": "Test announcement description",
            "category": category,
            "start_date": now,
            "end_date": now + timedelta(days=7),
        }

    @staticmethod
    def create_enrollment_data(course_id):
        """Create enrollment data."""
        return {"course_id": course_id}


class TestAssertions:
    """Common test assertions."""

    @staticmethod
    def assert_user_response(data, expected_username=None):
        """Assert user response structure."""
        assert "id" in data
        assert "username" in data
        assert "email" in data
        assert "first_name" in data
        assert "last_name" in data
        assert "birth_date" in data
        if expected_username:
            assert data["username"] == expected_username

    @staticmethod
    def assert_course_response(data, expected_code=None):
        """Assert course response structure."""
        assert "id" in data
        assert "course_code" in data
        assert "course_name" in data
        assert "credits" in data
        assert "available_seats" in data
        assert "created_at" in data
        if expected_code:
            assert data["course_code"] == expected_code

    @staticmethod
    def assert_announcement_response(data, expected_title=None):
        """Assert announcement response structure."""
        assert "id" in data
        assert "title" in data
        assert "description" in data
        assert "category" in data
        assert "start_date" in data
        assert "end_date" in data
        assert "created_at" in data
        if expected_title:
            assert data["title"] == expected_title

    @staticmethod
    def assert_enrollment_response(data, expected_course_id=None):
        """Assert enrollment response structure."""
        assert "id" in data
        assert "course_id" in data
        assert "status" in data
        assert "enrollment_at" in data
        if expected_course_id:
            assert data["course_id"] == expected_course_id
