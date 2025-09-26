from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from app.api import videos, highlights, health
from app.core.config import settings
from app.core.database import engine, Base
from app.core.websocket import websocket_endpoint

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    title="Touchdown API",
    description="Video Highlight Reel Generator API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(videos.router, prefix="/api/videos", tags=["videos"])
app.include_router(highlights.router, prefix="/api/highlights", tags=["highlights"])
app.websocket("/ws/{client_id}")(websocket_endpoint)

@app.get("/")
async def root():
    return {"message": "Touchdown API - Video Highlight Generator", "version": "1.0.0"}