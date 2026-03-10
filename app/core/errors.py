import logging
from datetime import datetime, timezone

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("app.error")


def _body(status: int, code: str, message: str, detail=None, request_id: str | None = None):
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "code": code,
        "message": message,
        "detail": detail or [],
        "request_id": request_id,
    }


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(
        "http exception",
        extra={
            "request_id": _request_id(request),
            "method": request.method,
            "path": request.url.path,
            "status_code": exc.status_code,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=_body(
            exc.status_code, "HTTP_ERROR", str(exc.detail), request_id=_request_id(request)
        ),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(
        "validation exception",
        extra={
            "request_id": _request_id(request),
            "method": request.method,
            "path": request.url.path,
            "status_code": 422,
        },
    )
    return JSONResponse(
        status_code=422,
        content=_body(
            422, "VALIDATION_ERROR", "invalid request", exc.errors(), _request_id(request)
        ),
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "unhandled exception",
        extra={
            "request_id": _request_id(request),
            "method": request.method,
            "path": request.url.path,
            "status_code": 500,
        },
    )
    return JSONResponse(
        status_code=500,
        content=_body(500, "INTERNAL_SERVER_ERROR", str(exc), request_id=_request_id(request)),
    )
