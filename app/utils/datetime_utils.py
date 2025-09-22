from datetime import datetime
from typing import Optional


def make_naive_datetime(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Convert timezone-aware datetime to naive datetime

    Args:
        dt: datetime object (can be timezone-aware or naive)

    Returns:
        naive datetime object or None
    """
    if dt is None:
        return None

    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)

    return dt


def validate_datetime_range(start_date: datetime, end_date: datetime) -> None:
    if start_date >= end_date:
        raise ValueError("วันที่เริ่มต้องอยู่ก่อนวันที่สิ้นสุด")
