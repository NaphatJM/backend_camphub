import asyncio
from app.core.db import init_db

if __name__ == "__main__":
    asyncio.run(init_db())
    print("Database initialized.")
