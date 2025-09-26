from fastapi import FastAPI
from .config import settings

app = FastAPI(
    title=settings.app_name,
    description="A FastAPI application built with uv",
    version=settings.app_version,
    debug=settings.debug
)


@app.get("/")
async def processVideo():
    return {"message": f"Hello from {settings.openai_api_key}!", "version": settings.app_version}



@app.get("/config")
async def get_config():
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "debug": settings.debug
    }

