import asyncio
from sqlmodel import SQLModel
from app.models import __all__  # import ทุก model
from app.core.db import async_engine


async def drop_all_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    print("✅ All tables dropped")


if __name__ == "__main__":
    asyncio.run(drop_all_tables())

# วิธีใช้ cd มาที่ backend_camphub
# $python ./scripts drop_db.py
