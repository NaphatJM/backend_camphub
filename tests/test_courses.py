import pytest
import pytest_asyncio
from httpx import AsyncClient
from app.models.user_model import User
from app.models.faculty_model import Faculty
from app.models.role_model import Role
from app.models.course_model import Course


@pytest_asyncio.fixture
async def setup_base_data(session):
    """Setup base data required for tests."""
    # Create roles (matching init_data.py)
    professor_role = Role(
        id=1, name="Professor", description="Faculty member who can teach courses"
    )
    student_role = Role(
        id=2, name="Student", description="Student who can enroll in courses"
    )
    admin_role = Role(
        id=3, name="Admin", description="System administrator with full access"
    )
    session.add_all([professor_role, student_role, admin_role])

    # Create faculty
    faculty = Faculty(id=1, name="คณะวิทยาศาสตร์และเทคโนโลยี")
    session.add(faculty)

    await session.commit()
    return {
        "professor_role": professor_role,
        "student_role": student_role,
        "admin_role": admin_role,
        "faculty": faculty,
    }


@pytest_asyncio.fixture
async def teacher_user(client: AsyncClient, setup_base_data):
    """Create and authenticate a teacher user."""
    signup_data = {
        "username": "teacher1",
        "email": "teacher1@example.com",
        "password": "teacherpass123",
        "first_name": "Teacher",
        "last_name": "One",
        "birth_date": "1980-01-01",
        "faculty_id": 1,
        "role_id": 1,  # Professor role
    }

    response = await client.post("/api/auth/signup", json=signup_data)
    token = response.json()["access_token"]

    return {
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
        "user_data": signup_data,
    }


@pytest_asyncio.fixture
async def admin_user(client: AsyncClient, setup_base_data):
    """Create and authenticate an admin user."""
    signup_data = {
        "username": "admin1",
        "email": "admin1@example.com",
        "password": "adminpass123",
        "first_name": "Admin",
        "last_name": "User",
        "birth_date": "1975-01-01",
        "faculty_id": 1,
        "role_id": 3,  # Admin role
    }

    response = await client.post("/api/auth/signup", json=signup_data)
    token = response.json()["access_token"]

    return {
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
        "user_data": signup_data,
    }


@pytest_asyncio.fixture
async def student_user(client: AsyncClient, setup_base_data):
    """Create and authenticate a student user."""
    signup_data = {
        "username": "student1",
        "email": "student1@example.com",
        "password": "studentpass123",
        "first_name": "Student",
        "last_name": "One",
        "birth_date": "2000-01-01",
        "faculty_id": 1,
        "year_of_study": 2,
        "role_id": 2,  # Student role
    }

    response = await client.post("/api/auth/signup", json=signup_data)
    token = response.json()["access_token"]

    return {
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
        "user_data": signup_data,
    }


@pytest_asyncio.fixture
def course_create_data():
    """Valid course creation data."""
    return {
        "course_code": "CS101",
        "course_name": "Introduction to Computer Science",
        "credits": 3,
        "available_seats": 40,
        "description": "Basic concepts of computer science",
        "teacher_ids": [],
    }


@pytest_asyncio.fixture
async def sample_course(session, admin_user):
    """Create a sample course in the database."""
    course = Course(
        course_code="MATH101",
        course_name="Basic Mathematics",
        credits=3,
        available_seats=30,
        description="Fundamental mathematical concepts",
    )

    session.add(course)
    await session.commit()
    await session.refresh(course)

    return course


class TestCourse:
    """Test course endpoints."""

    @pytest.mark.asyncio
    async def test_get_courses_success(self, client: AsyncClient, sample_course):
        """Test getting all courses."""
        response = await client.get("/api/courses/")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Check course structure
        course = data[0]
        assert "id" in course
        assert "course_code" in course
        assert "course_name" in course
        assert "credits" in course
        assert "available_seats" in course
        assert "description" in course
        assert "created_at" in course
        assert "enrolled_count" in course

    @pytest.mark.asyncio
    async def test_get_course_by_id_success(self, client: AsyncClient, sample_course):
        """Test getting course by ID."""
        course_id = sample_course.id

        response = await client.get(f"/api/courses/{course_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == course_id
        assert data["course_code"] == "MATH101"
        assert data["course_name"] == "Basic Mathematics"
        assert data["credits"] == 3
        assert data["available_seats"] == 30
        assert data["enrolled_count"] == 0

    @pytest.mark.asyncio
    async def test_get_course_by_id_not_found(self, client: AsyncClient):
        """Test getting non-existent course by ID."""
        response = await client.get("/api/courses/9999")
        assert response.status_code == 404
        assert "Course not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_course_as_admin_success(
        self, client: AsyncClient, admin_user, course_create_data
    ):
        """Test creating course as admin user."""
        headers = admin_user["headers"]

        response = await client.post(
            "/api/courses/", json=course_create_data, headers=headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["course_code"] == course_create_data["course_code"]
        assert data["course_name"] == course_create_data["course_name"]
        assert data["credits"] == course_create_data["credits"]
        assert data["available_seats"] == course_create_data["available_seats"]
        assert data["description"] == course_create_data["description"]
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_course_as_professor_success(
        self, client: AsyncClient, teacher_user, course_create_data
    ):
        """Test creating course as professor user (role_id=1) should work."""
        headers = teacher_user["headers"]
        course_data = course_create_data.copy()
        course_data["course_code"] = "CS102"  # Different code to avoid conflicts

        response = await client.post("/api/courses/", json=course_data, headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["course_code"] == "CS102"
        assert data["course_name"] == course_data["course_name"]

    @pytest.mark.asyncio
    async def test_create_course_as_student_forbidden(
        self, client: AsyncClient, student_user, course_create_data
    ):
        """Test creating course as student user (role_id=2) should be forbidden."""
        headers = student_user["headers"]
        course_data = course_create_data.copy()
        course_data["course_code"] = "CS102"  # Different code to avoid conflicts

        response = await client.post("/api/courses/", json=course_data, headers=headers)
        # Note: Based on the service code, student (role_id=2) should NOT be allowed
        # Only role_id 1 (Professor) or 3 (Admin) are allowed. Let's test the expected behavior.
        assert response.status_code == 403
        assert (
            "Only professors and admins can create courses" in response.json()["detail"]
        )

    @pytest.mark.asyncio
    async def test_create_course_as_student_forbidden(
        self, client: AsyncClient, student_user, course_create_data
    ):
        """Test creating course as student user should be forbidden."""
        headers = student_user["headers"]

        response = await client.post(
            "/api/courses/", json=course_create_data, headers=headers
        )
        assert response.status_code == 403
        assert (
            "Only professors and admins can create courses" in response.json()["detail"]
        )

    @pytest.mark.asyncio
    async def test_create_course_unauthorized(
        self, client: AsyncClient, course_create_data
    ):
        """Test creating course without authentication."""
        response = await client.post("/api/courses/", json=course_create_data)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_course_duplicate_code(
        self, client: AsyncClient, admin_user, sample_course, course_create_data
    ):
        """Test creating course with duplicate course code."""
        headers = admin_user["headers"]

        # Use the same course code as sample_course
        duplicate_data = course_create_data.copy()
        duplicate_data["course_code"] = "MATH101"  # Same as sample_course

        response = await client.post(
            "/api/courses/", json=duplicate_data, headers=headers
        )
        # Should fail with proper error handling (400 instead of 500)
        assert response.status_code == 400
        assert f"Course code 'MATH101' already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_course_success(
        self, client: AsyncClient, admin_user, sample_course
    ):
        """Test updating course successfully."""
        headers = admin_user["headers"]
        course_id = sample_course.id

        update_data = {
            "course_name": "Advanced Mathematics",
            "credits": 4,
            "available_seats": 25,
            "description": "Advanced mathematical concepts",
        }

        response = await client.put(
            f"/api/courses/{course_id}", json=update_data, headers=headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["course_name"] == "Advanced Mathematics"
        assert data["credits"] == 4
        assert data["available_seats"] == 25
        assert data["description"] == "Advanced mathematical concepts"

    @pytest.mark.asyncio
    async def test_update_course_not_found(self, client: AsyncClient, admin_user):
        """Test updating non-existent course."""
        headers = admin_user["headers"]

        update_data = {"course_name": "Does Not Exist"}

        response = await client.put(
            "/api/courses/9999", json=update_data, headers=headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_course_unauthorized(self, client: AsyncClient, sample_course):
        """Test updating course without authentication."""
        course_id = sample_course.id

        update_data = {"course_name": "Should Fail"}

        response = await client.put(f"/api/courses/{course_id}", json=update_data)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_course_success(
        self, client: AsyncClient, admin_user, sample_course
    ):
        """Test deleting course successfully."""
        headers = admin_user["headers"]
        course_id = sample_course.id

        response = await client.delete(f"/api/courses/{course_id}", headers=headers)
        assert response.status_code == 200

        # Verify course is deleted
        get_response = await client.get(f"/api/courses/{course_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_course_not_found(self, client: AsyncClient, admin_user):
        """Test deleting non-existent course."""
        headers = admin_user["headers"]

        response = await client.delete("/api/courses/9999", headers=headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_course_unauthorized(self, client: AsyncClient, sample_course):
        """Test deleting course without authentication."""
        course_id = sample_course.id

        response = await client.delete(f"/api/courses/{course_id}")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_course_crud_flow(self, client: AsyncClient, admin_user):
        """Test complete course CRUD flow."""
        headers = admin_user["headers"]

        # 1. Create course
        create_data = {
            "course_code": "CRUD101",
            "course_name": "CRUD Test Course",
            "credits": 3,
            "available_seats": 35,
            "description": "Course for testing CRUD operations",
            "teacher_ids": [],
        }

        create_response = await client.post(
            "/api/courses/", json=create_data, headers=headers
        )
        assert create_response.status_code == 200
        course_id = create_response.json()["id"]

        # 2. Read course
        read_response = await client.get(f"/api/courses/{course_id}")
        assert read_response.status_code == 200
        assert read_response.json()["course_name"] == "CRUD Test Course"

        # 3. Update course
        update_data = {"course_name": "Updated CRUD Course", "credits": 4}
        update_response = await client.put(
            f"/api/courses/{course_id}", json=update_data, headers=headers
        )
        assert update_response.status_code == 200
        assert update_response.json()["course_name"] == "Updated CRUD Course"
        assert update_response.json()["credits"] == 4

        # 4. Delete course
        delete_response = await client.delete(
            f"/api/courses/{course_id}", headers=headers
        )
        assert delete_response.status_code == 200

        # 5. Verify deletion
        final_read = await client.get(f"/api/courses/{course_id}")
        assert final_read.status_code == 404

    @pytest.mark.asyncio
    async def test_course_list_after_operations(self, client: AsyncClient, admin_user):
        """Test course listing after create/delete operations."""
        headers = admin_user["headers"]

        # Get initial count
        initial_response = await client.get("/api/courses/")
        initial_count = len(initial_response.json())

        # Create a course
        create_data = {
            "course_code": "LIST101",
            "course_name": "List Test Course",
            "credits": 3,
            "available_seats": 30,
            "description": "Course for testing listing",
            "teacher_ids": [],
        }

        create_response = await client.post(
            "/api/courses/", json=create_data, headers=headers
        )
        assert create_response.status_code == 200
        course_id = create_response.json()["id"]

        # Check increased count
        after_create_response = await client.get("/api/courses/")
        after_create_count = len(after_create_response.json())
        assert after_create_count == initial_count + 1

        # Delete the course
        await client.delete(f"/api/courses/{course_id}", headers=headers)

        # Check count returned to initial
        final_response = await client.get("/api/courses/")
        final_count = len(final_response.json())
        assert final_count == initial_count
