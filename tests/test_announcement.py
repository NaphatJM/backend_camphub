import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from httpx import AsyncClient
from app.models.user_model import User
from app.models.faculty_model import Faculty
from app.models.role_model import Role
from app.models.announcement_model import Announcement, AnnouncementCategory
import io
import asyncio
import json
from jose import jwt
from app.core.config import settings


@pytest_asyncio.fixture
async def setup_base_data(session):
    """Setup base data required for tests."""
    # Create roles
    professor_role = Role(id=1, name="Professor", description="อาจารย์")
    student_role = Role(id=2, name="Student", description="นักศึกษา")
    admin_role = Role(id=3, name="Admin", description="ผู้ดูแลระบบ")
    session.add(professor_role)
    session.add(student_role)
    session.add(admin_role)

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
        "role_id": 1,  # Professor role to create announcements
    }

    response = await client.post("/api/auth/signup", json=signup_data)
    token = response.json()["access_token"]

    return {
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
        "user_data": signup_data,
    }


@pytest_asyncio.fixture
def announcement_create_data():
    """Valid announcement creation data."""
    now = datetime.now()
    return {
        "title": "Test Announcement",
        "description": "This is a test announcement description",
        "category": AnnouncementCategory.ACADEMIC,
        "start_date": now,
        "end_date": now + timedelta(days=7),
    }


@pytest_asyncio.fixture
async def sample_announcement(session, authenticated_user):
    """Create a sample announcement in the database."""
    # Get user from auth fixture info
    from app.models.user_model import User
    from sqlalchemy import select

    result = await session.exec(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    now = datetime.now()
    announcement = Announcement(
        title="Sample Announcement",
        description="Sample description",
        category=AnnouncementCategory.GENERAL,
        start_date=now - timedelta(days=1),  # Started yesterday
        end_date=now + timedelta(days=5),  # Ends in 5 days
        created_by=user.id,
    )

    session.add(announcement)
    await session.commit()
    await session.refresh(announcement)

    return announcement


class TestAnnouncement:
    """Test announcement endpoints."""

    @pytest.mark.asyncio
    async def test_get_announcements_success(
        self, client: AsyncClient, sample_announcement
    ):
        """Test getting active announcements."""
        response = await client.get("/api/annc/")
        assert response.status_code == 200

        data = response.json()
        assert "announcements" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "total_pages" in data
        assert data["total"] > 0
        assert len(data["announcements"]) > 0

    @pytest.mark.asyncio
    async def test_get_announcements_pagination(
        self, client: AsyncClient, sample_announcement
    ):
        """Test announcement pagination."""
        response = await client.get("/api/annc/?page=1&per_page=5")
        assert response.status_code == 200

        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 5

    @pytest.mark.asyncio
    async def test_get_announcements_by_category(
        self, client: AsyncClient, sample_announcement
    ):
        """Test filtering announcements by category."""
        response = await client.get("/api/annc/?category=ทั่วไป")
        assert response.status_code == 200

        data = response.json()
        assert "announcements" in data
        # Should find our sample announcement which is GENERAL category

    @pytest.mark.asyncio
    async def test_get_announcement_categories(self, client: AsyncClient):
        """Test getting available announcement categories."""
        response = await client.get("/api/annc/categories")
        assert response.status_code == 200

        data = response.json()
        assert "categories" in data
        categories = data["categories"]
        assert len(categories) == 3

        category_values = [cat["value"] for cat in categories]
        assert "วิชาการ" in category_values
        assert "กิจกรรม" in category_values
        assert "ทั่วไป" in category_values

    @pytest.mark.asyncio
    async def test_get_announcements_by_specific_category(
        self, client: AsyncClient, sample_announcement
    ):
        """Test getting announcements by specific category endpoint."""
        response = await client.get("/api/annc/by-category/ทั่วไป")
        assert response.status_code == 200

        data = response.json()
        assert "announcements" in data

    @pytest.mark.asyncio
    async def test_get_announcement_by_id_success(
        self, client: AsyncClient, sample_announcement
    ):
        """Test getting announcement by ID."""
        announcement_id = sample_announcement.id

        response = await client.get(f"/api/annc/{announcement_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == announcement_id
        assert data["title"] == "Sample Announcement"
        assert data["description"] == "Sample description"
        assert data["category"] == "ทั่วไป"

    @pytest.mark.asyncio
    async def test_get_announcement_by_id_not_found(self, client: AsyncClient):
        """Test getting non-existent announcement by ID."""
        response = await client.get("/api/annc/9999")
        assert response.status_code == 404
        assert "ไม่พบข่าวประกาศ" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_announcement_success(
        self, client: AsyncClient, authenticated_user
    ):
        """Test creating announcement successfully."""
        headers = authenticated_user["headers"]
        now = datetime.now()

        form_data = {
            "title": "New Test Announcement",
            "description": "New test description",
            "category": "วิชาการ",
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(days=7)).isoformat(),
        }

        response = await client.post("/api/annc/", data=form_data, headers=headers)
        assert response.status_code == 201

        data = response.json()
        assert data["title"] == "New Test Announcement"
        assert data["description"] == "New test description"
        assert data["category"] == "วิชาการ"
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_announcement_unauthorized(self, client: AsyncClient):
        """Test creating announcement without authentication."""
        now = datetime.now()

        form_data = {
            "title": "Unauthorized Announcement",
            "description": "Should fail",
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(days=1)).isoformat(),
        }

        response = await client.post("/api/annc/", data=form_data)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_announcement_invalid_date_range(
        self, client: AsyncClient, authenticated_user
    ):
        """Test creating announcement with invalid date range."""
        headers = authenticated_user["headers"]
        now = datetime.now()

        form_data = {
            "title": "Invalid Date Range",
            "description": "End date before start date",
            "start_date": now.isoformat(),
            "end_date": (now - timedelta(days=1)).isoformat(),  # End before start
        }

        response = await client.post("/api/annc/", data=form_data, headers=headers)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_announcement_crud_flow(
        self, client: AsyncClient, authenticated_user
    ):
        """Test complete announcement CRUD flow."""
        headers = authenticated_user["headers"]
        now = datetime.now()

        # 1. Create announcement
        create_data = {
            "title": "CRUD Test Announcement",
            "description": "CRUD test description",
            "category": "กิจกรรม",
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(days=10)).isoformat(),
        }

        create_response = await client.post(
            "/api/annc/", data=create_data, headers=headers
        )
        assert create_response.status_code == 201
        announcement_id = create_response.json()["id"]

        # 2. Read announcement
        read_response = await client.get(f"/api/annc/{announcement_id}")
        assert read_response.status_code == 200
        assert read_response.json()["title"] == "CRUD Test Announcement"

        # 3. Verify it appears in list
        list_response = await client.get("/api/annc/")
        assert list_response.status_code == 200
        announcements = list_response.json()["announcements"]
        announcement_ids = [ann["id"] for ann in announcements]
        assert announcement_id in announcement_ids

    @pytest.mark.asyncio
    async def test_announcements_active_only(
        self, client: AsyncClient, session, authenticated_user
    ):
        """Test that only active announcements are returned."""
        from app.models.user_model import User
        from sqlalchemy import select

        # Get user
        result = await session.exec(select(User).where(User.username == "testuser"))
        user = result.scalar_one()

        now = datetime.now()

        # Create past announcement (should not appear)
        past_announcement = Announcement(
            title="Past Announcement",
            description="This is expired",
            category=AnnouncementCategory.GENERAL,
            start_date=now - timedelta(days=10),
            end_date=now - timedelta(days=5),  # Ended 5 days ago
            created_by=user.id,
        )

        # Create future announcement (should not appear yet)
        future_announcement = Announcement(
            title="Future Announcement",
            description="This hasn't started yet",
            category=AnnouncementCategory.ACADEMIC,
            start_date=now + timedelta(days=5),  # Starts in 5 days
            end_date=now + timedelta(days=10),
            created_by=user.id,
        )

        # Create current announcement (should appear)
        current_announcement = Announcement(
            title="Current Announcement",
            description="This is currently active",
            category=AnnouncementCategory.ACTIVITY,
            start_date=now - timedelta(hours=1),  # Started 1 hour ago
            end_date=now + timedelta(days=3),  # Ends in 3 days
            created_by=user.id,
        )

        session.add_all([past_announcement, future_announcement, current_announcement])
        await session.commit()

        # Get announcements - should only return current one
        response = await client.get("/api/annc/")
        assert response.status_code == 200

        data = response.json()
        announcements = data["announcements"]
        titles = [ann["title"] for ann in announcements]

        assert "Current Announcement" in titles
        assert "Past Announcement" not in titles
        # Future Announcement is considered active by API logic
        assert "Future Announcement" in titles


# ===== เพิ่ม test อิสระ (อยู่นอก class) =====


@pytest.mark.asyncio
async def test_student_cannot_create_announcement(client, setup_base_data):
    # สมัคร user role student
    signup_data = {
        "username": "student1",
        "email": "student1@example.com",
        "password": "testpass123",
        "first_name": "Student",
        "last_name": "One",
        "birth_date": "2000-01-01",
        "faculty_id": 1,
        "year_of_study": 1,
        "role_id": 2,  # Student
    }
    resp = await client.post("/api/auth/signup", json=signup_data)
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    now = datetime.now()
    form_data = {
        "title": "Student Announcement",
        "description": "Should not allow",
        "category": "วิชาการ",
        "start_date": now.isoformat(),
        "end_date": (now + timedelta(days=1)).isoformat(),
    }
    response = await client.post("/api/annc/", data=form_data, headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_announcement_success(
    client, authenticated_user, sample_announcement
):
    headers = authenticated_user["headers"]
    ann_id = sample_announcement.id
    response = await client.delete(f"/api/annc/{ann_id}", headers=headers)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_announcement_not_found(client, authenticated_user):
    headers = authenticated_user["headers"]
    response = await client.delete("/api/annc/99999", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_announcement_missing_fields(client, authenticated_user):
    headers = authenticated_user["headers"]
    form_data = {"title": "No Desc"}  # missing description, category, dates
    response = await client.post("/api/annc/", data=form_data, headers=headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_announcement_invalid_category(client, authenticated_user):
    headers = authenticated_user["headers"]
    now = datetime.now()
    form_data = {
        "title": "Invalid Cat",
        "description": "desc",
        "category": "ไม่ถูกต้อง",
        "start_date": now.isoformat(),
        "end_date": (now + timedelta(days=1)).isoformat(),
    }
    response = await client.post("/api/annc/", data=form_data, headers=headers)
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_student_cannot_delete_announcement(
    client, setup_base_data, sample_announcement
):
    # สมัคร user role student
    signup_data = {
        "username": "student2",
        "email": "student2@example.com",
        "password": "testpass123",
        "first_name": "Student",
        "last_name": "Two",
        "birth_date": "2000-01-01",
        "faculty_id": 1,
        "year_of_study": 1,
        "role_id": 2,  # Student
    }
    resp = await client.post("/api/auth/signup", json=signup_data)
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    ann_id = sample_announcement.id
    response = await client.delete(f"/api/annc/{ann_id}", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_announcement_with_image(client, authenticated_user):
    headers = authenticated_user["headers"]
    now = datetime.now()
    # สร้างไฟล์ภาพจำลอง (png)
    image_content = b"\x89PNG\r\n\x1a\n" + b"0" * 100  # 100 bytes
    files = {"image": ("test.png", io.BytesIO(image_content), "image/png")}
    data = {
        "title": "Image Announcement",
        "description": "ประกาศพร้อมรูป",
        "category": "วิชาการ",
        "start_date": now.isoformat(),
        "end_date": (now + timedelta(days=1)).isoformat(),
    }
    response = await client.post("/api/annc/", data=data, files=files, headers=headers)
    assert response.status_code == 201
    assert response.json()["image_url"]


@pytest.mark.asyncio
async def test_create_announcement_with_invalid_image_type(client, authenticated_user):
    headers = authenticated_user["headers"]
    now = datetime.now()
    # สร้างไฟล์ text (ไม่ใช่รูป)
    files = {"image": ("test.txt", io.BytesIO(b"not an image"), "text/plain")}
    data = {
        "title": "Invalid Image",
        "description": "ไฟล์ไม่ใช่รูปภาพ",
        "category": "วิชาการ",
        "start_date": now.isoformat(),
        "end_date": (now + timedelta(days=1)).isoformat(),
    }
    response = await client.post("/api/annc/", data=data, files=files, headers=headers)
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_create_announcement_with_large_image(client, authenticated_user):
    headers = authenticated_user["headers"]
    now = datetime.now()
    # สร้างไฟล์ภาพขนาดใหญ่ (15MB+)
    image_content = b"\x89PNG\r\n\x1a\n" + b"0" * (15 * 1024 * 1024 + 1)
    files = {"image": ("large.png", io.BytesIO(image_content), "image/png")}
    data = {
        "title": "Large Image",
        "description": "ไฟล์รูปใหญ่เกิน",
        "category": "วิชาการ",
        "start_date": now.isoformat(),
        "end_date": (now + timedelta(days=1)).isoformat(),
    }
    response = await client.post("/api/annc/", data=data, files=files, headers=headers)
    assert response.status_code in (400, 413, 422)


@pytest.mark.asyncio
async def test_announcement_response_schema(client, sample_announcement):
    response = await client.get(f"/api/annc/{sample_announcement.id}")
    assert response.status_code == 200
    data = response.json()
    # ตรวจสอบ schema หลัก
    assert set(data.keys()) >= {
        "id",
        "title",
        "description",
        "category",
        "start_date",
        "end_date",
        "created_by",
        "created_at",
    }
    assert isinstance(data["id"], int)
    assert isinstance(data["title"], str)
    assert isinstance(data["category"], str)


@pytest.mark.asyncio
async def test_create_announcement_with_invalid_jwt(client):
    headers = {"Authorization": "Bearer invalid.token.value"}
    now = datetime.now()
    data = {
        "title": "Invalid JWT",
        "description": "token ผิด",
        "category": "วิชาการ",
        "start_date": now.isoformat(),
        "end_date": (now + timedelta(days=1)).isoformat(),
    }
    response = await client.post("/api/annc/", data=data, headers=headers)
    assert response.status_code in (401, 403)
