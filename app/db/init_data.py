"""
Database initialization and seeding script
"""

from datetime import date, datetime, time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.db import async_engine
from app.models import User, Role, Faculty, Course, CourseSchedule
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
    async with AsyncSession(async_engine) as session:
        # --- ตรวจว่ามี course อยู่แล้วไหม ---
        result = await session.execute(select(Course))
        existing_courses = result.scalars().all()

        if existing_courses:
            print("Courses already exist")
            return

        # --- หา teacher id=2 ---
        result = await session.execute(select(User).where(User.id == 2))
        teacher = result.scalars().first()
        if not teacher:
            print("❌ ไม่พบ User id=2 ที่เป็น teacher, seed ไม่สำเร็จ")
            return

        # --- สร้าง courses ---
        course1 = Course(
            course_code="CS101",
            course_name="Introduction to Computer Science",
            credits=3,
            available_seats=50,
            description="พื้นฐานการเขียนโปรแกรมและโครงสร้างข้อมูลเบื้องต้น",
            created_at=datetime.now(),
        )
        course2 = Course(
            course_code="MA201",
            course_name="Advanced Mathematics",
            credits=4,
            available_seats=40,
            description="คณิตศาสตร์ระดับสูงสำหรับวิศวกรรม",
            created_at=datetime.now(),
        )
        course3 = Course(
            course_code="PHY301",
            course_name="Physics for Engineers",
            credits=3,
            available_seats=35,
            description="ฟิสิกส์ประยุกต์สำหรับวิศวกรรม",
            created_at=datetime.now(),
        )

        # --- ผูก teacher id=2 เข้ากับทุก course ---
        for c in [course1, course2, course3]:
            c.teachers.append(teacher)

        session.add_all([course1, course2, course3])
        await session.flush()  # เพื่อให้ได้ course.id ก่อนสร้าง schedule

        # --- เพิ่ม CourseSchedule ---
        schedules = [
            CourseSchedule(
                course_id=course1.id,
                day_of_week="Monday",
                start_time=time(9, 0),
                end_time=time(11, 0),
                room="Room A101",
            ),
            CourseSchedule(
                course_id=course1.id,
                day_of_week="Monday",
                start_time=time(13, 0),
                end_time=time(15, 0),
                room="Room A101",
            ),
            CourseSchedule(
                course_id=course1.id,
                day_of_week="Friday",
                start_time=time(9, 0),
                end_time=time(11, 0),
                room="Room A101",
            ),
            CourseSchedule(
                course_id=course2.id,
                day_of_week="Wednesday",
                start_time=time(13, 0),
                end_time=time(15, 0),
                room="Room B201",
            ),
            CourseSchedule(
                course_id=course3.id,
                day_of_week="Friday",
                start_time=time(10, 0),
                end_time=time(12, 0),
                room="Room C301",
            ),
        ]
        session.add_all(schedules)

        await session.commit()
        print("🎉 Demo courses + schedules created")


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
