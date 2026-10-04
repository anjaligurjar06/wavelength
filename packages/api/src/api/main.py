import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.errors import register_exception_handlers
from api.logging_config import configure_logging
from api.routes import chat
from api.routes.auth import router as auth_router
from api.routes.compatibility import router as compatibility_router
from api.routes.matching import router as matching_router
from api.routes.music import router as music_router
from api.routes.trust_safety import router as trust_safety_router
from api.routes.users import router as users_router

configure_logging()
access_logger = logging.getLogger("wavelength.access")

app = FastAPI(title="Wavelength API", version="0.1.0")
register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = uuid.uuid4().hex[:12]
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - start) * 1000
        access_logger.error(
            "%s %s -> 500 %.1fms rid=%s",
            request.method, request.url.path, duration_ms, request_id,
        )
        raise
    duration_ms = (time.perf_counter() - start) * 1000
    level = logging.DEBUG if request.url.path == "/health" else logging.INFO
    access_logger.log(
        level,
        "%s %s -> %s %.1fms rid=%s",
        request.method, request.url.path, response.status_code, duration_ms, request_id,
    )
    response.headers["X-Request-ID"] = request_id
    return response


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(music_router)
app.include_router(matching_router)
app.include_router(compatibility_router)
app.include_router(chat.router)
app.include_router(trust_safety_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}