# CampHub Backend Tests

Integration tests สำหรับ CampHub Backend API ที่ทดสอบการเชื่อมต่อระหว่าง API endpoints, database และ business logic

## การติดตั้ง

1. ติดตั้ง dependencies:
```bash
pip install pytest pytest-asyncio httpx
```

2. ตั้งค่า environment variables (ถ้าจำเป็น):
```bash
# ไม่จำเป็นสำหรับ tests เนื่องจากใช้ SQLite in-memory
```

## การรัน Tests

### รัน tests ทั้งหมด:
```bash
python -m pytest tests/ -v
```

### รัน test file เฉพาะ:
```bash
python -m pytest tests/test_auth.py -v
python -m pytest tests/test_user.py -v
python -m pytest tests/test_courses.py -v
python -m pytest tests/test_enrollment.py -v
python -m pytest tests/test_announcement.py -v
```

### รัน test function เฉพาะ:
```bash
python -m pytest tests/test_auth.py::TestAuth::test_signup_success -v
```

### รันด้วย coverage report:
```bash
python -m pytest tests/ --cov=app --cov-report=html -v
```

### รันแบบ silent (เฉพาะผลลัพธ์):
```bash
python -m pytest tests/ -q
```

## โครงสร้าง Tests

```
tests/
├── __init__.py              # Empty init file
├── conftest.py             # Pytest fixtures และ configuration
├── test_auth.py            # Tests สำหรับ authentication endpoints
├── test_user.py            # Tests สำหรับ user management endpoints  
├── test_courses.py         # Tests สำหรับ course management endpoints
├── test_enrollment.py      # Tests สำหรับ enrollment system
├── test_announcement.py    # Tests สำหรับ announcement system
├── test_utils.py          # Helper utilities และ test data factories
├── run_tests.py           # Script สำหรับรัน tests
└── README.md              # คู่มือนี้
```

## Test Coverage

Tests ครอบคลุมพื้นที่หลัก:

### 1. Authentication (`test_auth.py`)
- ✅ User signup (success, duplicate username/email, validation)
- ✅ User signin (success, wrong credentials)
- ✅ Complete auth flow integration

### 2. User Management (`test_user.py`)
- ✅ Get current user profile
- ✅ Get user by ID
- ✅ Update user profile (success, validation, duplicates)
- ✅ Authorization checks

### 3. Course Management (`test_courses.py`)
- ✅ List all courses
- ✅ Get course by ID
- ✅ Create course (permissions, validation)
- ✅ Update course
- ✅ Delete course
- ✅ Complete CRUD flow

### 4. Enrollment System (`test_enrollment.py`)
- ✅ Course enrollment (success, duplicate, validation)
- ✅ Enrollment cancellation
- ✅ Get user enrollments
- ✅ Get course enrollments
- ✅ Multi-student enrollment scenarios

### 5. Announcement System (`test_announcement.py`)
- ✅ List announcements (with pagination, filtering)
- ✅ Get announcement by ID
- ✅ Create announcement (with validation)
- ✅ Active-only announcement filtering
- ✅ Category filtering

## Test Design Principles

### 1. Environment Setup
- ใช้ SQLite in-memory database สำหรับ tests
- Clean slate สำหรับทุก test (isolated)
- Dependency override สำหรับ database session

### 2. Test Structure
- **Arrange**: Setup test data และ authentication
- **Act**: เรียก API endpoint
- **Assert**: ตรวจสอบ response และ side effects

### 3. Data Isolation
- แต่ละ test ไม่ depend กัน
- Database reset ทุกครั้ง
- Independent test execution

### 4. Real Integration Testing  
- ทดสอบผ่าน HTTP client จริง
- ครอบคลุม API ↔ Database ↔ Business Logic
- ไม่ mock internal dependencies

## Test Fixtures

### Core Fixtures (`conftest.py`)
- `engine`: Test database engine (SQLite in-memory)
- `session`: Database session สำหรับแต่ละ test
- `client`: HTTP client พร้อม dependency override

### User Fixtures (ใน test files)
- `authenticated_user`: นักศึกษาที่ login แล้ว
- `teacher_user`: อาจารย์ที่ login แล้ว  
- `admin_user`: Admin user ที่ login แล้ว
- `setup_base_data`: ข้อมูลพื้นฐาน (roles, faculty)

### Data Fixtures
- `sample_course`: Course ตัวอย่าง
- `sample_announcement`: Announcement ตัวอย่าง
- `course_create_data`: ข้อมูลสำหรับสร้าง course

## การเขียน Test ใหม่

### 1. Test Structure Template:
```python
class TestFeatureName:
    """Test feature description."""

    @pytest.mark.asyncio
    async def test_happy_path_success(self, client, authenticated_user):
        """Test successful operation."""
        # Arrange
        headers = authenticated_user["headers"]
        data = {"field": "value"}
        
        # Act  
        response = await client.post("/api/endpoint", json=data, headers=headers)
        
        # Assert
        assert response.status_code == 200
        assert response.json()["field"] == "value"

    @pytest.mark.asyncio
    async def test_error_case(self, client):
        """Test error scenario."""
        # Test unauthorized, not found, validation errors, etc.
```

### 2. Best Practices:
- ใช้ descriptive test names
- Test ทั้ง happy path และ error cases  
- ใช้ fixtures สำหรับ common setup
- Assert ทั้ง status code และ response data
- Test business rules และ edge cases

## การ Debug Tests

### 1. รัน test เฉพาะที่ fail:
```bash
python -m pytest tests/test_auth.py::TestAuth::test_signup_success -v -s
```

### 2. ดู detailed output:
```bash
python -m pytest tests/ -v -s --tb=long
```

### 3. ใช้ print debugging:
```python
@pytest.mark.asyncio
async def test_debug_example(self, client):
    response = await client.get("/api/endpoint")
    print(f"Response: {response.json()}")  # จะแสดงเมื่อ run ด้วย -s
    assert response.status_code == 200
```

## Notes

- Tests ใช้ข้อมูลจริงจาก project (models, schemas, endpoints)
- ไม่มี external dependencies (network, files, etc.)
- รัน fast (< 1 นาทีสำหรับ test suite ทั้งหมด)
- Deterministic (ผลเหมือนเดิมทุกครั้ง)

## ตัวอย่างการรัน

```bash
# รัน tests ทั้งหมด
$ python -m pytest tests/ -v
======================== test session starts ========================
collected 45 items

tests/test_auth.py::TestAuth::test_signup_success PASSED        [ 11%]
tests/test_auth.py::TestAuth::test_signin_success PASSED        [ 22%]
tests/test_user.py::TestUser::test_get_me_success PASSED        [ 33%]
...
======================== 45 passed in 8.32s ========================
```
