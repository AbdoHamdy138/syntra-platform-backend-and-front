"""
SYNTRA FastAPI Application Entrypoint.
Exposes `app` from `app.main` for ASGI servers (Uvicorn / Gunicorn).
"""
from app.main import app

__all__ = ["app"]
