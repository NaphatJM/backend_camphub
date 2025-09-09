import asyncio
from app.models import init_db

if __name__ == "__main__":
    asyncio.run(init_db())
    print("Database initialized.")
