import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient

from main import app, engine, Base


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_database():
    with engine.begin() as connection:
        connection.execute(
            text("""
                TRUNCATE TABLE
                    note_tags,
                    notes,
                    tags,
                    users
                RESTART IDENTITY CASCADE
            """)
        )

@pytest.fixture
def client(clean_database):
    with TestClient(app) as client:
        yield client


@pytest.fixture
def auth_headers(client):
    email = "test@example.com"
    password = "password123"

    response = client.post(
        "/api/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    response = client.post(
        "/api/token",
        data={
            "username": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }