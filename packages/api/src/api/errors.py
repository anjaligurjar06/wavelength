import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("wavelength.api")

PROBLEM_JSON = "application/problem+json"


def _problem(
    request: Request,
    status: int,
    detail,
    headers: dict | None = None,
    **extra,
) -> JSONResponse:
    body = {
        "type": "about:blank",
        "title": HTTPStatus(status).phrase,
        "status": status,
        "detail": detail,
        "instance": request.url.path,
        **extra,
    }
    return JSONResponse(
        jsonable_encoder(body),
        status_code=status,
        media_type=PROBLEM_JSON,
        headers=headers,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code >= 500:
        logger.error("%s %s -> %s", request.method, request.url.path, exc.status_code)
    else:
        logger.info("%s %s -> %s %s", request.method, request.url.path, exc.status_code, exc.detail)
    return _problem(request, exc.status_code, exc.detail, headers=exc.headers)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return _problem(
        request, 422, "Request validation failed", errors=exc.errors()
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return _problem(request, 500, "Internal server error")


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)