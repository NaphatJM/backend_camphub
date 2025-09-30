from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload
from app.models import Course, CourseTeacherLink, User
from app.schemas.course_schema import CourseCreate, CourseRead, CourseUpdate

NOT_FOUND_COURSE_MSG = "Course not found"


class CourseService:
    """
    Service class สำหรับจัดการ CRUD ของ Course
    ใช้ encapsulate logic ทั้งหมดเกี่ยวกับ course
    และเชื่อมโยงกับ current_user
    """

    def __init__(self, session: AsyncSession, current_user: User | None = None):
        """
        กำหนด session สำหรับ db และ user ปัจจุบัน
        current_user เป็น optional
        สำหรับ method ที่ไม่ต้อง authentication จะไม่ต้องส่ง user
        """
        self.session = session
        self.current_user = current_user

    async def get_all(self) -> list[CourseRead]:
        """
        ดึงข้อมูล course ทั้งหมด พร้อม preload enrollments
        คืนค่าเป็น list ของ CourseRead schema
        """
        result = await self.session.exec(
            select(Course).options(selectinload(Course.enrollments))
        )
        courses = result.scalars().all()
        return [
            CourseRead(
                id=c.id,
                course_code=c.course_code,
                course_name=c.course_name,
                credits=c.credits,
                available_seats=c.available_seats,
                description=c.description,
                created_at=c.created_at,
                enrolled_count=len(c.enrollments),
            )
            for c in courses
        ]

    async def get_by_id(self, course_id: int) -> CourseRead:
        """
        ดึง course ตาม ID พร้อม preload enrollments
        ถ้าไม่พบ course จะ raise HTTPException 404
        """
        result = await self.session.exec(
            select(Course)
            .options(selectinload(Course.enrollments))
            .where(Course.id == course_id)
        )
        course = result.scalars().first()
        if not course:
            raise HTTPException(status_code=404, detail=NOT_FOUND_COURSE_MSG)
        return CourseRead(
            id=course.id,
            course_code=course.course_code,
            course_name=course.course_name,
            credits=course.credits,
            available_seats=course.available_seats,
            description=course.description,
            created_at=course.created_at,
            enrolled_count=len(course.enrollments),
        )

    async def create(self, data: CourseCreate) -> CourseRead:
        """
        สร้าง course ใหม่
        ตรวจสอบ role ของ user (Professor=1, Admin=3) ก่อนสร้าง
        คืนค่า CourseRead ของ course ที่สร้างใหม่
        """
        # เฉพาะ Professor (role_id=1) และ Admin (role_id=3) เท่านั้นที่สร้าง course ได้
        if self.current_user.role_id not in [1, 3]:
            raise HTTPException(
                status_code=403, detail="Only professors and admins can create courses"
            )

        # ตรวจสอบ duplicate course code
        existing_course = await self.session.exec(
            select(Course).where(Course.course_code == data.course_code)
        )
        if existing_course.scalars().first():
            raise HTTPException(
                status_code=400,
                detail=f"Course code '{data.course_code}' already exists",
            )
        db_course = Course(
            course_code=data.course_code,
            course_name=data.course_name,
            credits=data.credits,
            available_seats=data.available_seats,
            description=data.description,
        )
        self.session.add(db_course)
        await self.session.commit()
        await self.session.refresh(db_course)
        return CourseRead(
            id=db_course.id,
            course_code=db_course.course_code,
            course_name=db_course.course_name,
            credits=db_course.credits,
            available_seats=db_course.available_seats,
            description=db_course.description,
            created_at=db_course.created_at,
            enrolled_count=0,
        )

    async def update(self, course_id: int, data: CourseUpdate) -> CourseRead:
        """
        อัปเดต course ตาม ID
        ตรวจสอบ role ของ user (Professor=1 หรือ Admin=3)
        - อัปเดต field ที่ถูกส่งมา
        - อัปเดต teacher_links:
            - ถ้า teacher_ids ถูกส่งมา ใช้ teacher_ids ใหม่
            - ถ้าไม่ส่ง ใช้ prevalue (existing teacher) หรือ current_user ถ้าไม่มี
        คืนค่า CourseRead ของ course ที่อัปเดตแล้ว
        """
        if self.current_user.role_id not in [1, 3]:
            raise HTTPException(
                status_code=403, detail="Only professors and admins can update courses"
            )

        course = await self.session.get(Course, course_id)
        if not course:
            raise HTTPException(status_code=404, detail=NOT_FOUND_COURSE_MSG)

        update_data = data.model_dump(exclude_unset=True)
        teacher_ids = update_data.pop("teacher_ids", None)

        for field, value in update_data.items():
            setattr(course, field, value)
        self.session.add(course)

        # preload existing teacher links
        result = await self.session.exec(
            select(CourseTeacherLink.user_id).where(
                CourseTeacherLink.course_id == course_id
            )
        )
        existing_teacher_ids = [row[0] for row in result.fetchall()]

        if teacher_ids is not None:
            await self.session.exec(
                text("DELETE FROM course_teacher_link WHERE course_id = :course_id"),
                {"course_id": course_id},
            )
            for tid in teacher_ids:
                teacher = await self.session.get(User, tid)
                if not teacher:
                    raise HTTPException(
                        status_code=404, detail=f"Teacher {tid} not found"
                    )
                self.session.add(CourseTeacherLink(course_id=course_id, user_id=tid))
        else:
            # ใช้ prevalue
            if not existing_teacher_ids:
                self.session.add(
                    CourseTeacherLink(course_id=course_id, user_id=self.current_user.id)
                )
            else:
                for tid in existing_teacher_ids:
                    self.session.add(
                        CourseTeacherLink(course_id=course_id, user_id=tid)
                    )

        await self.session.commit()

        result = await self.session.exec(
            select(Course)
            .options(selectinload(Course.enrollments))
            .where(Course.id == course_id)
        )
        course = result.scalars().first()

        return CourseRead(
            id=course.id,
            course_code=course.course_code,
            course_name=course.course_name,
            credits=course.credits,
            available_seats=course.available_seats,
            description=course.description,
            created_at=course.created_at,
            enrolled_count=len(course.enrollments),
        )

    async def delete(self, course_id: int) -> dict:
        """
        ลบ course ตาม ID
        ตรวจสอบ role ของ user (1 หรือ 3)
        คืนค่า {"ok": True} ถ้าลบสำเร็จ
        """
        course = await self.session.get(Course, course_id)
        if not course:
            raise HTTPException(status_code=404, detail=NOT_FOUND_COURSE_MSG)
        if self.current_user.role_id not in [1, 3]:
            raise HTTPException(
                status_code=403, detail="Only professors and admins can delete courses"
            )
        await self.session.delete(course)
        await self.session.commit()
        return {"ok": True}
