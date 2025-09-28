import pytest
from datetime import datetime, timedelta


@pytest.mark.asyncio
async def test_create_event_success(client, authenticated_user):
    headers = authenticated_user["headers"]
    now = datetime.now()
    data = {
        "title": "Test Event",
        "description": "กิจกรรมทดสอบ",
        "start_date": now.isoformat(),
        "end_date": (now + timedelta(days=1)).isoformat(),
        "capacity": 100,
        "is_active": True,
    }
    resp = await client.post("/api/events/", data=data, headers=headers)
    assert resp.status_code == 201
    result = resp.json()
    assert result["title"] == "Test Event"
    assert result["enrolled_count"] == 0


@pytest.mark.asyncio
async def test_create_event_invalid_date(client, authenticated_user):
    headers = authenticated_user["headers"]
    now = datetime.now()
    data = {
        "title": "Invalid Date Event",
        "start_date": now.isoformat(),
        "end_date": (now - timedelta(days=1)).isoformat(),
    }
    resp = await client.post("/api/events/", data=data, headers=headers)
    assert resp.status_code == 400
    assert resp.json()["detail"] == "วันที่เริ่มต้องอยู่ก่อนวันที่สิ้นสุด"


@pytest.mark.asyncio
async def test_get_events_list(client, authenticated_user):
    headers = authenticated_user["headers"]
    now = datetime.now()
    # สร้าง event 2 อัน
    for i in range(2):
        data = {
            "title": f"Event {i}",
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(days=1)).isoformat(),
        }
        await client.post("/api/events/", data=data, headers=headers)
    resp = await client.get("/api/events/")
    assert resp.status_code == 200
    events = resp.json()
    assert len(events) >= 2
    assert any("Event 0" in e["title"] for e in events)


@pytest.mark.asyncio
async def test_get_event_public_view(client, authenticated_user):
    headers = authenticated_user["headers"]
    now = datetime.now()
    data = {
        "title": "Public Event",
        "start_date": now.isoformat(),
        "end_date": (now + timedelta(days=1)).isoformat(),
    }
    resp = await client.post("/api/events/", data=data, headers=headers)
    event_id = resp.json()["id"]
    resp2 = await client.get(f"/api/events/public/{event_id}")
    assert resp2.status_code == 200
    assert resp2.json()["title"] == "Public Event"


@pytest.mark.asyncio
async def test_get_event_not_found(client):
    resp = await client.get("/api/events/public/999999")
    assert resp.status_code == 404
    assert "ไม่พบกิจกรรม" in resp.json()["detail"]
