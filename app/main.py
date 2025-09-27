from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import asyncio
import logging

from app.routers import router
from app.core.config import get_settings
from app.core.exceptions import BaseCustomException
from app.core.error_handlers import (
    custom_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
)
from app.core.cache import cache_cleanup_task

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    # await init_db()
    # print("Database tables initialized")

    # Initialize default data
    # await init_all_data()

    # Start background tasks
    cache_task = asyncio.create_task(cache_cleanup_task())

    try:
        yield
    finally:
        # Cleanup background tasks
        cache_task.cancel()
        try:
            await cache_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title=settings.APP_NAME if hasattr(settings, "APP_NAME") else "CampHub API",
    lifespan=lifespan,
    description="CampHub Backend API with comprehensive error handling and caching",
    version="1.0.0",
)

# Add exception handlers
app.add_exception_handler(BaseCustomException, custom_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "camphub-api"}
