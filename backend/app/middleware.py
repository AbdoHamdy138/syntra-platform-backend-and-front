import time
import uuid
from datetime import datetime, timezone
from typing import Optional, Literal
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.models.api_models import ApiErrorResponse, ApiErrorCode

class AppException(Exception):
    def __init__(
        self,
        status_code: int,
        code: ApiErrorCode,
        message: str,
        request_id: Optional[str] = None
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.request_id = request_id
        super().__init__(message)

def raise_invalid_input(message: str) -> None:
    raise AppException(status_code=400, code="invalid_input", message=message)

def raise_unauthorized(message: str = "Authentication required") -> None:
    raise AppException(status_code=401, code="unauthorized", message=message)

def raise_forbidden(message: str = "Access forbidden") -> None:
    raise AppException(status_code=403, code="forbidden", message=message)

def raise_not_found(message: str = "Resource not found") -> None:
    raise AppException(status_code=404, code="not_found", message=message)

def raise_rate_limited(message: str = "Rate limit exceeded. Please try again later.") -> None:
    raise AppException(status_code=429, code="rate_limited", message=message)

def raise_dependency_unavailable(message: str = "External dependency unavailable") -> None:
    raise AppException(status_code=503, code="dependency_unavailable", message=message)

def raise_internal_error(message: str = "Internal server error") -> None:
    raise AppException(status_code=500, code="internal_error", message=message)

def get_request_id(request: Request) -> str:
    req_id = request.headers.get("x-request-id")
    if not req_id:
        req_id = getattr(request.state, "request_id", None)
    if not req_id:
        req_id = f"req_{uuid.uuid4().hex[:12]}"
        request.state.request_id = req_id
    return req_id

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    req_id = exc.request_id or get_request_id(request)
    now_iso = datetime.now(timezone.utc).isoformat()
    return JSONResponse(
        status_code=exc.status_code,
        headers={"X-Request-Id": req_id},
        content={
            "error": True,
            "code": exc.code,
            "message": exc.message,
            "request_id": req_id,
            "generated_at": now_iso
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    req_id = get_request_id(request)
    now_iso = datetime.now(timezone.utc).isoformat()
    # Build clean human-readable error summary
    errors = exc.errors()
    msg_parts = []
    for err in errors:
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        msg = err.get("msg", "invalid")
        msg_parts.append(f"{loc}: {msg}")
    error_msg = "; ".join(msg_parts) if msg_parts else "Invalid request payload"

    return JSONResponse(
        status_code=400,
        headers={"X-Request-Id": req_id},
        content={
            "error": True,
            "code": "invalid_input",
            "message": error_msg,
            "request_id": req_id,
            "generated_at": now_iso
        }
    )

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    req_id = get_request_id(request)
    now_iso = datetime.now(timezone.utc).isoformat()
    code_map: dict[int, ApiErrorCode] = {
        400: "invalid_input",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        429: "rate_limited",
        503: "dependency_unavailable"
    }
    code = code_map.get(exc.status_code, "internal_error")
    msg = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        headers={"X-Request-Id": req_id},
        content={
            "error": True,
            "code": code,
            "message": msg,
            "request_id": req_id,
            "generated_at": now_iso
        }
    )

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    req_id = get_request_id(request)
    now_iso = datetime.now(timezone.utc).isoformat()
    return JSONResponse(
        status_code=500,
        headers={"X-Request-Id": req_id},
        content={
            "error": True,
            "code": "internal_error",
            "message": f"An unexpected error occurred: {str(exc)}",
            "request_id": req_id,
            "generated_at": now_iso
        }
    )

