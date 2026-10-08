from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    spotify_client_id: str
    spotify_client_secret: str
    spotify_redirect_uri: str
    jwt_secret: str
    database_url: str
    frontend_url: str = "http://localhost:3000"
    redis_url: str = "redis://localhost:6379/0"

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, value: str) -> str:
        """Hosts like Railway/Heroku hand out postgres:// or postgresql:// URLs.

        SQLAlchemy maps both to the psycopg2 driver, but this project uses psycopg v3,
        so rewrite them to postgresql+psycopg://. URLs that already name a driver are kept.
        """
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value[len(prefix):]
        return value


settings = Settings()