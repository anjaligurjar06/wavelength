from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.errors import register_exception_handlers
from api.routes import chat
from api.routes.auth import router as auth_router
from api.routes.compatibility import router as compatibility_router
from api.routes.matching import router as matching_router
from api.routes.music import router as music_router
from api.routes.trust_safety import router as trust_safety_router
from api.routes.users import router as users_router

app = FastAPI(title="Wavelength API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app = FastAPI(title="Wavelength API", version="0.1.0")
register_exception_handlers(app)
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
