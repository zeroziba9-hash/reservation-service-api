from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "dev"
    database_url: str = "sqlite:///./app.db"
    redis_url: str = "redis://localhost:6379/0"


settings = Settings()
