from contextlib import asynccontextmanager
from datetime import date
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import init_db, get_session, User, async_engine
from app.core.security import hash_password
from app.routers import router
from app.core.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with AsyncSession(async_engine) as session:
        result = await session.execute(select(User))
        if not result.first():
            session.add(
                User(
                    username="user_demo",
                    email="demo@mail.com",
                    first_name="Demo",
                    last_name="User",
                    birth_date=date(1990, 1, 1),
                    hashed_password=hash_password("123456"),
                )
            )
            await session.commit()
            print("Demo user created")
    yield


app = FastAPI(
    title=settings.APP_NAME if hasattr(settings, "APP_NAME") else "CampHub API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
