from fastapi import FastAPI

from api.routes.auth import router as auth_router
from api.routes.users import router as users_router

app = FastAPI(title="Wavelength API", version="0.1.0")

app.include_router(auth_router)
app.include_router(users_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
