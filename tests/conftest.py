from pathlib import Path
import pytest

from app.db.base import Base
from app.db.session import engine
import app.models  # noqa: F401


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    db_file = Path("app.db")
    if db_file.exists():
        db_file.unlink()
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
