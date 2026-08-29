def test_register(client):
    response = client.post(
        "/api/register",
        json={
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "hashed_password" not in data


def test_register_duplicate_email(client):
    client.post(
        "/api/register",
        json={
            "email": "test@example.com",
            "password": "password123",
        },
    )

    response = client.post(
        "/api/register",
        json={
            "email": "test@example.com",
            "password": "differentpassword",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_login(client):
    client.post(
        "/api/register",
        json={
            "email": "login@example.com",
            "password": "password123",
        },
    )

    response = client.post(
        "/api/token",
        data={
            "username": "login@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    client.post(
        "/api/register",
        json={
            "email": "wrong@example.com",
            "password": "password123",
        },
    )

    response = client.post(
        "/api/token",
        data={
            "username": "wrong@example.com",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_get_notes_requires_authentication(client):
    response = client.get("/api/notes")

    assert response.status_code == 401


def test_create_note(client, auth_headers):
    response = client.post(
        "/api/notes",
        headers=auth_headers,
        json={
            "title": "My first note",
            "text": "Hello from pytest",
            "tags": ["python", "testing"],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "My first note"
    assert data["text"] == "Hello from pytest"
    assert set(data["tags"]) == {"python", "testing"}
    assert data["id"] is not None
    assert data["created_at"] is not None


def test_get_notes(client, auth_headers):
    client.post(
        "/api/notes",
        headers=auth_headers,
        json={
            "title": "Python",
            "text": "Learning pytest",
            "tags": ["python"],
        },
    )

    client.post(
        "/api/notes",
        headers=auth_headers,
        json={
            "title": "Docker",
            "text": "Learning Docker",
            "tags": ["docker"],
        },
    )

    response = client.get(
        "/api/notes",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_get_note_by_id(client, auth_headers):
    create_response = client.post(
        "/api/notes",
        headers=auth_headers,
        json={
            "title": "Specific note",
            "text": "Some text",
            "tags": ["test"],
        },
    )

    assert create_response.status_code == 200

    note_id = create_response.json()["id"]

    response = client.get(
        f"/api/notes/{note_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == note_id
    assert data["title"] == "Specific note"
    assert data["text"] == "Some text"
    assert data["tags"] == ["test"]


def test_get_nonexistent_note(client, auth_headers):
    response = client.get(
        "/api/notes/999999",
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_update_note(client, auth_headers):
    create_response = client.post(
        "/api/notes",
        headers=auth_headers,
        json={
            "title": "Old title",
            "text": "Old text",
            "tags": ["old"],
        },
    )

    note_id = create_response.json()["id"]

    response = client.put(
        f"/api/notes/{note_id}",
        headers=auth_headers,
        json={
            "title": "New title",
            "text": "New text",
            "tags": ["new", "updated"],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == note_id
    assert data["title"] == "New title"
    assert data["text"] == "New text"
    assert set(data["tags"]) == {"new", "updated"}


def test_delete_note(client, auth_headers):
    create_response = client.post(
        "/api/notes",
        headers=auth_headers,
        json={
            "title": "Delete me",
            "text": "This should disappear",
            "tags": [],
        },
    )

    note_id = create_response.json()["id"]

    response = client.delete(
        f"/api/notes/{note_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    response = client.get(
        f"/api/notes/{note_id}",
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_user_cannot_access_another_users_note(client):
    response = client.post(
        "/api/register",
        json={
            "email": "user_a@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200

    response = client.post(
        "/api/token",
        data={
            "username": "user_a@example.com",
            "password": "password123",
        },
    )

    headers_a = {
        "Authorization": f"Bearer {response.json()['access_token']}"
    }

    response = client.post(
        "/api/notes",
        headers=headers_a,
        json={
            "title": "Private note",
            "text": "User B must not see this",
            "tags": [],
        },
    )

    assert response.status_code == 200

    note_id = response.json()["id"]

    response = client.post(
        "/api/register",
        json={
            "email": "user_b@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200

    response = client.post(
        "/api/token",
        data={
            "username": "user_b@example.com",
            "password": "password123",
        },
    )

    headers_b = {
        "Authorization": f"Bearer {response.json()['access_token']}"
    }

    response = client.get(
        f"/api/notes/{note_id}",
        headers=headers_b,
    )

    assert response.status_code == 404


def test_user_cannot_update_another_users_note(client):
    client.post(
        "/api/register",
        json={
            "email": "user_a@example.com",
            "password": "password123",
        },
    )

    response = client.post(
        "/api/token",
        data={
            "username": "user_a@example.com",
            "password": "password123",
        },
    )

    headers_a = {
        "Authorization": f"Bearer {response.json()['access_token']}"
    }

    response = client.post(
        "/api/notes",
        headers=headers_a,
        json={
            "title": "Original",
            "text": "Original text",
            "tags": [],
        },
    )

    note_id = response.json()["id"]

    client.post(
        "/api/register",
        json={
            "email": "user_b@example.com",
            "password": "password123",
        },
    )

    response = client.post(
        "/api/token",
        data={
            "username": "user_b@example.com",
            "password": "password123",
        },
    )

    headers_b = {
        "Authorization": f"Bearer {response.json()['access_token']}"
    }

    response = client.put(
        f"/api/notes/{note_id}",
        headers=headers_b,
        json={
            "title": "Hacked",
            "text": "Modified by B",
            "tags": [],
        },
    )

    assert response.status_code == 404

    response = client.get(
        f"/api/notes/{note_id}",
        headers=headers_a,
    )

    data = response.json()

    assert data["title"] == "Original"
    assert data["text"] == "Original text"


def test_user_cannot_delete_another_users_note(client):
    client.post(
        "/api/register",
        json={
            "email": "user_a@example.com",
            "password": "password123",
        },
    )

    response = client.post(
        "/api/token",
        data={
            "username": "user_a@example.com",
            "password": "password123",
        },
    )

    headers_a = {
        "Authorization": f"Bearer {response.json()['access_token']}"
    }

    response = client.post(
        "/api/notes",
        headers=headers_a,
        json={
            "title": "Protected note",
            "text": "Do not delete",
            "tags": [],
        },
    )

    note_id = response.json()["id"]
    client.post(
        "/api/register",
        json={
            "email": "user_b@example.com",
            "password": "password123",
        },
    )

    response = client.post(
        "/api/token",
        data={
            "username": "user_b@example.com",
            "password": "password123",
        },
    )

    headers_b = {
        "Authorization": f"Bearer {response.json()['access_token']}"
    }

    response = client.delete(
        f"/api/notes/{note_id}",
        headers=headers_b,
    )

    assert response.status_code == 404

    response = client.get(
        f"/api/notes/{note_id}",
        headers=headers_a,
    )

    assert response.status_code == 200



def test_invalid_token(client):
    response = client.get(
        "/api/notes",
        headers={"Authorization": "Bearer completely-invalid-token"},
    )

    assert response.status_code == 401

def test_register_missing_password(client):
    response = client.post(
        "/api/register",
        json={
            "email": "test@example.com",
        },
    )

    assert response.status_code == 422

def test_register_missing_email(client):
    response = client.post(
        "/api/register",
        json={
            "password": "password123",
        },
    )

    assert response.status_code == 422

def test_create_note_without_text(client, auth_headers):
    response = client.post(
        "/api/notes",
        headers=auth_headers,
        json={
            "title": "No text",
            "tags": [],
        },
    )

    assert response.status_code == 422


def test_search_notes(client, auth_headers):
    client.post(
        "/api/notes",
        headers=auth_headers,
        json={
            "title": "Python tutorial",
            "text": "Learning FastAPI",
            "tags": [],
        },
    )

    client.post(
        "/api/notes",
        headers=auth_headers,
        json={
            "title": "Docker",
            "text": "Containerization",
            "tags": [],
        },
    )

    response = client.get(
        "/api/notes?search=python",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["title"] == "Python tutorial"

def test_search_is_case_insensitive(client, auth_headers):
    client.post(
        "/api/notes",
        headers=auth_headers,
        json={
            "title": "Python",
            "text": "PYTHON FASTAPI",
            "tags": [],
        },
    )

    response = client.get(
        "/api/notes?search=python",
        headers=auth_headers,
    )

    assert response.json()["total"] == 1

def test_filter_notes_by_tag(client, auth_headers):
    client.post(
        "/api/notes",
        headers=auth_headers,
        json={
            "title": "Python",
            "text": "Python stuff",
            "tags": ["python"],
        },
    )

    client.post(
        "/api/notes",
        headers=auth_headers,
        json={
            "title": "Docker",
            "text": "Docker stuff",
            "tags": ["docker"],
        },
    )

    response = client.get(
        "/api/notes?tag=python",
        headers=auth_headers,
    )

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["title"] == "Python"


def test_filter_notes_by_date(client, auth_headers):
    client.post(
        "/api/notes",
        headers=auth_headers,
        json={
            "title": "Today's note",
            "text": "Text",
            "tags": [],
        },
    )

    response = client.get(
        "/api/notes?start_date=2026-08-29",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1

def test_user_cannot_see_another_users_notes(client):
    client.post(
        "/api/register",
        json={
            "email": "a@example.com",
            "password": "password123",
        },
    )

    response = client.post(
        "/api/token",
        data={
            "username": "a@example.com",
            "password": "password123",
        },
    )

    headers_a = {
        "Authorization": f"Bearer {response.json()['access_token']}"
    }

    client.post(
        "/api/notes",
        headers=headers_a,
        json={
            "title": "Private A",
            "text": "Secret",
            "tags": [],
        },
    )

    client.post(
        "/api/register",
        json={
            "email": "b@example.com",
            "password": "password123",
        },
    )

    response = client.post(
        "/api/token",
        data={
            "username": "b@example.com",
            "password": "password123",
        },
    )

    headers_b = {
        "Authorization": f"Bearer {response.json()['access_token']}"
    }

    response = client.get(
        "/api/notes",
        headers=headers_b,
    )

    data = response.json()

    assert data["total"] == 0
    assert data["items"] == []

def test_delete_nonexistent_note(client, auth_headers):
    response = client.delete(
        "/api/notes/999999",
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_update_nonexistent_note(client, auth_headers):
    response = client.put(
        "/api/notes/999999",
        headers=auth_headers,
        json={
            "title": "Whatever",
            "text": "Whatever",
            "tags": [],
        },
    )

    assert response.status_code == 404