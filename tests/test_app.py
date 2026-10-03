from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_static_app(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_details(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == activities
    assert activities
    for activity in response.json().values():
        assert set(activity) == {
            "description",
            "schedule",
            "max_participants",
            "participants",
        }


def test_signup_adds_participant(client):
    activity_name = next(iter(activities))
    email = "new.student@mergington.edu"

    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}",
    }
    assert email in client.get("/activities").json()[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(client):
    activity_name = next(iter(activities))
    email = activities[activity_name]["participants"][0]

    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity",
    }


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown Activity/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_requires_email(client):
    activity_name = next(iter(activities))

    response = client.post(f"/activities/{activity_name}/signup")

    assert response.status_code == 422


def test_unregister_removes_participant(client):
    activity_name = next(iter(activities))
    email = activities[activity_name]["participants"][0]

    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}",
    }
    assert email not in client.get("/activities").json()[activity_name]["participants"]


def test_unregister_rejects_unknown_participant(client):
    activity_name = next(iter(activities))

    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": "unknown@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Participant not found"}


def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown Activity/unregister",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_requires_email(client):
    activity_name = next(iter(activities))

    response = client.delete(f"/activities/{activity_name}/unregister")

    assert response.status_code == 422
