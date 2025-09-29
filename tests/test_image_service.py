import pytest
from app.services.image_service import ImageUploadService
from fastapi import HTTPException
import io
from unittest.mock import MagicMock, AsyncMock
from pathlib import Path


@pytest.mark.asyncio
async def test_save_image_invalid_type(tmp_path):
    service = ImageUploadService("static/test_images")
    fake_file = MagicMock()
    fake_file.filename = "test.txt"
    fake_file.read = AsyncMock(return_value=b"not an image")
    fake_file.content_type = "text/plain"
    fake_file.size = None
    with pytest.raises(HTTPException) as exc:
        await service.save_image(fake_file)
    assert exc.value.status_code == 400
