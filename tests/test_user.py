import pytest
import pytest_asyncio
import pytest_asyncio
from datetime import date
from httpx import AsyncClient
from app.models.user_model import User
from app.models.faculty_model import Faculty
from app.models.role_model import Role


@pytest_asyncio.fixture
async def setup_base_data(session):
    """Setup base data required for tests."""
    # Create roles
    student_role = Role(id=1, name="Student", description="นักศึกษา")
    teacher_role = Role(id=2, name="Teacher", description="อาจารย์")
    session.add(student_role)
    session.add(teacher_role)

    # Create faculty
    faculty = Faculty(id=1, name="คณะวิทยาศาสตร์และเทคโนโลยี")
    session.add(faculty)

    await session.commit()
    return {
        "student_role": student_role,
        "teacher_role": teacher_role,
        "faculty": faculty,
    }


@pytest_asyncio.fixture
async def authenticated_user(client: AsyncClient, setup_base_data):
    """Create and authenticate a test user."""
    signup_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "first_name": "Test",
        "last_name": "User",
        "birth_date": "2000-01-01",
        "faculty_id": 1,
        "year_of_study": 3,
        "role_id": 1,
    }

    # Signup user
    response = await client.post("/api/auth/signup", json=signup_data)
    token = response.json()["access_token"]

    return {
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
        "user_data": signup_data,
    }


@pytest_asyncio.fixture
async def second_user(client: AsyncClient, setup_base_data):
    """Create a second authenticated user for testing."""
    signup_data = {
        "username": "seconduser",
        "email": "second@example.com",
        "password": "pass123",
        "first_name": "Second",
        "last_name": "User",
        "birth_date": "1999-05-15",
        "faculty_id": 1,
        "year_of_study": 2,
        "role_id": 2,
    }

    response = await client.post("/api/auth/signup", json=signup_data)
    token = response.json()["access_token"]

    return {
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
        "user_data": signup_data,
    }


class TestUser:
    """Test user endpoints."""

    @pytest.mark.asyncio
    async def test_get_me_success(self, client: AsyncClient, authenticated_user):
        """Test getting current user profile."""
        headers = authenticated_user["headers"]

        response = await client.get("/api/user", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["first_name"] == "Test"
        assert data["last_name"] == "User"
        assert data["birth_date"] == "2000-01-01"
        assert data["faculty_id"] == 1
        assert data["faculty_name"] == "คณะวิทยาศาสตร์และเทคโนโลยี"
        assert data["year_of_study"] == 3
        assert data["role_id"] == 1
        assert data["role_name"] == "Student"
        assert "id" in data
        assert "age" in data
        assert "fullname" in data

    @pytest.mark.asyncio
    async def test_get_me_unauthorized(self, client: AsyncClient):
        """Test getting current user profile without authentication."""
        response = await client.get("/api/user")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_me_invalid_token(self, client: AsyncClient):
        """Test getting current user profile with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = await client.get("/api/user", headers=headers)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(
        self, client: AsyncClient, authenticated_user, second_user
    ):
        """Test getting user profile by ID."""
        # Get current user to extract their ID
        headers = authenticated_user["headers"]
        me_response = await client.get("/api/user", headers=headers)
        user_id = me_response.json()["id"]

        # Get user by ID
        response = await client.get(f"/api/user/{user_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == user_id
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, client: AsyncClient):
        """Test getting non-existent user by ID."""
        response = await client.get("/api/user/9999")
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_me_success(self, client: AsyncClient, authenticated_user):
        """Test updating current user profile."""
        headers = authenticated_user["headers"]

        update_data = {"first_name": "Updated", "last_name": "Name", "year_of_study": 4}

        response = await client.put("/api/user", json=update_data, headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"
        assert data["year_of_study"] == 4

    @pytest.mark.asyncio
    async def test_update_me_duplicate_username(
        self, client: AsyncClient, authenticated_user, second_user
    ):
        """Test updating username to an existing one."""
        headers = authenticated_user["headers"]

        update_data = {"username": "seconduser"}  # Username of second user

        response = await client.put("/api/user", json=update_data, headers=headers)
        assert response.status_code == 400
        assert "Username already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_me_duplicate_email(
        self, client: AsyncClient, authenticated_user, second_user
    ):
        """Test updating email to an existing one."""
        headers = authenticated_user["headers"]

        update_data = {"email": "second@example.com"}  # Email of second user

        response = await client.put("/api/user", json=update_data, headers=headers)
        assert response.status_code == 400
        assert "Email already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_me_password(self, client: AsyncClient, authenticated_user):
        """Test updating password."""
        headers = authenticated_user["headers"]

        update_data = {"new_password": "newpassword123"}

        response = await client.put("/api/user", json=update_data, headers=headers)
        assert response.status_code == 200

        # Test login with new password
        login_data = {"email": "test@example.com", "password": "newpassword123"}

        login_response = await client.post("/api/auth/signin", json=login_data)
        assert login_response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_me_unauthorized(self, client: AsyncClient):
        """Test updating profile without authentication."""
        update_data = {"first_name": "Should Fail"}

        response = await client.put("/api/user", json=update_data)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_me_partial_fields(
        self, client: AsyncClient, authenticated_user
    ):
        """Test updating only some fields."""
        headers = authenticated_user["headers"]

        # Update only birth_date
        update_data = {"birth_date": "1999-12-25"}

        response = await client.put("/api/user", json=update_data, headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["birth_date"] == "1999-12-25"
        # Other fields should remain unchanged
        assert data["username"] == "testuser"
        assert data["first_name"] == "Test"

    @pytest.mark.asyncio
    async def test_user_crud_flow(self, client: AsyncClient, setup_base_data):
        """Test complete user CRUD flow."""
        # 1. Create user (signup)
        signup_data = {
            "username": "cruduser",
            "email": "crud@example.com",
            "password": "crudpass123",
            "first_name": "CRUD",
            "last_name": "Test",
            "birth_date": "1998-03-10",
            "faculty_id": 1,
            "role_id": 1,
        }

        signup_response = await client.post("/api/auth/signup", json=signup_data)
        assert signup_response.status_code == 201
        token = signup_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Read user profile
        read_response = await client.get("/api/user", headers=headers)
        assert read_response.status_code == 200
        user_data = read_response.json()
        user_id = user_data["id"]

        # 3. Update user
        update_data = {"first_name": "Updated CRUD", "year_of_study": 1}
        update_response = await client.put(
            "/api/user", json=update_data, headers=headers
        )
        assert update_response.status_code == 200
        assert update_response.json()["first_name"] == "Updated CRUD"

        # 4. Verify update by reading again
        final_read = await client.get("/api/user", headers=headers)
        assert final_read.status_code == 200
        assert final_read.json()["first_name"] == "Updated CRUD"
        assert final_read.json()["year_of_study"] == 1
