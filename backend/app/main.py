"""
Main FastAPI Application Entrypoint.
Implements Module 40 (API Design), Module 43 (Backend Structure), and Database Lifespan.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.database import init_db
from app.api.cases import router as cases_router
from app.api.court import router as court_router
from app.api.audit import router as audit_router
from app.api.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database Tables
    await init_db()
    yield
    # Shutdown: Clean up resources


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Domain-Independent Agentic AI Decision Validation Platform",
    lifespan=lifespan,
)

# Enable CORS for React frontend (Vite dev server default http://localhost:5173 or any port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router)
app.include_router(cases_router)
app.include_router(court_router)
app.include_router(audit_router)


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
