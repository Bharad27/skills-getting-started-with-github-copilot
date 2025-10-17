"""
Tests for the Mergington High School Activities API
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


class TestActivitiesAPI:
    """Test cases for the Activities API endpoints"""

    def test_root_redirect(self, client, reset_activities):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/")
        assert response.status_code == 200
        # Should redirect to static files
        assert "text/html" in response.headers.get("content-type", "")

    def test_get_activities(self, client, reset_activities):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        
        # Check structure of an activity
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)

    def test_signup_for_activity_success(self, client, reset_activities):
        """Test successful signup for an activity"""
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == f"Signed up {email} for {activity}"
        
        # Verify the participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity]["participants"]

    def test_signup_for_nonexistent_activity(self, client, reset_activities):
        """Test signup for an activity that doesn't exist"""
        email = "student@mergington.edu"
        activity = "Nonexistent Activity"
        
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 404
        
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_signup_duplicate_registration(self, client, reset_activities):
        """Test that duplicate registration is prevented"""
        email = "michael@mergington.edu"  # Already registered in Chess Club
        activity = "Chess Club"
        
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 400
        
        data = response.json()
        assert data["detail"] == "Student is already signed up for this activity"

    def test_unregister_from_activity_success(self, client, reset_activities):
        """Test successful unregistration from an activity"""
        email = "michael@mergington.edu"  # Pre-registered in Chess Club
        activity = "Chess Club"
        
        # Verify the participant is initially registered
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity]["participants"]
        
        # Unregister the participant
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == f"Unregistered {email} from {activity}"
        
        # Verify the participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data[activity]["participants"]

    def test_unregister_from_nonexistent_activity(self, client, reset_activities):
        """Test unregistering from an activity that doesn't exist"""
        email = "student@mergington.edu"
        activity = "Nonexistent Activity"
        
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 404
        
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_unregister_not_registered_participant(self, client, reset_activities):
        """Test unregistering a participant who is not registered"""
        email = "notregistered@mergington.edu"
        activity = "Chess Club"
        
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 400
        
        data = response.json()
        assert data["detail"] == "Student is not registered for this activity"

    def test_signup_and_unregister_workflow(self, client, reset_activities):
        """Test complete workflow: signup then unregister"""
        email = "workflow@mergington.edu"
        activity = "Programming Class"
        
        # Step 1: Sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Verify signup
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity]["participants"]
        
        # Step 2: Unregister
        unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert unregister_response.status_code == 200
        
        # Verify unregistration
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data[activity]["participants"]

    def test_multiple_activities_signup(self, client, reset_activities):
        """Test signing up for multiple activities"""
        email = "multisport@mergington.edu"
        activities_list = ["Chess Club", "Programming Class", "Basketball Team"]
        
        # Sign up for multiple activities
        for activity in activities_list:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify participant is in all activities
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        
        for activity in activities_list:
            assert email in activities_data[activity]["participants"]

    def test_activity_capacity_tracking(self, client, reset_activities):
        """Test that participant counts are properly tracked"""
        activity = "Chess Club"
        
        # Get initial state
        response = client.get("/activities")
        initial_data = response.json()
        initial_count = len(initial_data[activity]["participants"])
        max_participants = initial_data[activity]["max_participants"]
        
        # Add a new participant
        new_email = "capacity@mergington.edu"
        signup_response = client.post(f"/activities/{activity}/signup?email={new_email}")
        assert signup_response.status_code == 200
        
        # Verify count increased
        response = client.get("/activities")
        updated_data = response.json()
        updated_count = len(updated_data[activity]["participants"])
        
        assert updated_count == initial_count + 1
        assert updated_count <= max_participants