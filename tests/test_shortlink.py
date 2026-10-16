import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine

client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_shorten_and_redirect():
    r = client.post("/shorten", json={"url": "https://example.com/page"})
    assert r.status_code == 201
    code = r.json()["code"]
    assert len(code) == 6
    r = client.get(f"/{code}", follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == "https://example.com/page"


def test_click_counter():
    code = client.post("/shorten", json={"url": "https://example.com"}).json()["code"]
    for _ in range(3):
        client.get(f"/{code}", follow_redirects=False)
    assert client.get(f"/stats/{code}").json()["clicks"] == 3


def test_invalid_url_rejected():
    assert client.post("/shorten", json={"url": "not-a-url"}).status_code == 422


def test_unknown_code_404():
    assert client.get("/zzzzzz", follow_redirects=False).status_code == 404
