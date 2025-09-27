from typing import List, Optional, Dict, Any
from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.core.base_service import BaseService
from app.core.exceptions import (
    NotFoundError,
    ValidationException,
    PermissionDeniedError,
)
from app.core.cache import cache_result
from app.models.event_model import Event
from app.models.event_enrollment_model import EventEnrollment
from app.models.user_model import User
from app.schemas.event_schema import (
    EventCreate,
    EventUpdate,
    EventResponse,
    EventListResponse,
)
from app.services.image_service import event_image_service
from app.utils import make_naive_datetime, validate_datetime_range


class EventService(BaseService[Event, EventCreate, EventUpdate]):
    """
    Event management service with full CRUD operations,
    image handling, and enrollment management
    """

    def __init__(self, session: AsyncSession, current_user: Optional[User] = None):
        super().__init__(Event, session, current_user)

    # Core CRUD Operations
    async def get_by_id(self, event_id: int) -> EventResponse:
        """Get event by ID with enrollment count"""
        event = await self.session.get(Event, event_id)
        if not event:
            raise NotFoundError("Event not found")

        # Get enrollment count
        enrolled_count = await self._get_enrollment_count(event_id)

        return EventResponse.model_validate(
            event.__dict__ | {"enrolled_count": enrolled_count}
        )

    async def get_public_event(self, event_id: int) -> EventResponse:
        """Get active event details for public access (no auth required)"""
        event = await self.session.get(Event, event_id)
        if not event or not event.is_active:
            raise NotFoundError("Event not found or not active")

        enrolled_count = await self._get_enrollment_count(event_id)

        return EventResponse.model_validate(
            event.__dict__ | {"enrolled_count": enrolled_count}
        )

    @cache_result(ttl=300)  # Cache for 5 minutes
    async def get_events_list(
        self,
        created_by: Optional[int] = None,
        is_active: Optional[bool] = None,
        q: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        include_enrolled_count: bool = True,
    ) -> List[EventListResponse]:
        """Get events list with filters and optional enrollment counts"""

        # Build query filters
        filters = []
        if created_by is not None:
            filters.append(Event.created_by == created_by)
        if is_active is not None:
            filters.append(Event.is_active == is_active)
        if q:
            filters.append(func.lower(Event.title).like(f"%{q.lower()}%"))
        if date_from:
            filters.append(Event.start_date >= date_from)
        if date_to:
            filters.append(Event.end_date <= date_to)

        stmt = select(Event)
        if filters:
            stmt = stmt.where(and_(*filters))

        stmt = stmt.order_by(Event.created_at.desc())
        result = await self.session.execute(stmt)
        events = result.scalars().all()

        # Convert to response format
        response_items = []
        if include_enrolled_count and events:
            # Batch get enrollment counts for performance
            event_ids = [e.id for e in events]
            counts_map = await self._get_enrollment_counts_batch(event_ids)

            for event in events:
                response_items.append(
                    EventListResponse.model_validate(
                        event.__dict__ | {"enrolled_count": counts_map.get(event.id, 0)}
                    )
                )
        else:
            for event in events:
                response_items.append(
                    EventListResponse.model_validate(
                        event.__dict__ | {"enrolled_count": 0}
                    )
                )

        return response_items

    async def create_with_image(
        self, data: EventCreate, image: Optional[UploadFile] = None
    ) -> EventResponse:
        """Create event with optional image upload"""
        if not self.current_user:
            raise PermissionDeniedError("Authentication required")

        # Validate datetime range
        validate_datetime_range(data.start_date, data.end_date)

        # Handle image upload
        image_url = None
        if image:
            image_url, _ = await event_image_service.save_image(image, "event")

        # Create event
        event_data = data.model_dump()
        event_data.update(
            {
                "image_url": image_url,
                "created_by": self.current_user.id,
                "updated_by": self.current_user.id,
            }
        )

        try:
            event = Event(**event_data)
            self.session.add(event)
            await self.session.commit()
            await self.session.refresh(event)

            return EventResponse.model_validate(event.__dict__ | {"enrolled_count": 0})

        except Exception as e:
            await self.session.rollback()
            if image_url:
                event_image_service.delete_image(image_url)
            raise ValidationException(f"Failed to create event: {str(e)}")

    async def update_with_image(
        self,
        event_id: int,
        data: EventUpdate,
        image: Optional[UploadFile] = None,
        remove_image: bool = False,
    ) -> EventResponse:
        """Update event with optional image management"""
        event = await self.session.get(Event, event_id)
        if not event:
            raise NotFoundError("Event not found")

        # Check permissions
        if not self.current_user or event.created_by != self.current_user.id:
            raise PermissionDeniedError(
                "You don't have permission to update this event"
            )

        update_data = data.model_dump(exclude_unset=True)

        # Convert datetime fields
        if "start_date" in update_data:
            update_data["start_date"] = make_naive_datetime(update_data["start_date"])
        if "end_date" in update_data:
            update_data["end_date"] = make_naive_datetime(update_data["end_date"])

        # Validate datetime range if dates are being updated
        if ("start_date" in update_data) or ("end_date" in update_data):
            start_date = update_data.get("start_date", event.start_date)
            end_date = update_data.get("end_date", event.end_date)
            validate_datetime_range(start_date, end_date)

        # Handle image operations
        if image:
            new_url, _ = await event_image_service.replace_image(
                image, event.image_url, "event"
            )
            event.image_url = new_url
        elif remove_image and event.image_url:
            event_image_service.delete_image(event.image_url)
            event.image_url = None

        # Apply updates
        for field, value in update_data.items():
            setattr(event, field, value)

        event.updated_by = self.current_user.id
        event.updated_at = datetime.now()

        await self.session.commit()
        await self.session.refresh(event)

        # Get enrollment count
        enrolled_count = await self._get_enrollment_count(event_id)

        return EventResponse.model_validate(
            event.__dict__ | {"enrolled_count": enrolled_count}
        )

    async def delete_with_cleanup(self, event_id: int) -> Dict[str, Any]:
        """Delete event with proper cleanup of image and enrollments"""
        event = await self.session.get(Event, event_id)
        if not event:
            raise NotFoundError("Event not found")

        # Check permissions
        if not self.current_user or event.created_by != self.current_user.id:
            raise PermissionDeniedError(
                "You don't have permission to delete this event"
            )

        # Delete associated image
        if event.image_url:
            event_image_service.delete_image(event.image_url)

        # Delete event (enrollments will be cascade deleted)
        await self.session.delete(event)
        await self.session.commit()

        return {"message": "Event deleted successfully"}

    # Helper methods for enrollment management
    async def _get_enrollment_count(self, event_id: int) -> int:
        """Get enrollment count for a single event"""
        result = await self.session.execute(
            select(func.count(EventEnrollment.id)).where(
                EventEnrollment.event_id == event_id
            )
        )
        return result.scalar_one()

    async def _get_enrollment_counts_batch(
        self, event_ids: List[int]
    ) -> Dict[int, int]:
        """Get enrollment counts for multiple events efficiently"""
        if not event_ids:
            return {}

        result = await self.session.execute(
            select(
                EventEnrollment.event_id, func.count(EventEnrollment.id).label("count")
            )
            .where(EventEnrollment.event_id.in_(event_ids))
            .group_by(EventEnrollment.event_id)
        )

        return {row.event_id: row.count for row in result}

    # Capacity and availability checks
    async def check_event_capacity(self, event_id: int) -> Dict[str, Any]:
        """Check event capacity and availability"""
        event = await self.session.get(Event, event_id)
        if not event:
            raise NotFoundError("Event not found")

        enrolled_count = await self._get_enrollment_count(event_id)

        return {
            "event_id": event_id,
            "title": event.title,
            "capacity": event.capacity,
            "enrolled_count": enrolled_count,
            "available_spots": (
                max(0, event.capacity - enrolled_count) if event.capacity else None
            ),
            "is_full": event.capacity and enrolled_count >= event.capacity,
            "is_active": event.is_active,
        }

    @cache_result(ttl=600)  # Cache for 10 minutes
    async def get_active_events(self) -> List[EventListResponse]:
        """Get all active events (cached)"""
        return await self.get_events_list(is_active=True)
