# CampHub Backend API

A modern FastAPI backend for CampHub with async database operations, JWT authentication, and PostgreSQL support.

## Features

- 🚀 **FastAPI** - Modern, fast web framework for building APIs
- 🔐 **JWT Authentication** - Secure token-based authentication
- 📊 **PostgreSQL + AsyncPG** - Async database operations
- 📋 **SQLModel** - Type-safe database models with Pydantic
- 📝 **API Documentation** - Auto-generated with Swagger UI

## Project Structure

```
app/
├── core/
│   ├── config.py          # Settings and configuration
│   ├── security.py        # JWT and password hashing
│   └── deps.py            # Dependencies (auth, db)
├── models/
│   ├── __init__.py        # Database setup and exports
│   ├── user_model.py      # User model
│   ├── faculty_model.py   # Faculty model
│   └── role_model.py      # Role model
├── routers/
│   └── endpoints/
│       ├── auth_route.py  # Authentication endpoints
│       └── user_route.py  # User management endpoints
├── schemas/
│   ├── user_schema.py     # User request/response schemas
│   ├── faculty_schema.py  # Faculty schemas
│   └── role_schema.py     # Role schemas
└── main.py               # FastAPI application entry point
```

---

## 1. How to Initial Setup After Clone This Git

### Prerequisites

- Python 3.12
- Docker and Docker Compose
- Git


### Default Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@camphub.com | admin123 |
| Professor | prof.smith@camphub.com | prof123 |
| Student | student.doe@camphub.com | student123 |



### Step-by-Step Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/krahyor/backend_camphub.git
   cd backend_camphub
   ```

2. **Create and activate virtual environment**

   ```bash
   # Create virtual environment
   python -m venv .venv

   # Activate virtual environment
   # Windows:
   venv/Scripts/activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Poetry in the virtual environment**

   ```bash
   # Install Poetry using pip in the activated venv
   pip install poetry

   # Verify Poetry installation
   poetry --version
   ```

4. **Install project dependencies with Poetry**

   ```bash
   # Install all dependencies from pyproject.toml
   poetry install
   ```

5. **Setup PostgreSQL Database with Docker Compose**

   ```bash
   # Start PostgreSQL container (database will be created automatically)
   docker-compose up -d db

   # Verify database is running
   docker-compose ps
   ```

   The Docker setup automatically creates:

   - Database: `camphub`
   - Username: `postgres`
   - Password: `postgres`
   - Port: `5432`

6. **Environment Configuration**

   - Copy `.env.example` to `.env` (if exists) or create `.env` file:

   ```bash
   cp .env.example .env
   ```

   - Edit `.env` file with your database credentials (for Docker setup):

   ```env
   SQLDB_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/camphub
   SECRET_KEY=your-super-secret-key-change-in-production
   JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
   JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
   JWT_REFRESH_TOKEN_EXPIRE_MINUTES=10080
   JWT_ALGORITHM=HS256
   ```

7. **Initialize Database**
   ```bash
   # Run database initialization (make sure venv is activated)
   poetry run python -c "import asyncio; from app.models import init_db; asyncio.run(init_db())"
   # Or Use
   poetry run python init_db.py
   ```

---

## 2. How to Build

This FastAPI project doesn't require a traditional "build" process, but here are the preparation steps:

### Development Setup

```bash
# Make sure venv is activated first
# Install development dependencies (if not already included)
poetry add --group dev pytest pytest-asyncio httpx black flake8

# Verify installation
poetry run python -c "from app.main import app; print('✅ App imports successfully')"
```

### Production Preparation

```bash
# Make sure venv is activated first
# Install production server
poetry add gunicorn

# Export requirements.txt if needed (for Docker or other deployment)
poetry export -f requirements.txt --output requirements.txt

# Run database migrations/initialization
poetry run python -c "import asyncio; from app.models import init_db; asyncio.run(init_db())"
```

### Docker Build (Optional)

```bash
# If you have Dockerfile
docker build -t camphub-backend .
```

---

## 3. How to Run

### Prerequisites for Running

1. **Start PostgreSQL with Docker Compose**

   ```bash
   # Start the database (if not already running)
   docker-compose up -d postgres

   # Check if database is running
   docker-compose ps
   ```

### Development Mode

1. **Start the development server**

   ```bash
   # Make sure virtual environment is activated first
   # Windows: venv\Scripts\activate
   # macOS/Linux: source venv/bin/activate

   # Run using FastAPI dev command (Recommended)
   poetry run fastapi dev app/main.py

   # Alternative: using uvicorn directly
   poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Access the application**
   - API: http://localhost:8000
   - Interactive API docs: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

### Production Mode

1. **Using Gunicorn (Recommended)**

   ```bash
   # Make sure venv is activated, then run with Poetry
   poetry run gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

2. **Using Uvicorn**
   ```bash
   # Make sure venv is activated, then run with Poetry
   poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

### Docker Run (Optional)

```bash
docker run -p 8000:8000 camphub-backend
```

---

## API Endpoints

### Authentication

- `POST /api/auth/signup` - User registration
- `POST /api/auth/signin` - User login (email + password)

### User Management

- `GET /api/user` - Get current user profile
- `PUT /api/user` - Update user profile

### API Documentation

- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation

---

## Default Demo User

The application creates a demo user on first startup:

- **Email:** demo@mail.com
- **Password:** 123456
- **Username:** user_demo

---

## Environment Variables

| Variable                           | Description                  | Default  |
| ---------------------------------- | ---------------------------- | -------- |
| `SQLDB_URL`                        | PostgreSQL connection string | Required |
| `SECRET_KEY`                       | Application secret key       | Required |
| `JWT_SECRET_KEY`                   | JWT signing key              | Required |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`  | Access token expiry          | 60       |
| `JWT_REFRESH_TOKEN_EXPIRE_MINUTES` | Refresh token expiry         | 10080    |
| `JWT_ALGORITHM`                    | JWT algorithm                | HS256    |

---

## Database Models

- **User**: Student/Professor with email authentication
- **Faculty**: Academic faculties/departments
- **Role**: User roles (1=Professor, 2=Student)

---

## Development

### Running Tests

```bash
# Make sure venv is activated first
poetry run pytest
```

### Code Quality

```bash
# Make sure venv is activated first
# Format code
poetry run black app/

# Lint code
poetry run flake8 app/
```

### Adding New Dependencies

```bash
# Make sure venv is activated first
# Add runtime dependency
poetry add package-name

# Add development dependency
poetry add --group dev package-name

# Update dependencies
poetry update
```

### Virtual Environment Management

```bash
# Activate venv (do this first)
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Deactivate venv
deactivate

# Show Poetry environment info
poetry env info

# Show installed packages
poetry show
```

---

## Troubleshooting

### Common Issues

1. **Database Connection Error**

   - Check PostgreSQL is running
   - Verify credentials in `.env`
   - Ensure database exists

2. **Import Errors**

   - Activate venv first: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (macOS/Linux)
   - Install missing dependencies: `poetry install`

3. **Permission Errors**

   - Check database user permissions
   - Verify file permissions

4. **Poetry Issues**
   - Make sure venv is activated first
   - Update Poetry: `pip install --upgrade poetry` (in activated venv)
   - Clear cache: `poetry cache clear pypi --all`
   - Reinstall dependencies: `poetry install --no-cache`

### Logs

```bash
# Make sure venv is activated first, then view application logs
poetry run uvicorn app.main:app --log-level debug
```

---
