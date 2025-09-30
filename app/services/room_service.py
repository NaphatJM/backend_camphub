from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models import User, Room, Location
from app.schemas.room import RoomCreate, RoomRead, RoomUpdate

NOT_FOUND_ROOM_MSG = "Room not found"


class RoomService:
    def __init__(self, session: AsyncSession, current_user: Optional[User] = None):
        self.session = session
        self.current_user = current_user

    # --------------------------
    # GET all rooms (with location)
    # --------------------------
    async def get_all(self) -> List[RoomRead]:
        result = await self.session.exec(
            select(Room).options(selectinload(Room.location))
        )
        rooms = result.scalars().all()
        return [RoomRead.model_validate(r) for r in rooms]

    # --------------------------
    # GET by ID
    # --------------------------
    async def get_by_id(self, room_id: int) -> RoomRead:
        room = await self.session.get(
            Room, room_id, options=selectinload(Room.location)
        )
        if not room:
            raise HTTPException(status_code=404, detail=NOT_FOUND_ROOM_MSG)
        return RoomRead.model_validate(room)

    # --------------------------
    # CREATE
    # --------------------------
    async def create(self, data: RoomCreate) -> RoomRead:
        self._check_permission()
        # ตรวจว่า location_id มีอยู่จริง
        location = await self.session.get(Location, data.location_id)
        if not location:
            raise HTTPException(status_code=404, detail="Location not found")

        new_room = Room(**data.model_dump())
        self.session.add(new_room)
        await self.session.commit()
        await self.session.refresh(new_room)
        return RoomRead.model_validate(new_room)

    # --------------------------
    # UPDATE
    # --------------------------
    async def update(self, room_id: int, data: RoomUpdate) -> RoomRead:
        self._check_permission()
        room = await self.session.get(Room, room_id)
        if not room:
            raise HTTPException(status_code=404, detail=NOT_FOUND_ROOM_MSG)

        update_data = data.model_dump(exclude_unset=True)
        if "location_id" in update_data:
            location = await self.session.get(Location, update_data["location_id"])
            if not location:
                raise HTTPException(status_code=404, detail="Location not found")

        for field, value in update_data.items():
            setattr(room, field, value)

        self.session.add(room)
        await self.session.commit()
        await self.session.refresh(room)
        return RoomRead.model_validate(room)

    # --------------------------
    # DELETE
    # --------------------------
    async def delete(self, room_id: int) -> dict:
        self._check_permission()
        room = await self.session.get(Room, room_id)
        if not room:
            raise HTTPException(status_code=404, detail=NOT_FOUND_ROOM_MSG)

        await self.session.delete(room)
        await self.session.commit()
        return {"ok": True}

    # --------------------------
    # PRIVATE: ตรวจสอบสิทธิ์
    # --------------------------
    def _check_permission(self):
        if not self.current_user or self.current_user.role_id not in [1, 3]:
            raise HTTPException(
                status_code=403, detail="You are not allowed to manage rooms"
            )
