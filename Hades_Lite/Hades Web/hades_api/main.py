"""
Hades API - Backend para análisis forense de documentos.

FastAPI application con autenticación Keycloak.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import health, jobs, admin, export
from .database import engine, Base
from .config import settings

# Crear tablas
Base.metadata.create_all(bind=engine)

# App
app = FastAPI(
    title=settings.APP_NAME,
    description="API para análisis forense de documentos de identidad",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router)
app.include_router(jobs.router)
app.include_router(admin.router)
app.include_router(export.router)


@app.on_event("startup")
async def startup_event():
    """Evento de inicio"""
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} iniciado")
    print(f"📊 Database: {settings.DATABASE_URL.split('@')[-1]}")
    print(f"🔐 Keycloak: {settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}")


@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre"""
    print(f"👋 {settings.APP_NAME} detenido")
