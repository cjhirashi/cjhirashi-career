"""
cjhirashi-career-ai - aplicación FastAPI del harness de agentes.

Los routers se importan de forma incondicional: un ImportError debe romper el arranque,
nunca silenciarse (hazard documentado en la spec 009).
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from config import settings
from database import close_db
from routes import health


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await close_db()


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)

app.include_router(health.router)
