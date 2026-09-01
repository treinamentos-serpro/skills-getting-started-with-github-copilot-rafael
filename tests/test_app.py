from src.app import activities


ACTIVITY_FIELDS = {"description", "schedule", "max_participants", "participants"}


def test_get_activities_returns_seeded_activities(client):
    # Arrange
    expected_activity_names = set(activities)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert len(expected_activity_names) == 9
    assert set(response.json()) == expected_activity_names


def test_get_activities_returns_expected_structure(client):
    # Arrange
    expected_fields = ACTIVITY_FIELDS

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    for activity in response.json().values():
        assert set(activity) == expected_fields
        assert isinstance(activity["description"], str)
        assert isinstance(activity["schedule"], str)
        assert isinstance(activity["max_participants"], int)
        assert isinstance(activity["participants"], list)


def test_root_redirects_to_static_application(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_signup_adds_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]
    initial_participants = list(activities[activity_name]["participants"])

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}
    assert activities[activity_name]["participants"] == initial_participants


def test_signup_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"
    email = "new.student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_full_activity(client):
    # Arrange
    activity_name = "Futsal Team"
    activity = activities[activity_name]
    activity["participants"] = [
        f"student{index}@mergington.edu"
        for index in range(activity["max_participants"])
    ]
    initial_participants = list(activity["participants"])

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "waiting.student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Activity is full"}
    assert activity["participants"] == initial_participants


def test_signup_requires_email(client):
    # Arrange
    activity_name = "Chess Club"

    # Act
    response = client.post(f"/activities/{activity_name}/signup")

    # Assert
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", "email"]


def test_unregister_removes_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]

    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_rejects_participant_not_enrolled(client):
    # Arrange
    activity_name = "Chess Club"
    email = "not.enrolled@mergington.edu"
    initial_participants = list(activities[activity_name]["participants"])

    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student is not signed up for this activity"}
    assert activities[activity_name]["participants"] == initial_participants


def test_unregister_frees_place_for_new_signup(client):
    # Arrange
    activity_name = "Futsal Team"
    activity = activities[activity_name]
    activity["participants"] = [
        f"student{index}@mergington.edu"
        for index in range(activity["max_participants"])
    ]
    departing_email = activity["participants"][0]
    incoming_email = "incoming.student@mergington.edu"

    # Act
    unregister_response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": departing_email},
    )
    signup_response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": incoming_email},
    )

    # Assert
    assert unregister_response.status_code == 200
    assert signup_response.status_code == 200
    assert departing_email not in activity["participants"]
    assert incoming_email in activity["participants"]
    assert len(activity["participants"]) == activity["max_participants"]
