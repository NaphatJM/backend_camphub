import pytest
import pytest_asyncio
from httpx import AsyncClient
from app.models.user_model import User
from app.models.faculty_model import Faculty
from app.models.role_model import Role
from app.models.course_model import Course
from app.models.enrollment_model import Enrollment


@pytest_asyncio.fixture
async def setup_base_data(session):
    """Setup base data required for tests."""
    # Create roles
    student_role = Role(id=1, name="Student", description="นักศึกษา")
    teacher_role = Role(id=2, name="Teacher", description="อาจารย์")
    admin_role = Role(id=3, name="Admin", description="ผู้ดูแล")
    session.add_all([student_role, teacher_role, admin_role])

    # Create faculty
    faculty = Faculty(id=1, name="คณะวิทยาศาสตร์และเทคโนโลยี")
    session.add(faculty)

    await session.commit()
    return {
        "student_role": student_role,
        "teacher_role": teacher_role,
        "admin_role": admin_role,
        "faculty": faculty,
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
        "role_id": 1,  # Student role
    }

    response = await client.post("/api/auth/signup", json=signup_data)
    token = response.json()["access_token"]

    return {
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
        "user_data": signup_data,
    }


@pytest_asyncio.fixture
async def second_student(client: AsyncClient, setup_base_data):
    """Create a second student user."""
    signup_data = {
        "username": "student2",
        "email": "student2@example.com",
        "password": "studentpass123",
        "first_name": "Student",
        "last_name": "Two",
        "birth_date": "1999-05-15",
        "faculty_id": 1,
        "year_of_study": 3,
        "role_id": 1,
    }

    response = await client.post("/api/auth/signup", json=signup_data)
    token = response.json()["access_token"]

    return {
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
        "user_data": signup_data,
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
        "role_id": 2,
    }

    response = await client.post("/api/auth/signup", json=signup_data)
    token = response.json()["access_token"]

    return {
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
        "user_data": signup_data,
    }


@pytest_asyncio.fixture
async def sample_course(session):
    """Create a sample course in the database."""
    course = Course(
        course_code="CS101",
        course_name="Introduction to Computer Science",
        credits=3,
        available_seats=30,
        description="Basic concepts of computer science",
    )

    session.add(course)
    await session.commit()
    await session.refresh(course)

    return course


class TestEnrollment:
    """Test enrollment endpoints."""

    @pytest.mark.asyncio
    async def test_enroll_course_success(
        self, client: AsyncClient, student_user, sample_course
    ):
        """Test successful course enrollment."""
        headers = student_user["headers"]
        course_id = sample_course.id

        enroll_data = {"course_id": course_id}

        response = await client.post(
            "/api/enrollments/enroll", json=enroll_data, headers=headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["course_id"] == course_id
        assert data["status"] == "enrolled"
        assert "id" in data
        assert "enrollment_at" in data

    @pytest.mark.asyncio
    async def test_enroll_nonexistent_course(self, client: AsyncClient, student_user):
        """Test enrolling in non-existent course."""
        headers = student_user["headers"]

        enroll_data = {"course_id": 9999}  # Non-existent course

        response = await client.post(
            "/api/enrollments/enroll", json=enroll_data, headers=headers
        )
        # Should fail due to foreign key constraint or service validation
        assert response.status_code in [400, 404, 500]

    @pytest.mark.asyncio
    async def test_enroll_duplicate_enrollment(
        self, client: AsyncClient, student_user, sample_course
    ):
        """Test enrolling in the same course twice."""
        headers = student_user["headers"]
        course_id = sample_course.id

        enroll_data = {"course_id": course_id}

        # First enrollment
        first_response = await client.post(
            "/api/enrollments/enroll", json=enroll_data, headers=headers
        )
        assert first_response.status_code == 200

        # Second enrollment (should update existing)
        second_response = await client.post(
            "/api/enrollments/enroll", json=enroll_data, headers=headers
        )
        assert second_response.status_code == 200

        # Should return the same enrollment (updated status)
        first_data = first_response.json()
        second_data = second_response.json()
        assert first_data["id"] == second_data["id"]
        assert second_data["status"] == "enrolled"

    @pytest.mark.asyncio
    async def test_enroll_unauthorized(self, client: AsyncClient, sample_course):
        """Test enrolling without authentication."""
        enroll_data = {"course_id": sample_course.id}

        response = await client.post("/api/enrollments/enroll", json=enroll_data)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_cancel_enrollment_success(
        self, client: AsyncClient, student_user, sample_course
    ):
        """Test successful enrollment cancellation."""
        headers = student_user["headers"]
        course_id = sample_course.id

        # First enroll
        enroll_data = {"course_id": course_id}
        await client.post("/api/enrollments/enroll", json=enroll_data, headers=headers)

        # Then cancel
        response = await client.delete(
            f"/api/enrollments/cancel/{course_id}", headers=headers
        )
        assert response.status_code == 200

        # Try to cancel again - should fail
        second_cancel = await client.delete(
            f"/api/enrollments/cancel/{course_id}", headers=headers
        )
        assert second_cancel.status_code == 404
        assert "Enrollment not found" in second_cancel.json()["detail"]

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_enrollment(
        self, client: AsyncClient, student_user, sample_course
    ):
        """Test cancelling non-existent enrollment."""
        headers = student_user["headers"]
        course_id = sample_course.id

        response = await client.delete(
            f"/api/enrollments/cancel/{course_id}", headers=headers
        )
        assert response.status_code == 404
        assert "Enrollment not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_user_enrollments(
        self, client: AsyncClient, student_user, sample_course
    ):
        """Test getting current user's enrollments."""
        headers = student_user["headers"]

        # Enroll in a course first
        enroll_data = {"course_id": sample_course.id}
        await client.post("/api/enrollments/enroll", json=enroll_data, headers=headers)

        # Get user enrollments
        response = await client.get("/api/enrollments/me", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Check enrollment structure
        enrollment = data[0]
        assert enrollment["course_id"] == sample_course.id
        assert enrollment["status"] == "enrolled"

    @pytest.mark.asyncio
    async def test_get_user_enrollments_empty(self, client: AsyncClient, student_user):
        """Test getting enrollments when user has no enrollments."""
        headers = student_user["headers"]

        response = await client.get("/api/enrollments/me", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_get_course_enrollments(
        self,
        client: AsyncClient,
        student_user,
        second_student,
        teacher_user,
        sample_course,
    ):
        """Test getting enrollments for a specific course."""
        # Enroll both students
        headers1 = student_user["headers"]
        headers2 = second_student["headers"]
        teacher_headers = teacher_user["headers"]

        enroll_data = {"course_id": sample_course.id}

        await client.post("/api/enrollments/enroll", json=enroll_data, headers=headers1)
        await client.post("/api/enrollments/enroll", json=enroll_data, headers=headers2)

        # Get course enrollments as teacher
        response = await client.get(
            f"/api/enrollments/course/{sample_course.id}", headers=teacher_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["course_id"] == sample_course.id
        assert data["course_code"] == "CS101"
        assert data["course_name"] == "Introduction to Computer Science"
        assert data["total_enrolled"] == 2
        assert len(data["enrolled_users"]) == 2

        # Check student names are in the list
        enrolled_names = data["enrolled_users"]
        assert "Student One" in enrolled_names
        assert "Student Two" in enrolled_names

    @pytest.mark.asyncio
    async def test_get_course_enrollments_empty(
        self, client: AsyncClient, teacher_user, sample_course
    ):
        """Test getting enrollments for course with no enrollments."""
        headers = teacher_user["headers"]

        response = await client.get(
            f"/api/enrollments/course/{sample_course.id}", headers=headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["course_id"] == sample_course.id
        assert data["total_enrolled"] == 0
        assert len(data["enrolled_users"]) == 0

    @pytest.mark.asyncio
    async def test_enrollment_flow_integration(
        self, client: AsyncClient, student_user, sample_course
    ):
        """Test complete enrollment flow: enroll -> check enrollment -> cancel -> check again."""
        headers = student_user["headers"]
        course_id = sample_course.id

        # 1. Check initial state (no enrollments)
        initial_response = await client.get("/api/enrollments/me", headers=headers)
        assert len(initial_response.json()) == 0

        # 2. Enroll in course
        enroll_data = {"course_id": course_id}
        enroll_response = await client.post(
            "/api/enrollments/enroll", json=enroll_data, headers=headers
        )
        assert enroll_response.status_code == 200

        # 3. Check enrollment exists
        check_response = await client.get("/api/enrollments/me", headers=headers)
        enrollments = check_response.json()
        assert len(enrollments) == 1
        assert enrollments[0]["course_id"] == course_id
        assert enrollments[0]["status"] == "enrolled"

        # 4. Cancel enrollment
        cancel_response = await client.delete(
            f"/api/enrollments/cancel/{course_id}", headers=headers
        )
        assert cancel_response.status_code == 200

        # 5. Check enrollment is gone
        final_response = await client.get("/api/enrollments/me", headers=headers)
        assert len(final_response.json()) == 0

    @pytest.mark.asyncio
    async def test_multiple_students_same_course(
        self,
        client: AsyncClient,
        student_user,
        second_student,
        teacher_user,
        sample_course,
    ):
        """Test multiple students enrolling in the same course."""
        headers1 = student_user["headers"]
        headers2 = second_student["headers"]
        teacher_headers = teacher_user["headers"]
        course_id = sample_course.id

        # Both students enroll
        enroll_data = {"course_id": course_id}

        response1 = await client.post(
            "/api/enrollments/enroll", json=enroll_data, headers=headers1
        )
        assert response1.status_code == 200

        response2 = await client.post(
            "/api/enrollments/enroll", json=enroll_data, headers=headers2
        )
        assert response2.status_code == 200

        # Check course enrollments
        course_enrollments = await client.get(
            f"/api/enrollments/course/{course_id}", headers=teacher_headers
        )
        assert course_enrollments.status_code == 200
        assert course_enrollments.json()["total_enrolled"] == 2

        # Each student should see only their enrollment
        user1_enrollments = await client.get("/api/enrollments/me", headers=headers1)
        assert len(user1_enrollments.json()) == 1

        user2_enrollments = await client.get("/api/enrollments/me", headers=headers2)
        assert len(user2_enrollments.json()) == 1

        # Student 1 cancels
        await client.delete(f"/api/enrollments/cancel/{course_id}", headers=headers1)

        # Check updated counts
        updated_course_enrollments = await client.get(
            f"/api/enrollments/course/{course_id}", headers=teacher_headers
        )
        assert updated_course_enrollments.json()["total_enrolled"] == 1

        user1_after_cancel = await client.get("/api/enrollments/me", headers=headers1)
        assert len(user1_after_cancel.json()) == 0

        user2_still_enrolled = await client.get("/api/enrollments/me", headers=headers2)
        assert len(user2_still_enrolled.json()) == 1
