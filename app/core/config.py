from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "dev"
    database_url: str = "sqlite:///./app.db"
    redis_url: str = "redis://localhost:6379/0"

    secret_key: str = "change-this-in-env"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60


settings = Settings()
