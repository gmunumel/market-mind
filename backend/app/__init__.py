"""
Market Mind backend package.
"""

# Re-export FastAPI app for ASGI servers.
from app.main import app

__all__ = ["app"]
