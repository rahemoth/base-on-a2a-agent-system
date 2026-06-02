#!/usr/bin/env python3
"""
Startup script for A2A Multi-Agent System backend
"""
import logging
import uvicorn
import socket
from backend.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def check_port_available(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('127.0.0.1', port))
            print(f"Port {port} is available")
            return True
    except socket.error as e:
        print(f"Port {port} is not available: {e}")
        return False

if __name__ == "__main__":
    print(f"Starting A2A Agent System on {settings.host}:{settings.port}")

    if check_port_available(settings.port):
        uvicorn.run(
            "backend.main:app",
            host=settings.host,
            port=settings.port,
            reload=False,
            log_level="info"
        )
    else:
        print(f"Port {settings.port} is not available, exiting...")