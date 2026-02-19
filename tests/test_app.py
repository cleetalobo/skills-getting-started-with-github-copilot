"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestGetActivities:
    """Test suite for GET /activities endpoint"""

    def test_get_activities_returns_200(self):
        """Test that GET /activities returns a 200 status code"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)

    def test_get_activities_contains_basketball_team(self):
        """Test that Basketball Team is in activities"""
        response = client.get("/activities")
        data = response.json()
        assert "Basketball Team" in data

    def test_activity_has_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, details in data.items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            assert isinstance(details["participants"], list)

    def test_activities_have_participants(self):
        """Test that activities have participant lists"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, details in data.items():
            assert len(details["participants"]) >= 0


class TestSignupEndpoint:
    """Test suite for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_valid_activity_and_email(self):
        """Test successful signup with valid activity and email"""
        response = client.post(
            "/activities/Basketball%20Team/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_adds_participant_to_activity(self):
        """Test that signup actually adds the participant"""
        email = "test_participant@mergington.edu"
        
        # Get initial participants count
        response = client.get("/activities")
        activities_before = response.json()
        initial_count = len(activities_before["Tennis Club"]["participants"])
        
        # Sign up
        signup_response = client.post(
            "/activities/Tennis%20Club/signup?email=" + email
        )
        assert signup_response.status_code == 200
        
        # Verify participant was added
        response = client.get("/activities")
        activities_after = response.json()
        final_count = len(activities_after["Tennis Club"]["participants"])
        assert final_count == initial_count + 1
        assert email in activities_after["Tennis Club"]["participants"]

    def test_signup_nonexistent_activity_returns_404(self):
        """Test that signup to nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_email_returns_400(self):
        """Test that duplicate signup returns 400"""
        # First signup
        client.post(
            "/activities/Drama%20Club/signup?email=duplicate@mergington.edu"
        )
        
        # Attempt duplicate signup
        response = client.post(
            "/activities/Drama%20Club/signup?email=duplicate@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_with_existing_participant(self):
        """Test that existing participants are in the system"""
        response = client.get("/activities")
        data = response.json()
        
        # Basketball Team should have at least one participant
        assert len(data["Basketball Team"]["participants"]) > 0
        assert "alex@mergington.edu" in data["Basketball Team"]["participants"]


class TestRootRedirect:
    """Test suite for root endpoint redirect"""

    def test_root_redirects_to_static_index(self):
        """Test that root path redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307


class TestIntegration:
    """Integration tests for the full application workflow"""

    def test_full_signup_workflow(self):
        """Test complete signup workflow"""
        # 1. Get activities
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        activity_name = "Chess Club"
        assert activity_name in activities
        
        # 2. Sign up for activity
        email = "integration_test@mergington.edu"
        signup_response = client.post(
            f"/activities/{activity_name.replace(' ', '%20')}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # 3. Verify signup by checking activities again
        response = client.get("/activities")
        updated_activities = response.json()
        assert email in updated_activities[activity_name]["participants"]

    def test_activity_availability_decreases_on_signup(self):
        """Test that available spots decrease when someone signs up"""
        response = client.get("/activities")
        data = response.json()
        activity = "Gym Class"
        initial_spots = data[activity]["max_participants"] - len(data[activity]["participants"])
        
        # Sign up
        email = "availability_test@mergington.edu"
        client.post(
            f"/activities/{activity.replace(' ', '%20')}/signup?email={email}"
        )
        
        # Check availability
        response = client.get("/activities")
        data = response.json()
        final_spots = data[activity]["max_participants"] - len(data[activity]["participants"])
        assert final_spots == initial_spots - 1
