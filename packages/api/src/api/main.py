from fastapi import FastAPI

from api.routes import chat
from api.routes.auth import router as auth_router
from api.routes.compatibility import router as compatibility_router
from api.routes.matching import router as matching_router
from api.routes.music import router as music_router
from api.routes.users import router as users_router

app = FastAPI(title="Wavelength API", version="0.1.0")

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(music_router)
app.include_router(matching_router)
app.include_router(compatibility_router)
app.include_router(chat.router)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
