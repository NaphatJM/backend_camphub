from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.models import User
from app.schemas.location import LocationCreate, LocationRead, LocationUpdate
from app.services.location_service import LocationService
from app.core.deps import get_current_user

router = APIRouter(prefix="/location", tags=["location"])


@router.get("/", response_model=List[LocationRead])
async def get_locations(session: AsyncSession = Depends(get_session)):
    service = LocationService(session)
    return await service.get_all()


@router.get("/{location_id}", response_model=LocationRead)
async def get_location_by_id(
    location_id: int, session: AsyncSession = Depends(get_session)
):
    service = LocationService(session)
    return await service.get_by_id(location_id)


@router.post("/", response_model=LocationRead)
async def create_location(
    data: LocationCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = LocationService(session, current_user)
    return await service.create(data)


@router.put("/{location_id}", response_model=LocationRead)
async def update_location(
    location_id: int,
    data: LocationUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = LocationService(session, current_user)
    return await service.update(location_id, data)


@router.delete("/{location_id}")
async def delete_location(
    location_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = LocationService(session, current_user)
    return await service.delete(location_id)
