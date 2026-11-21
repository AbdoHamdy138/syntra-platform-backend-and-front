import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, APIRouter, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import settings
from app.middleware import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    generic_exception_handler,
    get_request_id
)
from app.routers import (
    health,
    auth,
    query,
    entities,
    history,
    labs,
    export
)

app = FastAPI(
    title="SYNTRA Threat Intelligence Backend",
    description="Authoritative, evidence-grounded threat intelligence API with MITRE ATT&CK integration, interactive cyber labs, and OTP authentication.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS Configuration
origins = [
    settings.CLIENT_ORIGIN,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4000",
    "http://127.0.0.1:4000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-Id", "Content-Disposition"]
)

# Request ID & Logging Middleware
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    req_id = request.headers.get("x-request-id") or f"req_{uuid.uuid4().hex[:12]}"
    request.state.request_id = req_id
    response = await call_next(request)
    response.headers["X-Request-Id"] = req_id
    return response

# Exception Handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# API v1 Router Registration
v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(health.router)
v1_router.include_router(auth.router)
v1_router.include_router(query.router)
v1_router.include_router(entities.router)
v1_router.include_router(history.router)
v1_router.include_router(labs.router)
v1_router.include_router(export.router)

app.include_router(v1_router)

@app.get("/")
def root():
    return {
        "service": "SYNTRA Threat Intelligence Backend",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/api/v1/health",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

