import os
import datetime
import pytest
from typing import Any, Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api import security
from app.api import utils
from app.api.models import Base
from app.main import app, get_db

FAKE_TIME = datetime.datetime(2020, 5, 30, 17, 35, 55)

# Configure a test database (in memory)
SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite://")
engine = create_engine(
    SQLALCHEMY_DATABASE_URI, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine,
)
Base.metadata.create_all(bind=engine)


@pytest.fixture
def datetime_now(monkeypatch):

    class FakeDateTime:
        @classmethod
        def now(cls):
            return FAKE_TIME

        @classmethod
        def utcnow(cls):
            return FAKE_TIME

    monkeypatch.setattr(security, "datetime", FakeDateTime)
    monkeypatch.setattr(utils, 'datetime', FakeDateTime)


@pytest.fixture()
def client() -> Generator[TestClient, Any, None]:
    """
    Create a new FastAPI TestClient fixture to override the `get_db`.
    """

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
