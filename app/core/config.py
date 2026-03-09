from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "dev"
    database_url: str = "postgresql+psycopg2://app:app@localhost:5432/appdb"
    redis_url: str = "redis://localhost:6379/0"

settings = Settings()
