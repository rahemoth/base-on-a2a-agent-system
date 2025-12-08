#!/usr/bin/env python3
"""
Startup script for A2A Multi-Agent System backend
"""
import uvicorn
from backend.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
