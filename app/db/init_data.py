"""
Database initialization and seeding script with locations and rooms
"""

from datetime import date, datetime, time, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.db import async_engine
from app.models import (
    User,
    Role,
    Faculty,
    Course,
    CourseSchedule,
    Enrollment,
    Location,
    Room,
)
from app.core.security import hash_password
from app.models.announcement_model import Announcement
from app.models.event_model import Event


# ---------------------------
# Roles
# ---------------------------
async def init_roles():
    async with AsyncSession(async_engine) as session:
        result = await session.execute(select(Role))
        existing_roles = result.scalars().all()
        if existing_roles:
            print("Roles already exist")
            return

        roles = [
            Role(
                id=1,
                name="Professor",
                description="Faculty member who can teach courses",
            ),
            Role(id=2, name="Student", description="Student who can enroll in courses"),
            Role(
                id=3, name="Admin", description="System administrator with full access"
            ),
        ]
        session.add_all(roles)
        await session.commit()
        print("Default roles created")


# ---------------------------
# Faculties
# ---------------------------
async def init_faculties():
    async with AsyncSession(async_engine) as session:
        result = await session.execute(select(Faculty))
        existing_faculties = result.scalars().all()
        if existing_faculties:
            print("Faculties already exist")
            return

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


# ---------------------------
# Demo Users
# ---------------------------
async def init_demo_users():
    async with AsyncSession(async_engine) as session:
        result = await session.execute(select(User))
        if result.scalars().first():
            print("Users already exist")
            return

        eng_faculty = await session.execute(
            select(Faculty).where(Faculty.name == "วิศวกรรมศาสตร์")
        )
        eng_faculty = eng_faculty.scalars().first()

        it_faculty = await session.execute(
            select(Faculty).where(Faculty.name == "เทคโนโลยีสารสนเทศ")
        )
        it_faculty = it_faculty.scalars().first()

        users = [
            User(
                username="admin",
                email="admin@camphub.com",
                first_name="Admin",
                last_name="User",
                birth_date=date(1980, 1, 1),
                hashed_password=hash_password("admin123"),
                role_id=3,
            ),
            User(
                username="prof.smith",
                email="prof.smith@camphub.com",
                first_name="John",
                last_name="Smith",
                birth_date=date(1975, 5, 15),
                faculty_id=eng_faculty.id if eng_faculty else 1,
                hashed_password=hash_password("prof123"),
                role_id=1,
            ),
            User(
                username="student.doe",
                email="student.doe@camphub.com",
                first_name="Jane",
                last_name="Doe",
                birth_date=date(2000, 8, 20),
                faculty_id=it_faculty.id if it_faculty else 2,
                year_of_study=3,
                hashed_password=hash_password("student123"),
                role_id=2,
            ),
        ]
        session.add_all(users)
        await session.commit()
        print("Demo users created")


async def init_demo_events():
    """Initialize demo events"""
    async with AsyncSession(async_engine) as session:
        result = await session.execute(select(Event))
        existing_events = result.scalars().all()

        if not existing_events:
            from datetime import datetime, timedelta

            now = datetime.now()

            events = [
                Event(
                    title="วันแนะแนวการศึกษาต่อ",
                    description="งานแสดงสาขาวิชาและการแนะแนวการศึกษาต่อระดับปริญญาตรี พร้อมปรึกษาอาจารย์และรุ่นพี่",
                    start_date=now + timedelta(days=10),
                    end_date=now + timedelta(days=10, hours=8),
                    capacity=200,
                    is_active=True,
                    image_url="https://images.unsplash.com/photo-1758691736591-5bf31a5d0dea?q=80&w=1332&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
                    created_by=1,  # Admin
                    updated_by=1,
                    created_at=now,
                    updated_at=now,
                ),
                Event(
                    title="การแข่งขันตอบปัญหาทางวิทยาศาสตร์",
                    description="การแข่งขันตอบปัญหาทางวิทยาศาสตร์และคณิตศาสตร์ระหว่างคณะ เปิดรับสมัครนักศึกษาทุกชั้นปี รางวัลรวมมูลค่า 50,000 บาท",
                    start_date=now + timedelta(days=15),
                    end_date=now + timedelta(days=15, hours=6),
                    capacity=100,
                    is_active=True,
                    image_url="https://images.unsplash.com/photo-1758685848261-16a5a9e68811?q=80&w=1332&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
                    created_by=2,  # Professor
                    updated_by=2,
                    created_at=now,
                    updated_at=now,
                ),
                Event(
                    title="งานกีฬาสีประจำปี",
                    description="งานกีฬาสีประจำปีของมหาวิทยาลัย แข่งขันกีฬาหลากหลายประเภท ทั้งกีฬาในร่มและกลางแจ้ง เชิญชวนนักศึกษาทุกคนร่วมเชียร์และเป็นส่วนหนึ่งของความสนุกสนาน",
                    start_date=now + timedelta(days=25),
                    end_date=now + timedelta(days=27),
                    capacity=500,
                    is_active=True,
                    image_url="https://images.unsplash.com/photo-1572579967902-154db90ca5be?q=80&w=1169&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
                    created_by=1,  # Admin
                    updated_by=1,
                    created_at=now,
                    updated_at=now,
                ),
            ]
            session.add_all(events)
            await session.commit()
            print("Demo events created")
        else:
            print("Events already exist")


async def init_demo_announcements():
    async with AsyncSession(async_engine) as session:
        result = await session.execute(select(Announcement))
        existing_announcements = result.scalars().all()

        if not existing_announcements:
            from datetime import datetime, timedelta

            now = datetime.now()

            announcements = [
                Announcement(
                    title="ยินดีต้อนรับสู่ CampHub",
                    content="เรายินดีต้อนรับคุณเข้าสู่แพลตฟอร์มของเรา!",
                    description="ข้อความต้อนรับอย่างเป็นทางการสำหรับผู้ใช้งานใหม่ทุกคนที่เข้าร่วมแพลตฟอร์ม CampHub",
                    image_url="https://images.unsplash.com/photo-1560265036-021b3652b490?q=80&w=1332&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
                    start_date=now,
                    end_date=now + timedelta(days=30),
                    created_by=1,
                ),
                Announcement(
                    title="เปิดรับสมัครลงทะเบียนเรียน",
                    content="ลงทะเบียนเรียนของคุณเดี๋ยวนี้! อย่าพลาดกำหนดเวลา",
                    description="การลงทะเบียนเรียนสำหรับภาคการศึกษาที่กำลังจะมาถึงเปิดให้บริการแล้ว นักศึกษาสามารถลงทะเบียนผ่านระบบพอร์ทัลนักศึกษา",
                    image_url="https://images.unsplash.com/photo-1613160058266-ed84e3251760?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
                    start_date=now,
                    end_date=now + timedelta(days=14),
                    created_by=1,
                ),
                Announcement(
                    title="ขยายเวลาเปิดห้องสมุดในช่วงสอบ",
                    content="ห้องสมุดจะเปิดบริการ 24 ชั่วโมงในช่วงสอบเริ่มสัปดาห์หน้า",
                    description="เพื่อสนับสนุนนักศึกษาในช่วงสอบ ห้องสมุดมหาวิทยาลัยจะขยายเวลาเปิดบริการเป็น 24 ชั่วโมงเป็นเวลา 2 สัปดาห์",
                    image_url="https://images.unsplash.com/photo-1508169351866-777fc0047ac5?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
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


# ---------------------------
# Locations & Rooms
# ---------------------------
async def init_locations_and_rooms():
    async with AsyncSession(async_engine) as session:
        # Locations
        result = await session.execute(select(Location))
        if result.scalars().first():
            print("Locations already exist")
            return

        loc1 = Location(
            name="อาคารเรียนรวม 1", code="B1", latitude=13.736717, longitude=100.523186
        )
        loc2 = Location(
            name="อาคารวิศวกรรมศาสตร์", code="ENG", latitude=13.7375, longitude=100.5250
        )

        session.add_all([loc1, loc2])
        await session.flush()  # เพื่อให้ได้ id ของ location

        # Rooms
        room1 = Room(
            name="A101",
            location_id=loc1.id,
            description="ห้องเรียนใหญ่ชั้น 1 อาคารเรียนรวม 1",
        )
        room2 = Room(
            name="B201",
            location_id=loc2.id,
            description="ห้องเรียนชั้น 2 อาคารวิศวกรรมศาสตร์",
        )
        room3 = Room(
            name="C301",
            location_id=loc2.id,
            description="ห้องเรียนชั้น 3 อาคารวิศวกรรมศาสตร์",
        )

        session.add_all([room1, room2, room3])
        await session.commit()
        print("Locations and rooms created")


# ---------------------------
# Courses + CourseSchedule
# ---------------------------
async def init_demo_courses():
    async with AsyncSession(async_engine) as session:
        if (await session.execute(select(Course))).scalars().first():
            print("Courses already exist")
            return

        teacher = await session.execute(select(User).where(User.id == 2))
        teacher = teacher.scalars().first()
        if not teacher:
            print("❌ Teacher user not found")
            return

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

        for c in [course1, course2, course3]:
            c.teachers.append(teacher)

        session.add_all([course1, course2, course3])
        await session.flush()  # เพื่อให้ได้ course.id

        # ดึง room
        rooms = await session.execute(select(Room))
        rooms = rooms.scalars().all()
        room_dict = {r.name: r.id for r in rooms}

        # CourseSchedule
        schedules = [
            CourseSchedule(
                course_id=course1.id,
                day_of_week="Monday",
                start_time=time(9, 0),
                end_time=time(11, 0),
                room_id=room_dict["A101"],
            ),
            CourseSchedule(
                course_id=course1.id,
                day_of_week="Monday",
                start_time=time(13, 0),
                end_time=time(15, 0),
                room_id=room_dict["A101"],
            ),
            CourseSchedule(
                course_id=course1.id,
                day_of_week="Friday",
                start_time=time(9, 0),
                end_time=time(11, 0),
                room_id=room_dict["A101"],
            ),
            CourseSchedule(
                course_id=course2.id,
                day_of_week="Wednesday",
                start_time=time(13, 0),
                end_time=time(15, 0),
                room_id=room_dict["B201"],
            ),
            CourseSchedule(
                course_id=course3.id,
                day_of_week="Friday",
                start_time=time(10, 0),
                end_time=time(12, 0),
                room_id=room_dict["C301"],
            ),
        ]

        session.add_all(schedules)
        await session.commit()
        print("Demo courses and schedules created")


async def init_demo_enrollments():
    async with AsyncSession(async_engine) as session:
        # ตรวจสอบว่ามี enrollment อยู่แล้วหรือยัง
        result = await session.execute(select(Enrollment))
        if result.scalars().first():
            print("Enrollments already exist")
            return

        # โหลดผู้ใช้งานและคอร์ส
        users_result = await session.execute(select(User))
        users = users_result.scalars().all()

        courses_result = await session.execute(select(Course))
        courses = courses_result.scalars().all()

        # สร้าง enrollment ตัวอย่าง
        enrollments = [
            Enrollment(
                course_id=courses[0].id,
                user_id=users[2].id,  # student.doe
                status="enrolled",
                enrollment_at=datetime.now(),
            ),
            Enrollment(
                course_id=courses[1].id,
                user_id=users[2].id,
                status="enrolled",
                enrollment_at=datetime.now(),
            ),
            Enrollment(
                course_id=courses[2].id,
                user_id=users[2].id,
                status="enrolled",
                enrollment_at=datetime.now(),
            ),
            Enrollment(
                course_id=courses[0].id,
                user_id=users[0].id,
                status="enrolled",
                enrollment_at=datetime.now(),
            ),
            Enrollment(
                course_id=courses[1].id,
                user_id=users[0].id,
                status="enrolled",
                enrollment_at=datetime.now(),
            ),
            Enrollment(
                course_id=courses[2].id,
                user_id=users[0].id,
                status="enrolled",
                enrollment_at=datetime.now(),
            ),
        ]

        session.add_all(enrollments)
        await session.commit()
        print("Demo enrollments created")


# ---------------------------
# Initialize all data
# ---------------------------
async def init_all_data():
    await init_roles()
    await init_faculties()
    await init_demo_users()
    await init_demo_events()
    await init_demo_announcements()
    await init_locations_and_rooms()
    await init_demo_courses()
    await init_demo_enrollments()
    print("Database initialization completed successfully!")


if __name__ == "__main__":
    import asyncio
    from app.core.db import init_db

    async def main():
        await init_db()
        print("Database tables created")
        await init_all_data()

    asyncio.run(main())
