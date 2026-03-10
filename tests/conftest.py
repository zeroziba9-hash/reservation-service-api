from pathlib import Path
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.base import Base
import app.models  # noqa: F401
from app.main import app
from app.deps import get_db, get_redis

TEST_DB_FILE = Path("test_app.db")
TEST_DB_URL = "sqlite:///./test_app.db"

test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


class FakeRedis:
    def __init__(self):
        self.store: dict[str, str] = {}

    def get(self, key: str):
        return self.store.get(key)

    def set(self, key: str, value: str, nx: bool = False, ex: int | None = None):
        if nx and key in self.store:
            return False
        self.store[key] = value
        return True

    def setex(self, key: str, _seconds: int, value: str):
        self.store[key] = value

    def delete(self, key: str):
        self.store.pop(key, None)


def override_get_redis():
    return fake_redis


fake_redis = FakeRedis()


@pytest.fixture(scope="session", autouse=True)
def setup_override():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis
    yield
    app.dependency_overrides.clear()
    test_engine.dispose()
    if TEST_DB_FILE.exists():
        TEST_DB_FILE.unlink()


@pytest.fixture(autouse=True)
def reset_tables():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    fake_redis.store.clear()
    yield
