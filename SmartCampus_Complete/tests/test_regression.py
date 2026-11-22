
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


def test_invalid_booking_time(client):
    login(client, "student", "student123")

    response = client.post(
        "/api/bookings",
        json={
            "facility_id": 1,
            "booking_date": "2026-12-15",
            "start_time": "12:00",
            "end_time": "11:00",
            "purpose": "Project work"
        }
    )

    assert response.status_code == 400


def test_faculty_cannot_access_audit(client):
    login(client, "faculty", "faculty123")

    response = client.get("/api/audit")

    assert response.status_code == 403


def test_invalid_ticket_status_rejected(client):
    login(client, "student", "student123")

    created = client.post(
        "/api/tickets",
        json={
            "title": "Broken chair",
            "description": "Chair is damaged"
        }
    )

    ticket_id = created.json["ticket_id"]

    login(client, "manager", "manager123")

    response = client.put(
        f"/api/tickets/{ticket_id}",
        json={"status": "Invalid Status"}
    )

    assert response.status_code == 400


def test_missing_facility_rejected(client):
    login(client, "student", "student123")

    response = client.post(
        "/api/bookings",
        json={
            "facility_id": 9999,
            "booking_date": "2026-12-15",
            "start_time": "10:00",
            "end_time": "11:00",
            "purpose": "Project work"
        }
    )

    assert response.status_code == 404
