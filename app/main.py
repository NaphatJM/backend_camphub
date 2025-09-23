from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.db import init_db
from app.db.init_data import init_all_data
from app.routers import router
from app.core.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    await init_db()
    print("Database tables initialized")

    # Initialize default data
    await init_all_data()

    yield


app = FastAPI(
    title=settings.APP_NAME if hasattr(settings, "APP_NAME") else "CampHub API",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
