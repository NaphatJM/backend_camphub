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
            Faculty(name="วิศวกรรมศาสตร์"),  # Engineering
            Faculty(name="วิทยาศาสตร์"),  # Sciences
            Faculty(name="อุตสาหกรรมเกษตร"),  # Agro-Industry
            Faculty(name="ทันตแพทยศาสตร์"),  # Dentistry
            Faculty(name="เศรษฐศาสตร์"),  # Economics
            Faculty(name="การจัดการสิ่งแวดล้อม"),  # Environment Management
            Faculty(name="นิติศาสตร์"),  # Law
            Faculty(name="ศิลปศาสตร์"),  # Liberal Arts
            Faculty(name="วิทยาการจัดการ"),  # Management Sciences
            Faculty(name="เทคนิคการแพทย์"),  # Medical Technology
            Faculty(name="แพทยศาสตร์"),  # Medicine
            Faculty(name="ทรัพยากรธรรมชาติ"),  # Natural Resources
            Faculty(name="พยาบาลศาสตร์"),  # Nursing
            Faculty(name="เภสัชศาสตร์"),  # Pharmaceutical Sciences
            Faculty(name="การแพทย์แผนไทย"),  # Traditional Thai Medicine
            Faculty(name="สัตวแพทยศาสตร์"),  # Veterinary Sciences
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

        science_faculty = await session.execute(
            select(Faculty).where(Faculty.name == "วิทยาศาสตร์")
        )
        science_faculty = science_faculty.scalars().first()

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
                faculty_id=science_faculty.id if science_faculty else None,
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
                    location="อาคารเรียนและปฏิบัติการพื้นฐานทางวิทยาศาสตร์",
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
                    location="อาคารวิจัยวิศวกรรมประยุกต์สิรินธร",
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
                    capacity=None,
                    is_active=True,
                    image_url="https://images.unsplash.com/photo-1572579967902-154db90ca5be?q=80&w=1169&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
                    location="อาคารเรียนและปฏิบัติการพื้นฐานทางวิทยาศาสตร์",
                    created_by=1,  # Admin
                    updated_by=1,
                    created_at=now,
                    updated_at=now,
                ),
                Event(
                    title="Tech Meetup 2025",
                    description="พบกับงาน Meetup สำหรับสายเทคโนโลยีและนวัตกรรม อัปเดตเทรนด์ใหม่ ๆ และ networking กับเพื่อน ๆ ในวงการ",
                    start_date=now + timedelta(days=30),
                    end_date=now + timedelta(days=30, hours=4),
                    capacity=300,
                    is_active=True,
                    image_url="https://images.unsplash.com/photo-1519389950473-47ba0277781c?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
                    location="อาคารวิจัยวิศวกรรมประยุกต์สิรินธร",
                    created_by=2,
                    updated_by=2,
                    created_at=now,
                    updated_at=now,
                ),
                Event(
                    title="อบรมการเขียนโปรแกรม Python เบื้องต้น",
                    description="Workshop สำหรับผู้เริ่มต้น Python สอนโดยอาจารย์ผู้เชี่ยวชาญ พร้อมใบประกาศนียบัตร",
                    start_date=now + timedelta(days=40),
                    end_date=now + timedelta(days=40, hours=6),
                    capacity=80,
                    is_active=True,
                    image_url="https://images.unsplash.com/photo-1660616246653-e2c57d1077b9?q=80&w=1331&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
                    location="อาคารเรียนและปฏิบัติการพื้นฐานทางวิทยาศาสตร์",
                    created_by=1,
                    updated_by=1,
                    created_at=now,
                    updated_at=now,
                ),
            ]
            events += [
                Event(
                    title="Open House 2025",
                    description="กิจกรรม Open House สำหรับนักเรียนมัธยมปลายและผู้ปกครอง เยี่ยมชมคณะและพบกับรุ่นพี่",
                    start_date=now + timedelta(days=45),
                    end_date=now + timedelta(days=45, hours=8),
                    capacity=400,
                    is_active=True,
                    image_url="https://images.unsplash.com/photo-1606761568499-6d2451b23c66?q=80&w=1074&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
                    location="อาคารวิจัยวิศวกรรมประยุกต์สิรินธร",
                    created_by=2,
                    updated_by=2,
                    created_at=now,
                    updated_at=now,
                ),
                Event(
                    title="ประกวด Startup Idea",
                    description="ขอเชิญชวนนักศึกษาส่งไอเดียธุรกิจ Startup ชิงเงินรางวัลและโอกาสเข้าร่วมโครงการบ่มเพาะ",
                    start_date=now + timedelta(days=50),
                    end_date=now + timedelta(days=50, hours=5),
                    capacity=120,
                    is_active=True,
                    image_url="https://images.unsplash.com/photo-1557804506-669a67965ba0?q=80&w=1074&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
                    location="อาคารเรียนและปฏิบัติการพื้นฐานทางวิทยาศาสตร์",
                    created_by=1,
                    updated_by=1,
                    created_at=now,
                    updated_at=now,
                ),
                Event(
                    title="กิจกรรม Movie Night",
                    description="Movie Night ชวนเพื่อน ๆ มาดูหนังกลางแปลงที่สนามหญ้าใหญ่ ฟรีป๊อปคอร์น!",
                    start_date=now + timedelta(days=55),
                    end_date=now + timedelta(days=55, hours=3),
                    capacity=250,
                    is_active=True,
                    image_url="https://images.unsplash.com/photo-1527979809431-ea3d5c0c01c9?q=80&w=1209&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
                    location="อาคารวิจัยวิศวกรรมประยุกต์สิรินธร",
                    created_by=3,
                    updated_by=3,
                    created_at=now,
                    updated_at=now,
                ),
                Event(
                    title="กิจกรรม English Camp",
                    description="English Camp สำหรับนักศึกษาที่ต้องการฝึกภาษาอังกฤษกับเจ้าของภาษา 2 วัน 1 คืน",
                    start_date=now + timedelta(days=60),
                    end_date=now + timedelta(days=61),
                    capacity=60,
                    is_active=True,
                    image_url="https://plus.unsplash.com/premium_photo-1666739032615-ecbd14dfb543?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
                    location="อาคารเรียนและปฏิบัติการพื้นฐานทางวิทยาศาสตร์",
                    created_by=2,
                    updated_by=2,
                    created_at=now,
                    updated_at=now,
                ),
                Event(
                    title="กิจกรรม Science Fair",
                    description="Science Fair งานแสดงผลงานวิจัยและนวัตกรรมของนักศึกษาและอาจารย์",
                    start_date=now + timedelta(days=70),
                    end_date=now + timedelta(days=71),
                    capacity=350,
                    is_active=True,
                    image_url="https://images.unsplash.com/photo-1493528237448-144452699e16?q=80&w=1303&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
                    location="อาคารวิจัยวิศวกรรมประยุกต์สิรินธร",
                    created_by=1,
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

            from app.models.announcement_model import AnnouncementCategory

            announcements = [
                Announcement(
                    title="ยินดีต้อนรับสู่ CampHub",
                    content="เรายินดีต้อนรับคุณเข้าสู่แพลตฟอร์มของเรา!",
                    description="ข้อความต้อนรับอย่างเป็นทางการสำหรับผู้ใช้งานใหม่ทุกคนที่เข้าร่วมแพลตฟอร์ม CampHub",
                    category=AnnouncementCategory.GENERAL,
                    image_url="https://images.unsplash.com/photo-1560265036-021b3652b490?q=80&w=1332&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
                    start_date=now,
                    end_date=now + timedelta(days=30),
                    created_by=1,
                ),
                Announcement(
                    title="เปิดรับสมัครลงทะเบียนเรียน",
                    content="ลงทะเบียนเรียนของคุณเดี๋ยวนี้! อย่าพลาดกำหนดเวลา",
                    description="การลงทะเบียนเรียนสำหรับภาคการศึกษาที่กำลังจะมาถึงเปิดให้บริการแล้ว นักศึกษาสามารถลงทะเบียนผ่านระบบพอร์ทัลนักศึกษา",
                    category=AnnouncementCategory.ACADEMIC,
                    image_url="https://images.unsplash.com/photo-1613160058266-ed84e3251760?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
                    start_date=now,
                    end_date=now + timedelta(days=14),
                    created_by=1,
                ),
                Announcement(
                    title="ขยายเวลาเปิดห้องสมุดในช่วงสอบ",
                    content="ห้องสมุดจะเปิดบริการ 24 ชั่วโมงในช่วงสอบเริ่มสัปดาห์หน้า",
                    description="เพื่อสนับสนุนนักศึกษาในช่วงสอบ ห้องสมุดมหาวิทยาลัยจะขยายเวลาเปิดบริการเป็น 24 ชั่วโมงเป็นเวลา 2 สัปดาห์",
                    category=AnnouncementCategory.ACTIVITY,
                    image_url="https://images.unsplash.com/photo-1508169351866-777fc0047ac5?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
                    start_date=now + timedelta(days=7),
                    end_date=now + timedelta(days=21),
                    created_by=3,
                ),
                Announcement(
                    title="ประกาศปิดปรับปรุงระบบ",
                    content="ระบบจะปิดปรับปรุงในวันที่ 10 ตุลาคม เวลา 22:00-02:00",
                    description="เพื่อพัฒนาระบบให้ดียิ่งขึ้น จะมีการปิดปรับปรุงชั่วคราวในช่วงเวลาดังกล่าว ขออภัยในความไม่สะดวก",
                    category=AnnouncementCategory.GENERAL,
                    image_url="https://plus.unsplash.com/premium_photo-1721830791498-ec809d9d94ec?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
                    start_date=now + timedelta(days=5),
                    end_date=now + timedelta(days=6),
                    created_by=1,
                ),
                Announcement(
                    title="Academic Conference 2025",
                    content="ขอเชิญชวนเข้าร่วมงานประชุมวิชาการประจำปี 2025",
                    description="งานประชุมวิชาการระดับนานาชาติสำหรับนักศึกษาและอาจารย์ พบกับวิทยากรรับเชิญจากต่างประเทศ",
                    category=AnnouncementCategory.ACADEMIC,
                    image_url="https://images.unsplash.com/photo-1587825140708-dfaf72ae4b04?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
                    start_date=now + timedelta(days=20),
                    end_date=now + timedelta(days=22),
                    created_by=2,
                ),
                Announcement(
                    title="กิจกรรม Big Cleaning Day",
                    content="ขอเชิญนักศึกษาทุกคนร่วมกิจกรรม Big Cleaning Day",
                    description="ร่วมกันทำความสะอาดพื้นที่มหาวิทยาลัยเพื่อสิ่งแวดล้อมที่ดีขึ้น พบกันวันศุกร์นี้ที่ลานกิจกรรม",
                    category=AnnouncementCategory.ACTIVITY,
                    image_url="https://plus.unsplash.com/premium_photo-1683141120496-f5921a97f5c4?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
                    start_date=now + timedelta(days=3),
                    end_date=now + timedelta(days=4),
                    created_by=3,
                ),
            ]
            announcements += [
                Announcement(
                    title="แจ้งเตือนการชำระค่าธรรมเนียมการศึกษา",
                    content="โปรดชำระค่าธรรมเนียมการศึกษาภายในวันที่กำหนด เพื่อหลีกเลี่ยงค่าปรับ",
                    description="นักศึกษาทุกคนต้องชำระค่าธรรมเนียมการศึกษาภายในวันที่ 15 ตุลาคม 2025",
                    category=AnnouncementCategory.GENERAL,
                    image_url="https://images.unsplash.com/photo-1625980344922-a4df108b2bd0?q=80&w=1175&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
                    start_date=now + timedelta(days=8),
                    end_date=now + timedelta(days=15),
                    created_by=1,
                ),
                Announcement(
                    title="ประกาศผลสอบกลางภาค",
                    content="สามารถตรวจสอบผลสอบกลางภาคได้ที่ระบบ Student Portal",
                    description="ผลสอบกลางภาคของทุกวิชาถูกอัปโหลดเรียบร้อยแล้วที่ Student Portal",
                    category=AnnouncementCategory.ACADEMIC,
                    image_url="https://images.unsplash.com/photo-1606326608690-4e0281b1e588?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
                    start_date=now + timedelta(days=12),
                    end_date=now + timedelta(days=20),
                    created_by=2,
                ),
                Announcement(
                    title="กิจกรรมรับน้องใหม่ Freshy Day",
                    content="ขอเชิญชวนน้องใหม่เข้าร่วมกิจกรรมรับน้อง Freshy Day พบกับกิจกรรมสนุก ๆ และของรางวัลมากมาย",
                    description="กิจกรรมรับน้องใหม่ประจำปี 2025 จัดขึ้นที่สนามกีฬาใหญ่",
                    category=AnnouncementCategory.ACTIVITY,
                    image_url="https://images.unsplash.com/photo-1540539234-c14a20fb7c7b?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
                    start_date=now + timedelta(days=18),
                    end_date=now + timedelta(days=19),
                    created_by=3,
                ),
                Announcement(
                    title="แจ้งเตือนการลงทะเบียนเรียนซ้ำซ้อน",
                    content="ตรวจสอบตารางเรียนของคุณเพื่อหลีกเลี่ยงการลงทะเบียนเรียนซ้ำซ้อน",
                    description="ระบบตรวจพบการลงทะเบียนเรียนซ้ำซ้อนในบางรายวิชา กรุณาตรวจสอบและแก้ไขก่อนวันปิดรับลงทะเบียน",
                    category=AnnouncementCategory.ACADEMIC,
                    image_url="https://plus.unsplash.com/premium_photo-1682310105362-76fa03431d65?q=80&w=1212&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
                    start_date=now + timedelta(days=9),
                    end_date=now + timedelta(days=12),
                    created_by=2,
                ),
                Announcement(
                    title="กิจกรรม Volunteer Day",
                    content="Volunteer Day ชวนเพื่อน ๆ มาร่วมทำกิจกรรมจิตอาสาเพื่อสังคม",
                    description="กิจกรรมจิตอาสาเพื่อสังคม จัดขึ้นที่ลานกิจกรรมกลางแจ้ง",
                    category=AnnouncementCategory.ACTIVITY,
                    image_url="https://plus.unsplash.com/premium_photo-1683121334505-907a00cf904c?q=80&w=1332&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
                    start_date=now + timedelta(days=25),
                    end_date=now + timedelta(days=26),
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
            name="อาคารเรียนและปฏิบัติการพื้นฐานทางวิทยาศาสตร์",
            code="BSc",
            latitude=7.006472135413086,
            longitude=100.49951107880403,
            description="เปิดจันทร์-ศุกร์ 08:00-17:00\nโทร: +66-74-287-0041\nเว็บไซต์: http://www.sci.psu.ac.th/",
        )
        loc2 = Location(
            name="อาคารวิจัยวิศวกรรมประยุกต์สิรินธร",
            code="S",
            latitude=7.006327821282247,
            longitude=100.50252641168618,
            description="เปิดจันทร์-ศุกร์ 08:30-16:30\nโทร: +66-74-287-0576\nเว็บไซต์: http://www.coe.psu.ac.th/",
        )
        loc3 = Location(
            name="คณะทันตแพทยศาสตร์",
            code="Dent",
            latitude=7.00822939668783,
            longitude=100.49646275464498,
            description="เปิดจันทร์-ศุกร์ 08:00-16:00\nโทร: +66-74-287-1293\nเว็บไซต์: http://www.dent.psu.ac.th/",
        )
        loc4 = Location(
            name="คณะแพทยศาสตร์",
            code="Med",
            latitude=7.007227694458388,
            longitude=100.49539693621114,
            description="เปิดจันทร์-ศุกร์ 08:00-17:00\nโทร: +66-74-287-4656\nเว็บไซต์: http://www.med.psu.ac.th/",
        )
        loc5 = Location(
            name="ศูนย์กีฬาและสุขภาพ",
            code="Sport",
            latitude=7.009715442579287,
            longitude=100.50043455287542,
            description="เปิดทุกวัน 06:00-22:00\nโทร: +66-74-287-7689\nเว็บไซต์: http://www.sport.psu.ac.th/",
        )
        loc6 = Location(
            name="คณะนิติศาสตร์",
            code="Law",
            latitude=7.011680636991237,
            longitude=100.49648841177901,
            description="เปิดจันทร์-ศุกร์ 08:30-16:30\nโทร: +66-74-287-2134\nเว็บไซต์: http://www.law.psu.ac.th/",
        )
        loc7 = Location(
            name="คณะวิทยาการจัดการ",
            code="FMS",
            latitude=7.0116184941311355,
            longitude=100.49826934997274,
            description="เปิดจันทร์-ศุกร์ 08:00-17:00\nโทร: +66-74-287-5067\nเว็บไซต์: http://www.fms.psu.ac.th/",
        )

        session.add_all([loc1, loc2, loc3, loc4, loc5, loc6, loc7])
        await session.flush()  # เพื่อให้ได้ id ของ location

        rooms = []
        rooms += [
            Room(
                name="BSc101",
                location_id=loc1.id,
                description="ห้อง BSc101 อาคารเรียนและปฏิบัติการพื้นฐานทางวิทยาศาสตร์",
            ),
            Room(
                name="BSc201",
                location_id=loc1.id,
                description="ห้อง BSc201 อาคารเรียนและปฏิบัติการพื้นฐานทางวิทยาศาสตร์",
            ),
            Room(
                name="BSc301",
                location_id=loc1.id,
                description="ห้อง BSc301 อาคารเรียนและปฏิบัติการพื้นฐานทางวิทยาศาสตร์",
            ),
            Room(
                name="BSc401",
                location_id=loc1.id,
                description="ห้อง BSc401 อาคารเรียนและปฏิบัติการพื้นฐานทางวิทยาศาสตร์",
            ),
            Room(
                name="BSc501",
                location_id=loc1.id,
                description="ห้อง BSc501 อาคารเรียนและปฏิบัติการพื้นฐานทางวิทยาศาสตร์",
            ),
        ]
        # loc2: S
        rooms += [
            Room(
                name="S201",
                location_id=loc2.id,
                description="ห้อง S201 อาคารวิจัยวิศวกรรมประยุกต์สิรินธร",
            ),
            Room(
                name="S301",
                location_id=loc2.id,
                description="ห้อง S301 อาคารวิจัยวิศวกรรมประยุกต์สิรินธร",
            ),
            Room(
                name="S401",
                location_id=loc2.id,
                description="ห้อง S401 อาคารวิจัยวิศวกรรมประยุกต์สิรินธร",
            ),
            Room(
                name="S501",
                location_id=loc2.id,
                description="ห้อง S501 อาคารวิจัยวิศวกรรมประยุกต์สิรินธร",
            ),
        ]
        # loc3: Dent
        rooms += [
            Room(
                name="Dent101",
                location_id=loc3.id,
                description="ห้อง Dent101 คณะทันตแพทยศาสตร์",
            ),
            Room(
                name="Dent201",
                location_id=loc3.id,
                description="ห้อง Dent201 คณะทันตแพทยศาสตร์",
            ),
            Room(
                name="Dent301",
                location_id=loc3.id,
                description="ห้อง Dent301 คณะทันตแพทยศาสตร์",
            ),
        ]
        # loc4: Med
        rooms += [
            Room(
                name="Med305",
                location_id=loc4.id,
                description="ห้อง Med305 คณะแพทยศาสตร์",
            ),
            Room(
                name="Med405",
                location_id=loc4.id,
                description="ห้อง Med405 คณะแพทยศาสตร์",
            ),
            Room(
                name="Med505",
                location_id=loc4.id,
                description="ห้อง Med505 คณะแพทยศาสตร์",
            ),
        ]
        # loc5: Sport
        rooms += [
            Room(
                name="Sport101",
                location_id=loc5.id,
                description="ห้อง Sport101 ศูนย์กีฬาและสุขภาพ",
            ),
            Room(
                name="Sport201",
                location_id=loc5.id,
                description="ห้อง Sport201 ศูนย์กีฬาและสุขภาพ",
            ),
            Room(
                name="Sport301",
                location_id=loc5.id,
                description="ห้อง Sport301 ศูนย์กีฬาและสุขภาพ",
            ),
        ]
        # loc6: Law
        rooms += [
            Room(
                name="Law101", location_id=loc6.id, description="ห้อง Law101 คณะนิติศาสตร์"
            ),
            Room(
                name="Law201", location_id=loc6.id, description="ห้อง Law201 คณะนิติศาสตร์"
            ),
            Room(
                name="Law301", location_id=loc6.id, description="ห้อง Law301 คณะนิติศาสตร์"
            ),
        ]
        # loc7: FMS
        rooms += [
            Room(
                name="FMS101",
                location_id=loc7.id,
                description="ห้อง FMS101 คณะวิทยาการจัดการ",
            ),
            Room(
                name="FMS201",
                location_id=loc7.id,
                description="ห้อง FMS201 คณะวิทยาการจัดการ",
            ),
            Room(
                name="FMS301",
                location_id=loc7.id,
                description="ห้อง FMS301 คณะวิทยาการจัดการ",
            ),
        ]

        session.add_all(rooms)
        await session.commit()
        print("Locations and rooms created")


# ---------------------------
# Courses + CourseSchedule
# ---------------------------
async def init_demo_courses():
    async with AsyncSession(async_engine) as session:
        result = await session.execute(select(Course))
        if result.scalars().first():
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
                room_id=room_dict["BSc101"],
            ),
            CourseSchedule(
                course_id=course1.id,
                day_of_week="Monday",
                start_time=time(13, 0),
                end_time=time(15, 0),
                room_id=room_dict["BSc101"],
            ),
            CourseSchedule(
                course_id=course1.id,
                day_of_week="Friday",
                start_time=time(9, 0),
                end_time=time(11, 0),
                room_id=room_dict["BSc101"],
            ),
            CourseSchedule(
                course_id=course2.id,
                day_of_week="Wednesday",
                start_time=time(13, 0),
                end_time=time(15, 0),
                room_id=room_dict["S201"],
            ),
            CourseSchedule(
                course_id=course3.id,
                day_of_week="Friday",
                start_time=time(10, 0),
                end_time=time(12, 0),
                room_id=room_dict["S301"],
            ),
        ]

        session.add_all(schedules)
        # Add mockup courses and schedules
        mock_course1 = Course(
            course_code="LAW101",
            course_name="Introduction to Law",
            credits=3,
            available_seats=60,
            description="พื้นฐานกฎหมายเบื้องต้นสำหรับนักศึกษาทุกสาขา",
            created_at=datetime.now(),
        )
        mock_course2 = Course(
            course_code="FMS201",
            course_name="Management Principles",
            credits=3,
            available_seats=45,
            description="หลักการจัดการและบริหารธุรกิจ",
            created_at=datetime.now(),
        )
        mock_course3 = Course(
            course_code="MED405",
            course_name="Clinical Medicine",
            credits=4,
            available_seats=30,
            description="การแพทย์คลินิกสำหรับนักศึกษาแพทย์",
            created_at=datetime.now(),
        )
        mock_course4 = Course(
            course_code="Dent301",
            course_name="Dental Anatomy",
            credits=2,
            available_seats=25,
            description="กายวิภาคศาสตร์ทางทันตกรรม",
            created_at=datetime.now(),
        )
        mock_course5 = Course(
            course_code="Sport101",
            course_name="Sports Science",
            credits=2,
            available_seats=40,
            description="วิทยาศาสตร์การกีฬาและสุขภาพ",
            created_at=datetime.now(),
        )
        session.add_all(
            [mock_course1, mock_course2, mock_course3, mock_course4, mock_course5]
        )
        await session.flush()
        # Schedules for mock courses
        mock_schedules = [
            # LAW101: only one day
            CourseSchedule(
                course_id=mock_course1.id,
                day_of_week="Tuesday",
                start_time=time(10, 0),
                end_time=time(12, 0),
                room_id=room_dict["Law101"],
            ),
            # FMS201: two days
            CourseSchedule(
                course_id=mock_course2.id,
                day_of_week="Monday",
                start_time=time(14, 0),
                end_time=time(16, 0),
                room_id=room_dict["FMS101"],
            ),
            CourseSchedule(
                course_id=mock_course2.id,
                day_of_week="Thursday",
                start_time=time(9, 0),
                end_time=time(11, 0),
                room_id=room_dict["FMS201"],
            ),
            # MED405: three days
            CourseSchedule(
                course_id=mock_course3.id,
                day_of_week="Monday",
                start_time=time(8, 0),
                end_time=time(10, 0),
                room_id=room_dict["Med405"],
            ),
            CourseSchedule(
                course_id=mock_course3.id,
                day_of_week="Wednesday",
                start_time=time(13, 0),
                end_time=time(15, 0),
                room_id=room_dict["Med505"],
            ),
            CourseSchedule(
                course_id=mock_course3.id,
                day_of_week="Friday",
                start_time=time(10, 0),
                end_time=time(12, 0),
                room_id=room_dict["Med305"],
            ),
            # Dent301: one day
            CourseSchedule(
                course_id=mock_course4.id,
                day_of_week="Thursday",
                start_time=time(13, 0),
                end_time=time(15, 0),
                room_id=room_dict["Dent301"],
            ),
            # Sport101: two days
            CourseSchedule(
                course_id=mock_course5.id,
                day_of_week="Tuesday",
                start_time=time(9, 0),
                end_time=time(11, 0),
                room_id=room_dict["Sport101"],
            ),
            CourseSchedule(
                course_id=mock_course5.id,
                day_of_week="Friday",
                start_time=time(14, 0),
                end_time=time(16, 0),
                room_id=room_dict["Sport301"],
            ),
        ]
        session.add_all(mock_schedules)
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
