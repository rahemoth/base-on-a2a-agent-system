"""
Main FastAPI application for A2A Agent System
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from backend.api import mcp_router
from backend.api.agents_a2a import router as agents_router
from backend.config import settings
from backend.agents.a2a_manager import a2a_agent_manager
from backend.mcp import mcp_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("Starting A2A Agent System...")
    yield
    # Shutdown
    print("Shutting down A2A Agent System...")
    await a2a_agent_manager.cleanup_all()
    await mcp_manager.close_all()


app = FastAPI(
    title="A2A Multi-Agent Collaboration System",
    description="A multi-agent collaboration system built with official A2A SDK and MCP support",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_origins=settings.allowed_origins.split("*"),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agents_router)
app.include_router(mcp_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "A2A Multi-Agent Collaboration System",
        "version": "2.0.0",
        "a2a_sdk": "official a2a-sdk v0.3.20+",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


# Serve static files for frontend
if os.path.exists("frontend/dist"):
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
