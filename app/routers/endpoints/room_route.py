from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.models import User
from app.schemas.room import RoomCreate, RoomRead, RoomUpdate
from app.services.room_service import RoomService
from app.core.deps import get_current_user

router = APIRouter(prefix="/room", tags=["room"])


@router.get("/", response_model=List[RoomRead])
async def get_rooms(session: AsyncSession = Depends(get_session)):
    service = RoomService(session)
    return await service.get_all()


@router.get("/{room_id}", response_model=RoomRead)
async def get_room_by_id(room_id: int, session: AsyncSession = Depends(get_session)):
    service = RoomService(session)
    return await service.get_by_id(room_id)


@router.post("/", response_model=RoomRead)
async def create_room(
    data: RoomCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = RoomService(session, current_user)
    return await service.create(data)


@router.put("/{room_id}", response_model=RoomRead)
async def update_room(
    room_id: int,
    data: RoomUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = RoomService(session, current_user)
    return await service.update(room_id, data)


@router.delete("/{room_id}")
async def delete_room(
    room_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = RoomService(session, current_user)
    return await service.delete(room_id)
