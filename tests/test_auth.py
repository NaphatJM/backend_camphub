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
def signup_data():
    """Valid signup data fixture."""
    return {
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


@pytest_asyncio.fixture
def login_data():
    """Valid login data fixture."""
    return {"email": "test@example.com", "password": "testpass123"}


class TestAuth:
    """Test authentication endpoints."""

    @pytest.mark.asyncio
    async def test_signup_success(
        self, client: AsyncClient, setup_base_data, signup_data
    ):
        """Test successful user signup."""
        response = await client.post("/api/auth/signup", json=signup_data)

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_signup_duplicate_username(
        self, client: AsyncClient, setup_base_data, signup_data
    ):
        """Test signup with duplicate username."""
        # Create first user
        await client.post("/api/auth/signup", json=signup_data)

        # Try to create another user with same username
        duplicate_data = signup_data.copy()
        duplicate_data["email"] = "different@example.com"

        response = await client.post("/api/auth/signup", json=duplicate_data)
        assert response.status_code == 400
        assert "ชื่อผู้ใช้นี้ถูกใช้แล้ว" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_signup_duplicate_email(
        self, client: AsyncClient, setup_base_data, signup_data
    ):
        """Test signup with duplicate email."""
        # Create first user
        await client.post("/api/auth/signup", json=signup_data)

        # Try to create another user with same email
        duplicate_data = signup_data.copy()
        duplicate_data["username"] = "differentuser"

        response = await client.post("/api/auth/signup", json=duplicate_data)
        assert response.status_code == 400
        assert "อีเมลนี้ถูกใช้แล้ว" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_signup_invalid_faculty(
        self, client: AsyncClient, setup_base_data, signup_data
    ):
        """Test signup with invalid faculty_id."""
        invalid_data = signup_data.copy()
        invalid_data["faculty_id"] = 999  # Non-existent faculty

        response = await client.post("/api/auth/signup", json=invalid_data)
        assert response.status_code == 400
        assert "กรุณากรอกคณะให้ถูกต้อง" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_signup_invalid_role(
        self, client: AsyncClient, setup_base_data, signup_data
    ):
        """Test signup with invalid role_id."""
        invalid_data = signup_data.copy()
        invalid_data["role_id"] = 999  # Non-existent role

        response = await client.post("/api/auth/signup", json=invalid_data)
        assert response.status_code == 400
        assert "กรุณากรอกบทบาทให้ถูกต้อง" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_signup_without_optional_fields(
        self, client: AsyncClient, setup_base_data
    ):
        """Test signup with minimal required fields."""
        minimal_data = {
            "username": "minimaluser",
            "email": "minimal@example.com",
            "password": "pass123",
            "first_name": "Min",
            "last_name": "User",
            "birth_date": "2000-05-15",
            "role_id": 1,
        }

        response = await client.post("/api/auth/signup", json=minimal_data)
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data

    @pytest.mark.asyncio
    async def test_signin_success(
        self, client: AsyncClient, setup_base_data, signup_data, login_data
    ):
        """Test successful user signin."""
        # Create user first
        await client.post("/api/auth/signup", json=signup_data)

        # Test login
        response = await client.post("/api/auth/signin", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_signin_invalid_email(self, client: AsyncClient, setup_base_data):
        """Test signin with non-existent email."""
        login_data = {"email": "nonexistent@example.com", "password": "anypassword"}

        response = await client.post("/api/auth/signin", json=login_data)
        assert response.status_code == 401
        assert "อีเมลหรือรหัสผ่านไม่ถูกต้อง" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_signin_invalid_password(
        self, client: AsyncClient, setup_base_data, signup_data
    ):
        """Test signin with wrong password."""
        # Create user first
        await client.post("/api/auth/signup", json=signup_data)

        # Try login with wrong password
        wrong_login = {"email": signup_data["email"], "password": "wrongpassword"}

        response = await client.post("/api/auth/signin", json=wrong_login)
        assert response.status_code == 401
        assert "อีเมลหรือรหัสผ่านไม่ถูกต้อง" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_auth_flow_integration(
        self, client: AsyncClient, setup_base_data, signup_data, login_data
    ):
        """Test complete auth flow: signup -> signin."""
        # 1. Signup
        signup_response = await client.post("/api/auth/signup", json=signup_data)
        assert signup_response.status_code == 201
        signup_token = signup_response.json()["access_token"]

        # 2. Signin
        signin_response = await client.post("/api/auth/signin", json=login_data)
        assert signin_response.status_code == 200
        signin_token = signin_response.json()["access_token"]

        # Both tokens should be valid JWT tokens (contain dots)
        assert "." in signup_token
        assert "." in signin_token
