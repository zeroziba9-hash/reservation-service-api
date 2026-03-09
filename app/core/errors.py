from datetime import datetime, timezone
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def _body(status: int, code: str, message: str, detail=None):
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "code": code,
        "message": message,
        "detail": detail or [],
    }


async def http_exception_handler(_: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=_body(exc.status_code, "HTTP_ERROR", str(exc.detail)),
    )


async def validation_exception_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=_body(422, "VALIDATION_ERROR", "invalid request", exc.errors()),
    )


async def unhandled_exception_handler(_: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=_body(500, "INTERNAL_SERVER_ERROR", str(exc)),
    )
