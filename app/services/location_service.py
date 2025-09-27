from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User, Location
from app.schemas.location import LocationCreate, LocationRead, LocationUpdate


class LocationService:
    def __init__(self, session: AsyncSession, current_user: Optional[User] = None):
        self.session = session
        self.current_user = current_user

    # --------------------------
    # GET all locations
    # --------------------------
    async def get_all(self) -> List[LocationRead]:
        result = await self.session.execute(select(Location))
        locations = result.scalars().all()
        return [LocationRead.from_orm(loc) for loc in locations]

    # --------------------------
    # GET by ID
    # --------------------------
    async def get_by_id(self, location_id: int) -> LocationRead:
        location = await self.session.get(Location, location_id)
        if not location:
            raise HTTPException(status_code=404, detail="ไม่พบสถานที่นี้")
        return LocationRead.from_orm(location)

    # --------------------------
    # CREATE
    # --------------------------
    async def create(self, data: LocationCreate) -> LocationRead:
        self._check_permission()
        new_location = Location(**data.model_dump())
        self.session.add(new_location)
        await self.session.commit()
        await self.session.refresh(new_location)
        return LocationRead.from_orm(new_location)

    # --------------------------
    # UPDATE
    # --------------------------
    async def update(self, location_id: int, data: LocationUpdate) -> LocationRead:
        self._check_permission()
        location = await self.session.get(Location, location_id)
        if not location:
            raise HTTPException(status_code=404, detail="ไม่พบสถานที่นี้")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(location, field, value)

        self.session.add(location)
        await self.session.commit()
        await self.session.refresh(location)
        return LocationRead.from_orm(location)

    # --------------------------
    # DELETE
    # --------------------------
    async def delete(self, location_id: int) -> dict:
        self._check_permission()
        location = await self.session.get(Location, location_id)
        if not location:
            raise HTTPException(status_code=404, detail="ไม่พบสถานที่นี้")

        await self.session.delete(location)
        await self.session.commit()
        return {"ok": True}

    # --------------------------
    # PRIVATE: ตรวจสอบสิทธิ์
    # --------------------------
    def _check_permission(self):
        if not self.current_user or self.current_user.role_id not in [1, 3]:
            raise HTTPException(status_code=403, detail="คุณไม่มีสิทธิ์ในการจัดการสถานที่")
