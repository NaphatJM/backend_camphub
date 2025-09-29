from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.db import get_session
from app.models import Faculty
from app.schemas.faculty_schema import FacultyRead

router = APIRouter(prefix="/faculty", tags=["faculty"])


@router.get("", response_model=list[FacultyRead])
async def get_all_faculties(session: AsyncSession = Depends(get_session)):
    result = await session.exec(select(Faculty))
    faculties = result.scalars().all()
    return faculties
