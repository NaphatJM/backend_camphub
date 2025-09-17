"""
Database initialization and seeding script
"""

from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import User, Role, Faculty, Course, CourseSchedule, async_engine
from app.core.security import hash_password
from app.models.announcement_model import Announcement


async def init_roles():
    """Initialize default roles"""
    async with AsyncSession(async_engine) as session:
        result = await session.execute(select(Role))
        existing_roles = result.scalars().all()

        if not existing_roles:
            roles = [
                Role(
                    id=1,
                    name="Professor",
                    description="Faculty member who can teach courses",
                ),
                Role(
                    id=2,
                    name="Student",
                    description="Student who can enroll in courses",
                ),
                Role(
                    id=3,
                    name="Admin",
                    description="System administrator with full access",
                ),
            ]
            session.add_all(roles)
            await session.commit()
            print("Default roles created")
        else:
            print("Roles already exist")


async def init_faculties():
    """Initialize default faculties"""
    async with AsyncSession(async_engine) as session:
        result = await session.execute(select(Faculty))
        existing_faculties = result.scalars().all()

        if not existing_faculties:
            faculties = [
                Faculty(name="วิศวกรรมศาสตร์"),
                Faculty(name="วิทยาศาสตร์"),
                Faculty(name="ครุศาสตร์"),
                Faculty(name="มนุษยศาสตร์"),
                Faculty(name="สังคมศาสตร์"),
                Faculty(name="บริหารธุรกิจ"),
                Faculty(name="เทคโนโลยีสารสนเทศ"),
                Faculty(name="การแพทย์"),
            ]
            session.add_all(faculties)
            await session.commit()
            print("Default faculties created")
        else:
            print("Faculties already exist")


async def init_demo_users():
    """Initialize demo users"""
    async with AsyncSession(async_engine) as session:
        result = await session.execute(select(User))
        existing_users = result.scalars().all()

        if not existing_users:
            eng_faculty = await session.execute(
                select(Faculty).where(Faculty.name == "วิศวกรรมศาสตร์")
            )
            eng_faculty = eng_faculty.scalars().first()

            it_faculty = await session.execute(
                select(Faculty).where(Faculty.name == "เทคโนโลยีสารสนเทศ")
            )
            it_faculty = it_faculty.scalars().first()

            users = [
                # Admin user
                User(
                    username="admin",
                    email="admin@camphub.com",
                    first_name="Admin",
                    last_name="User",
                    birth_date=date(1980, 1, 1),
                    hashed_password=hash_password("admin123"),
                    role_id=3,  # Admin
                ),
                # Professor
                User(
                    username="prof.smith",
                    email="prof.smith@camphub.com",
                    first_name="John",
                    last_name="Smith",
                    birth_date=date(1975, 5, 15),
                    faculty_id=eng_faculty.id if eng_faculty else 1,
                    hashed_password=hash_password("prof123"),
                    role_id=1,  # Professor
                ),
                # Student
                User(
                    username="student.doe",
                    email="student.doe@camphub.com",
                    first_name="Jane",
                    last_name="Doe",
                    birth_date=date(2000, 8, 20),
                    faculty_id=it_faculty.id if it_faculty else 2,
                    year_of_study=3,
                    hashed_password=hash_password("student123"),
                    role_id=2,  # Student
                ),
            ]
            session.add_all(users)
            await session.commit()
            print("Demo users created")
        else:
            print("Users already exist")


async def init_demo_announcements():
    async with AsyncSession(async_engine) as session:
        result = await session.execute(select(Announcement))
        existing_announcements = result.scalars().all()

        if not existing_announcements:
            from datetime import datetime, timedelta

            now = datetime.now()

            announcements = [
                Announcement(
                    title="Welcome to CampHub",
                    content="We are excited to have you on our platform!",
                    description="Official welcome message for all new users joining CampHub platform",
                    image_url="https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=800",
                    start_date=now,
                    end_date=now + timedelta(days=30),
                    created_by=1,
                ),
                Announcement(
                    title="Course Registration Open",
                    content="Register for your courses now! Don't miss the deadline.",
                    description="Course registration for the upcoming semester is now open. Students can register through the student portal.",
                    image_url="https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=800",
                    start_date=now,
                    end_date=now + timedelta(days=14),
                    created_by=1,
                ),
                Announcement(
                    title="Campus Library Hours Extended",
                    content="Library will be open 24/7 during exam period starting next week.",
                    description="To support students during the examination period, the campus library will extend its operating hours to 24/7 for the next two weeks.",
                    image_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800",
                    start_date=now + timedelta(days=7),
                    end_date=now + timedelta(days=21),
                    created_by=3,
                ),
            ]
            session.add_all(announcements)
            await session.commit()
            print("Demo announcements created")
        else:
            print("Announcements already exist")


async def init_demo_courses():
    """Initialize demo courses"""
    async with AsyncSession(async_engine) as session:
        # Check if courses already exist
        result = await session.execute(select(Course))
        existing_courses = result.scalars().all()

        if not existing_courses:
            courses = [
                Course(
                    course_code="CS101",
                    course_name="Introduction to Programming",
                    credits=3,
                    available_seats=40,
                    description="Learn the basics of programming using Python",
                ),
                Course(
                    course_code="CS201",
                    course_name="Data Structures and Algorithms",
                    credits=3,
                    available_seats=35,
                    description="Advanced programming concepts and algorithms",
                ),
                Course(
                    course_code="CS301",
                    course_name="Database Systems",
                    credits=3,
                    available_seats=30,
                    description="Database design and management",
                ),
                Course(
                    course_code="ENG101",
                    course_name="Engineering Mathematics",
                    credits=4,
                    available_seats=50,
                    description="Mathematical foundations for engineering",
                ),
                Course(
                    course_code="WEB201",
                    course_name="Web Development",
                    credits=3,
                    available_seats=25,
                    description="Full-stack web development with modern frameworks",
                ),
            ]
            session.add_all(courses)
            await session.flush()

            print("Demo courses created")
        else:
            print("Courses already exist")


async def init_all_data():
    """Initialize all required data"""
    print("Starting database initialization...")

    try:
        await init_roles()
        await init_faculties()
        await init_demo_users()
        await init_demo_announcements()
        await init_demo_courses()

        print("Database initialization completed successfully!")

    except Exception as e:
        print(f"Error during database initialization: {e}")
        raise


if __name__ == "__main__":
    import asyncio
    from app.models import init_db

    async def main():
        # Create tables first
        await init_db()
        print("Database tables created")

        # Initialize data
        await init_all_data()

    asyncio.run(main())
