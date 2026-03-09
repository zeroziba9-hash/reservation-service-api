from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

kwargs = {"pool_pre_ping": True}
if settings.database_url.startswith("sqlite"):
    kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.database_url, **kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
