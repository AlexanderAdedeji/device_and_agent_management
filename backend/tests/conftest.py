from typing import Generator
from unittest import mock

import pytest
from backend.app.db.utils import DataInitializer
from backend.app.db.session import SessionLocal
from backend.app.main import app
from fastapi import testclient
from sqlalchemy.orm import Session


@pytest.fixture(scope="session")
def db() -> Generator:
    yield SessionLocal()


@pytest.fixture(scope="module", autouse=True)
def mock_basic_publish():
    from backend.app.tasks import devices

    def f(*args, **kwargs):
        pass
        
    with mock.patch.object(devices, "send_notification_to_devices", f):
        yield


@pytest.fixture(scope="module", autouse=True)
def mock_post_mark_client(db: Session):
    class Email:
        def __init__(self, *args, **kwargs):
            pass

        def send_with_template(*args, **kwargs):
            return {"Message": "OK", "ErrorCode": 0}

    class MockPostMarkClient:
        def __init__(self, *args, **kwargs):
            self.emails = Email()

    import postmarker

    with mock.patch.object(postmarker.core, "PostmarkClient", MockPostMarkClient):
        yield


@pytest.fixture(scope="module")
def client() -> testclient.TestClient:
    c = testclient.TestClient(app)
    c.headers.update({"X-API-KEY": "DUMMY_API_KEY"})
    return c
