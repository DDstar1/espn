from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str  # required, no default
    SERVER_HOST: str | None = None  # optional; will pick up env if present

    class Config:
        env_file = ".env"


settings = Settings()
