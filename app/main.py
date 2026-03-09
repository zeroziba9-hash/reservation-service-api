from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from app.api.routes import router
from app.core.errors import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)

app = FastAPI(title="FastAPI Service Template", version="0.1.0")
app.include_router(router)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
