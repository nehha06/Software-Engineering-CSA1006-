
import pytest
import tempfile
import os

from backend import database
from backend.app import app


@pytest.fixture
def client(monkeypatch):
    db_file = tempfile.NamedTemporaryFile(delete=False)
    db_file.close()

    monkeypatch.setattr(database, "DB", db_file.name)
    database.init_db()

    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client

    os.unlink(db_file.name)


def login(client, username, password):
    return client.post(
        "/api/login",
        json={"username": username, "password": password}
    )


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json["status"] == "OK"


def test_valid_login(client):
    response = login(client, "student", "student123")
    assert response.status_code == 200
    assert response.json["role"] == "Student"


def test_invalid_login(client):
    response = login(client, "student", "wrongpassword")
    assert response.status_code == 401


def test_dashboard_requires_login(client):
    response = client.get("/api/dashboard")
    assert response.status_code == 401


def test_student_cannot_approve_booking(client):
    login(client, "student", "student123")
    response = client.put(
        "/api/bookings/1/decision",
        json={"decision": "approve"}
    )
    assert response.status_code == 403


def test_ticket_requires_title_and_description(client):
    login(client, "student", "student123")
    response = client.post(
        "/api/tickets",
        json={"title": "", "description": ""}
    )
    assert response.status_code == 400


def test_high_priority_ticket(client):
    login(client, "student", "student123")
    response = client.post(
        "/api/tickets",
        json={
            "title": "Urgent water leak",
            "description": "Water leaking in laboratory"
        }
    )
    assert response.status_code == 201
    assert response.json["priority"] == "High"


def test_low_priority_ticket(client):
    login(client, "student", "student123")
    response = client.post(
        "/api/tickets",
        json={
            "title": "General enquiry",
            "description": "Please provide information"
        }
    )
    assert response.status_code == 201
    assert response.json["priority"] == "Low"
