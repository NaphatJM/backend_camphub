from typing import Optional
from fastapi import HTTPException, UploadFile
from pathlib import Path
from uuid import uuid4
import os
import aiofiles


class ImageUploadService:
    """Service for handling image uploads"""

    def __init__(self, upload_dir: str):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.allowed_types = [
            "image/jpeg",
            "image/jpg",
            "image/png",
            "image/gif",
            "image/webp",
        ]

    def validate_image(self, file: UploadFile) -> None:
        """Validate image file type and size"""
        if not file.content_type or file.content_type not in self.allowed_types:
            raise HTTPException(
                status_code=400,
                detail="ไฟล์ต้องเป็นรูปภาพประเภท JPEG, PNG, GIF หรือ WebP เท่านั้น",
            )

        if file.size and file.size > self.max_file_size:
            raise HTTPException(status_code=400, detail="ไฟล์ต้องมีขนาดไม่เกิน 10MB")

    async def save_image(self, file: UploadFile, prefix: str = "") -> tuple[str, Path]:
        """
        Save uploaded image file

        Args:
            file: UploadFile object
            prefix: Optional prefix for filename

        Returns:
            tuple: (image_url, file_path)
        """
        self.validate_image(file)

        try:
            # Generate unique filename
            file_extension = Path(file.filename).suffix if file.filename else ".jpg"
            prefix_str = f"{prefix}_" if prefix else ""
            filename = f"{prefix_str}{uuid4().hex}{file_extension}"
            file_path = self.upload_dir / filename

            # Save file
            async with aiofiles.open(file_path, "wb") as f:
                content = await file.read()
                await f.write(content)

            # Generate URL path
            relative_path = str(self.upload_dir.relative_to(Path("static")))
            image_url = f"/static/{relative_path}/{filename}"

            return image_url, file_path

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"เกิดข้อผิดพลาดในการอัปโหลดไฟล์: {str(e)}"
            )

    def delete_image(self, image_url: str) -> bool:
        """
        Delete image file from storage

        Args:
            image_url: URL of the image to delete

        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            if not image_url:
                return False

            # Extract filename from URL
            filename = image_url.split("/")[-1]
            file_path = self.upload_dir / filename

            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False

        except Exception:
            return False

    async def replace_image(
        self, file: UploadFile, old_image_url: Optional[str] = None, prefix: str = ""
    ) -> tuple[str, Path]:
        """
        Replace existing image with new one

        Args:
            file: New UploadFile object
            old_image_url: URL of old image to delete
            prefix: Optional prefix for filename

        Returns:
            tuple: (new_image_url, new_file_path)
        """
        # Delete old image if exists
        if old_image_url:
            self.delete_image(old_image_url)

        # Save new image
        return await self.save_image(file, prefix)


# Pre-configured service instances
profile_image_service = ImageUploadService("static/profile_images")
event_image_service = ImageUploadService("static/event_images")
announcement_image_service = ImageUploadService("static/announcement_images")
