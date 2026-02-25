import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add src to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


@pytest.fixture
def client():
    """Fixture to provide a test client for the FastAPI app."""
    return TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_200(self, client):
        """Test that getting activities returns a 200 status code"""
        # Arrange
        # (no setup needed)

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200

    def test_get_activities_returns_dict(self, client):
        """Test that activities endpoint returns a dictionary"""
        # Arrange
        # (no setup needed)

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        assert isinstance(data, dict)

    def test_get_activities_contains_expected_fields(self, client):
        """Test that each activity has required fields"""
        # Arrange
        expected_fields = ["description", "schedule", "max_participants", "participants"]

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        for activity_name, activity_data in activities.items():
            for field in expected_fields:
                assert field in activity_data, f"Missing '{field}' in {activity_name}"
            assert isinstance(activity_data["participants"], list)

    def test_get_activities_has_data(self, client):
        """Test that activities list is not empty"""
        # Arrange
        # (no setup needed)

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        assert len(activities) > 0


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_for_valid_activity(self, client):
        """Test signing up for an existing activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "test@example.com"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]

    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant to the activity"""
        # Arrange
        activity_name = "Programming Class"
        email = "newstudent@mergington.edu"

        # Act
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        activities_response = client.get("/activities")

        # Assert
        assert signup_response.status_code == 200
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]

    def test_signup_for_nonexistent_activity_returns_404(self, client):
        """Test that signing up for a non-existent activity returns 404"""
        # Arrange
        fake_activity = "Nonexistent Activity"
        email = "test@example.com"

        # Act
        response = client.post(
            f"/activities/{fake_activity}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_duplicate_signup_returns_400(self, client):
        """Test that signing up twice returns a 400 error"""
        # Arrange
        activity_name = "Tennis Club"
        email = "duplicate@mergington.edu"

        # Act
        first_signup = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        second_signup = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert first_signup.status_code == 200
        assert second_signup.status_code == 400
        assert "already signed up" in second_signup.json()["detail"].lower()

    def test_signup_increments_availability(self, client):
        """Test that available spots decrease after signup"""
        # Arrange
        activity_name = "Gym Class"
        email = "spottest@mergington.edu"
        
        activities_before = client.get("/activities").json()
        participants_before = len(activities_before[activity_name]["participants"])
        max_participants = activities_before[activity_name]["max_participants"]
        spots_before = max_participants - participants_before

        # Act
        client.post(f"/activities/{activity_name}/signup?email={email}")
        activities_after = client.get("/activities").json()
        participants_after = len(activities_after[activity_name]["participants"])
        spots_after = max_participants - participants_after

        # Assert
        assert participants_after == participants_before + 1
        assert spots_after == spots_before - 1


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants endpoint"""

    def test_remove_participant_success(self, client):
        """Test successfully removing a participant"""
        # Arrange
        activity_name = "Drama Club"
        email = "removeme@mergington.edu"
        client.post(f"/activities/{activity_name}/signup?email={email}")

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert "Removed" in response.json()["message"]

    def test_remove_participant_removes_from_list(self, client):
        """Test that remove actually takes participant off the list"""
        # Arrange
        activity_name = "Basketball Team"
        email = "removetest@mergington.edu"
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        activities_before_removal = client.get("/activities").json()
        assert email in activities_before_removal[activity_name]["participants"]

        # Act
        client.delete(f"/activities/{activity_name}/participants?email={email}")
        activities_after_removal = client.get("/activities").json()

        # Assert
        assert email not in activities_after_removal[activity_name]["participants"]

    def test_remove_nonexistent_activity_returns_404(self, client):
        """Test removing from a non-existent activity returns 404"""
        # Arrange
        fake_activity = "Nonexistent Activity"
        email = "test@example.com"

        # Act
        response = client.delete(
            f"/activities/{fake_activity}/participants?email={email}"
        )

        # Assert
        assert response.status_code == 404

    def test_remove_nonexistent_participant_returns_404(self, client):
        """Test removing a participant who isn't in the activity returns 404"""
        # Arrange
        activity_name = "Chess Club"
        email = "notinlist@example.com"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_remove_decrements_availability(self, client):
        """Test that available spots increase after removing a participant"""
        # Arrange
        activity_name = "Science Club"
        email = "removespot@mergington.edu"
        
        client.post(f"/activities/{activity_name}/signup?email={email}")
        activities_before_removal = client.get("/activities").json()
        participants_before = len(activities_before_removal[activity_name]["participants"])
        max_participants = activities_before_removal[activity_name]["max_participants"]
        spots_before = max_participants - participants_before

        # Act
        client.delete(f"/activities/{activity_name}/participants?email={email}")
        activities_after_removal = client.get("/activities").json()
        participants_after = len(activities_after_removal[activity_name]["participants"])
        spots_after = max_participants - participants_after

        # Assert
        assert participants_after == participants_before - 1
        assert spots_after == spots_before + 1


class TestRootEndpoint:
    """Tests for GET / endpoint"""

    def test_root_redirects(self, client):
        """Test that root endpoint redirects to /static/index.html"""
        # Arrange
        expected_redirect_url = "/static/index.html"

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == expected_redirect_url
