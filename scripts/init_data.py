import asyncio
from app.core.db import init_db
from app.db.init_data import init_all_data


async def main():
    # สร้างตารางก่อน
    await init_db()
    print("✅ Database tables created")

    # seed ข้อมูล
    await init_all_data()
    print("🎉 Database seeded successfully")


if __name__ == "__main__":
    asyncio.run(main())
