from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from app.db.database import init_db, engine
from app.models import User
from app.core.security import hash_password
from app.routers import router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    with Session(engine) as session:
        if not session.exec(select(User)).first():
            session.add(
                User(
                    username="user_demo",
                    email="demo@mail.com",
                    full_name="Demo User",
                    hashed_password=hash_password("123456"),
                )
            )
            session.commit()
            print("Demo user created")
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
