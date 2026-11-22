
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


def test_booking_saved_in_database(client):
    login(client, "student", "student123")

    response = client.post(
        "/api/bookings",
        json={
            "facility_id": 1,
            "booking_date": "2026-12-10",
            "start_time": "10:00",
            "end_time": "11:00",
            "purpose": "Project work"
        }
    )

    assert response.status_code == 201

    bookings = client.get("/api/bookings")
    assert len(bookings.json) == 1
    assert bookings.json[0]["purpose"] == "Project work"


def test_ticket_saved_in_database(client):
    login(client, "student", "student123")

    response = client.post(
        "/api/tickets",
        json={
            "title": "Broken fan",
            "description": "Fan is not working"
        }
    )

    assert response.status_code == 201

    tickets = client.get("/api/tickets")
    assert len(tickets.json) == 1
    assert tickets.json[0]["title"] == "Broken fan"


def test_booking_overlap_rejected(client):
    login(client, "student", "student123")

    first = client.post(
        "/api/bookings",
        json={
            "facility_id": 1,
            "booking_date": "2026-12-11",
            "start_time": "10:00",
            "end_time": "11:00",
            "purpose": "First booking"
        }
    )

    login(client, "manager", "manager123")

    client.put(
        f"/api/bookings/{first.json['booking_id']}/decision",
        json={"decision": "approve"}
    )

    login(client, "student", "student123")

    second = client.post(
        "/api/bookings",
        json={
            "facility_id": 1,
            "booking_date": "2026-12-11",
            "start_time": "10:30",
            "end_time": "11:30",
            "purpose": "Second booking"
        }
    )

    login(client, "manager", "manager123")

    response = client.put(
        f"/api/bookings/{second.json['booking_id']}/decision",
        json={"decision": "approve"}
    )

    assert response.status_code == 409


def test_ticket_update_saved(client):
    login(client, "student", "student123")

    created = client.post(
        "/api/tickets",
        json={
            "title": "Broken light",
            "description": "Light is not working"
        }
    )

    ticket_id = created.json["ticket_id"]

    login(client, "manager", "manager123")

    response = client.put(
        f"/api/tickets/{ticket_id}",
        json={
            "status": "Resolved",
            "notes": "Light repaired"
        }
    )

    assert response.status_code == 200

    tickets = client.get("/api/tickets")
    assert tickets.json[0]["status"] == "Resolved"
