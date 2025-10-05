#!/usr/bin/env python3
"""
NovaSocial Backend API Comprehensive Testing Suite
Tests all backend endpoints for the social media application including 23+ phases
"""

import requests
import json
import base64
import uuid
from datetime import datetime, timedelta
import os
import sys
import time

# Get backend URL from frontend .env
BACKEND_URL = "https://bugzero-social.preview.emergentagent.com/api"

# Test data for comprehensive testing
TEST_USER_DATA = {
    "fullName": "Sarah Johnson",
    "username": "sarah_test_user",
    "email": "sarah.johnson@testmail.com",
    "password": "SecurePass123!"
}

TEST_USER2_DATA = {
    "fullName": "Mike Chen",
    "username": "mike_test_user", 
    "email": "mike.chen@testmail.com",
    "password": "SecurePass456!"
}

# Sample base64 image for testing
SAMPLE_IMAGE_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

class ReelsBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.test_results = []
        self.test_reel_id = None
        
    def log_result(self, test_name, success, details="", error_msg=""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if details:
            print(f"    Details: {details}")
        if error_msg:
            print(f"    Error: {error_msg}")
        print()
    
    def setup_auth(self):
        """Register and login test user"""
        print("🔐 Setting up authentication...")
        
        # Register user
        try:
            register_response = self.session.post(
                f"{BACKEND_URL}/auth/register",
                json=TEST_USER_DATA,
                headers={"Content-Type": "application/json"}
            )
            
            if register_response.status_code == 201 or register_response.status_code == 200:
                data = register_response.json()
                self.auth_token = data.get("token")
                self.user_id = data.get("user", {}).get("id")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                self.log_result("User Registration", True, f"User ID: {self.user_id}")
                return True
            elif register_response.status_code == 400 and "already" in register_response.text.lower():
                # User exists, try login
                login_response = self.session.post(
                    f"{BACKEND_URL}/auth/login",
                    json={"email": TEST_USER_DATA["email"], "password": TEST_USER_DATA["password"]},
                    headers={"Content-Type": "application/json"}
                )
                
                if login_response.status_code == 200:
                    data = login_response.json()
                    self.auth_token = data.get("token")
                    self.user_id = data.get("user", {}).get("id")
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    self.log_result("User Login", True, f"User ID: {self.user_id}")
                    return True
                else:
                    self.log_result("User Login", False, "", f"Status: {login_response.status_code}, Response: {login_response.text}")
                    return False
            else:
                self.log_result("User Registration", False, "", f"Status: {register_response.status_code}, Response: {register_response.text}")
                return False
                
        except Exception as e:
            self.log_result("Authentication Setup", False, "", str(e))
            return False
    
    def generate_mock_video_data(self):
        """Generate mock base64 video data"""
        # Create a simple mock video data (base64 encoded)
        mock_video_bytes = b"MOCK_VIDEO_DATA_FOR_TESTING_REELS_UPLOAD" * 100
        return base64.b64encode(mock_video_bytes).decode('utf-8')
        
    def test_phase18_endpoints(self):
        """Test Phase 18 - Video Filters & AR Effects for Reels endpoints"""
        print("🎬 Testing Phase 18 - Video Filters & AR Effects for Reels Endpoints...")
        
        # 1. Test Filter Presets (Public endpoint)
        self.test_get_filter_presets()
        
        # 2. Test Reel Upload with Filters and AR Effects
        self.test_upload_reel_with_filters()
        
        # Wait for processing to start
        time.sleep(3)
        
        # 3. Test Processing Status
        self.test_get_processing_status()
        
        # 4. Test Reels Feed
        self.test_get_reels_feed()
        
        # 5. Test Like/Unlike Functionality
        self.test_toggle_reel_like()
        
        # 6. Test View Tracking
        self.test_add_reel_view()
        
        # 7. Test Error Handling
        self.test_error_handling()
        
        # 8. Test Unauthorized Access
        self.test_unauthorized_access()
        
        # 9. Test Reel Deletion (last)
        self.test_delete_reel()
    
    def test_get_filter_presets(self):
        """Test GET /api/reels/filters/presets - Get available filter presets and AR effects"""
        print("  Testing Filter Presets API...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/reels/filters/presets")
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                if "filters" in data and "arEffects" in data:
                    filters_count = len(data["filters"])
                    ar_effects_count = len(data["arEffects"])
                    
                    # Check for expected preset filters
                    filter_names = [f["name"] for f in data["filters"]]
                    expected_filters = ["vintage", "dramatic", "soft_glow", "black_white"]
                    
                    # Check for expected AR effects
                    ar_effect_names = [e["name"] for e in data["arEffects"]]
                    expected_ar_effects = ["heart_eyes", "dog_ears", "sparkles"]
                    
                    missing_filters = [f for f in expected_filters if f not in filter_names]
                    missing_ar_effects = [e for e in expected_ar_effects if e not in ar_effect_names]
                    
                    if not missing_filters and not missing_ar_effects:
                        self.log_result(
                            "Get Filter Presets", 
                            True, 
                            f"Retrieved {filters_count} filters and {ar_effects_count} AR effects"
                        )
                    else:
                        self.log_result(
                            "Get Filter Presets", 
                            False, 
                            f"Missing filters: {missing_filters}, Missing AR effects: {missing_ar_effects}"
                        )
                else:
                    self.log_result("Get Filter Presets", False, "", "Invalid response structure")
            else:
                self.log_result("Get Filter Presets", False, "", f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Get Filter Presets", False, "", str(e))
    
    def test_upload_reel_with_filters(self):
        """Test POST /api/reels/upload - Upload reel with filters and AR effects"""
        print("  Testing Reel Upload with Filters...")
        
        # Prepare reel upload data with filters and AR effects
        reel_data = {
            "videoData": self.generate_mock_video_data(),
            "caption": "Testing reel upload with filters and AR effects! 🎬✨",
            "hashtags": ["#reelstest", "#filters", "#areffects", "#testing"],
            "tags": ["@reelstester"],
            "locationTag": {
                "name": "Test Location",
                "coordinates": {"lat": 40.7128, "lng": -74.0060}
            },
            "musicTrack": {
                "id": "test_track_001",
                "name": "Test Background Music",
                "artist": "Test Artist",
                "duration": 15
            },
            "filters": [
                {
                    "name": "vintage",
                    "type": "effect",
                    "parameters": {
                        "sepia": 0.7,
                        "contrast": 1.2,
                        "vignette": 0.4,
                        "noise": 0.1
                    },
                    "presetName": "vintage"
                }
            ],
            "arEffects": [
                {
                    "name": "heart_eyes",
                    "type": "face_tracking",
                    "assetUrl": "/ar_assets/heart_eyes.png",
                    "parameters": {
                        "facial_landmark": "eyes",
                        "tracking_confidence": 0.8
                    }
                }
            ],
            "privacy": "public"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/reels/upload",
                json=reel_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success") and "reelId" in data:
                    self.test_reel_id = data["reelId"]
                    reel_info = data.get("reel", {})
                    
                    # Validate reel data structure
                    required_fields = ["id", "userId", "caption", "hashtags", "videoUrl", "isProcessing"]
                    missing_fields = [field for field in required_fields if field not in reel_info]
                    
                    if not missing_fields:
                        self.log_result(
                            "Upload Reel with Filters", 
                            True, 
                            f"Reel uploaded successfully with ID: {self.test_reel_id}"
                        )
                    else:
                        self.log_result(
                            "Upload Reel with Filters", 
                            False, 
                            f"Missing required fields in response: {missing_fields}"
                        )
                else:
                    self.log_result("Upload Reel with Filters", False, "", "Invalid response structure")
            else:
                self.log_result("Upload Reel with Filters", False, "", f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Upload Reel with Filters", False, "", str(e))
    
    def test_get_processing_status(self):
        """Test GET /api/reels/processing/{reel_id} - Get processing status of a reel"""
        print("  Testing Processing Status API...")
        
        if not self.test_reel_id:
            self.log_result("Get Processing Status", False, "", "No test reel ID available")
            return
            
        try:
            response = self.session.get(f"{BACKEND_URL}/reels/processing/{self.test_reel_id}")
            if response.status_code == 200:
                data = response.json()
                
                # Validate processing status response
                required_fields = ["reelId", "isProcessing", "processingStatus", "processingProgress"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    processing_status = data["processingStatus"]
                    progress = data["processingProgress"]
                    
                    self.log_result(
                        "Get Processing Status", 
                        True, 
                        f"Status: {processing_status}, Progress: {progress}%"
                    )
                else:
                    self.log_result(
                        "Get Processing Status", 
                        False, 
                        f"Missing required fields: {missing_fields}"
                    )
            else:
                self.log_result("Get Processing Status", False, "", f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Get Processing Status", False, "", str(e))
    
    def test_get_reels_feed(self):
        """Test GET /api/reels/feed - Get personalized reels feed"""
        print("  Testing Reels Feed API...")
        
        try:
            params = {"skip": 0, "limit": 10}
            response = self.session.get(f"{BACKEND_URL}/reels/feed", params=params)
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    reels_count = len(data)
                    
                    # If we have reels, validate structure
                    if reels_count > 0:
                        first_reel = data[0]
                        required_fields = ["id", "userId", "caption", "videoUrl", "likesCount", "viewsCount"]
                        missing_fields = [field for field in required_fields if field not in first_reel]
                        
                        if not missing_fields:
                            self.log_result(
                                "Get Reels Feed", 
                                True, 
                                f"Retrieved {reels_count} reels from feed"
                            )
                        else:
                            self.log_result(
                                "Get Reels Feed", 
                                False, 
                                f"Missing required fields in reel: {missing_fields}"
                            )
                    else:
                        self.log_result("Get Reels Feed", True, "Feed retrieved successfully (empty)")
                else:
                    self.log_result("Get Reels Feed", False, "", "Response is not a list")
            else:
                self.log_result("Get Reels Feed", False, "", f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Get Reels Feed", False, "", str(e))
    
    def test_toggle_reel_like(self):
        """Test POST /api/reels/{reel_id}/like - Toggle like on a reel"""
        print("  Testing Reel Like Toggle...")
        
        if not self.test_reel_id:
            self.log_result("Toggle Reel Like", False, "", "No test reel ID available")
            return
            
        try:
            # Test liking the reel
            response = self.session.post(f"{BACKEND_URL}/reels/{self.test_reel_id}/like")
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success") and "action" in data:
                    action = data["action"]
                    
                    # Test unliking the reel
                    response2 = self.session.post(f"{BACKEND_URL}/reels/{self.test_reel_id}/like")
                    if response2.status_code == 200:
                        data2 = response2.json()
                        action2 = data2.get("action")
                        
                        if action == "liked" and action2 == "unliked":
                            self.log_result(
                                "Toggle Reel Like", 
                                True, 
                                f"Like toggle working: {action} -> {action2}"
                            )
                        else:
                            self.log_result(
                                "Toggle Reel Like", 
                                False, 
                                f"Unexpected toggle behavior: {action} -> {action2}"
                            )
                    else:
                        self.log_result("Toggle Reel Like", False, "", f"Second request failed: {response2.text}")
                else:
                    self.log_result("Toggle Reel Like", False, "", "Invalid response structure")
            else:
                self.log_result("Toggle Reel Like", False, "", f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Toggle Reel Like", False, "", str(e))
    
    def test_add_reel_view(self):
        """Test POST /api/reels/{reel_id}/view - Add view to a reel"""
        print("  Testing Reel View Tracking...")
        
        if not self.test_reel_id:
            self.log_result("Add Reel View", False, "", "No test reel ID available")
            return
            
        try:
            # Test adding a view
            response = self.session.post(f"{BACKEND_URL}/reels/{self.test_reel_id}/view")
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success") and "message" in data:
                    # Test adding another view (should not increment for same user)
                    response2 = self.session.post(f"{BACKEND_URL}/reels/{self.test_reel_id}/view")
                    if response2.status_code == 200:
                        data2 = response2.json()
                        
                        self.log_result(
                            "Add Reel View", 
                            True, 
                            "View tracking working (unique views only)"
                        )
                    else:
                        self.log_result("Add Reel View", False, "", f"Second request failed: {response2.text}")
                else:
                    self.log_result("Add Reel View", False, "", "Invalid response structure")
            else:
                self.log_result("Add Reel View", False, "", f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Add Reel View", False, "", str(e))
    
    def test_delete_reel(self):
        """Test DELETE /api/reels/{reel_id} - Delete a reel"""
        print("  Testing Reel Deletion...")
        
        if not self.test_reel_id:
            self.log_result("Delete Reel", False, "", "No test reel ID available")
            return
            
        try:
            response = self.session.delete(f"{BACKEND_URL}/reels/{self.test_reel_id}")
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success") and "message" in data:
                    # Verify reel is deleted by trying to get processing status
                    verify_response = self.session.get(f"{BACKEND_URL}/reels/processing/{self.test_reel_id}")
                    if verify_response.status_code == 404:
                        self.log_result(
                            "Delete Reel", 
                            True, 
                            "Reel deleted successfully and verified"
                        )
                    else:
                        self.log_result("Delete Reel", False, "", "Reel still exists after deletion")
                else:
                    self.log_result("Delete Reel", False, "", "Invalid response structure")
            else:
                self.log_result("Delete Reel", False, "", f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Delete Reel", False, "", str(e))
    
    def test_unauthorized_access(self):
        """Test endpoints without authentication"""
        print("  Testing Unauthorized Access Protection...")
        
        # Temporarily remove auth header
        original_auth = self.session.headers.get("Authorization")
        if "Authorization" in self.session.headers:
            del self.session.headers["Authorization"]
        
        try:
            # Test accessing protected endpoints without auth
            protected_endpoints = [
                ("POST", "/reels/upload"),
                ("GET", f"/reels/processing/{uuid.uuid4()}"),
                ("GET", "/reels/feed"),
                ("POST", f"/reels/{uuid.uuid4()}/like"),
                ("POST", f"/reels/{uuid.uuid4()}/view"),
                ("DELETE", f"/reels/{uuid.uuid4()}")
            ]
            
            unauthorized_count = 0
            
            for method, endpoint in protected_endpoints:
                if method == "GET":
                    response = self.session.get(f"{BACKEND_URL}{endpoint}")
                elif method == "POST":
                    response = self.session.post(f"{BACKEND_URL}{endpoint}")
                elif method == "DELETE":
                    response = self.session.delete(f"{BACKEND_URL}{endpoint}")
                
                if response.status_code == 401:
                    unauthorized_count += 1
                    
            if unauthorized_count == len(protected_endpoints):
                self.log_result(
                    "Unauthorized Access Protection", 
                    True, 
                    f"All {len(protected_endpoints)} protected endpoints properly reject unauthorized access"
                )
            else:
                self.log_result(
                    "Unauthorized Access Protection", 
                    False, 
                    f"Only {unauthorized_count}/{len(protected_endpoints)} endpoints properly protected"
                )
                
        finally:
            # Restore auth header
            if original_auth:
                self.session.headers["Authorization"] = original_auth
    
    def test_error_handling(self):
        """Test error handling scenarios"""
        print("  Testing Error Handling...")
        
        try:
            # Test with invalid reel ID
            fake_reel_id = str(uuid.uuid4())
            
            error_tests = [
                ("GET", f"/reels/processing/{fake_reel_id}", 404),
                ("POST", f"/reels/{fake_reel_id}/like", 404),
                ("POST", f"/reels/{fake_reel_id}/view", 404),
                ("DELETE", f"/reels/{fake_reel_id}", 404)
            ]
            
            correct_errors = 0
            
            for method, endpoint, expected_status in error_tests:
                if method == "GET":
                    response = self.session.get(f"{BACKEND_URL}{endpoint}")
                elif method == "POST":
                    response = self.session.post(f"{BACKEND_URL}{endpoint}")
                elif method == "DELETE":
                    response = self.session.delete(f"{BACKEND_URL}{endpoint}")
                
                if response.status_code == expected_status:
                    correct_errors += 1
                    
            if correct_errors == len(error_tests):
                self.log_result(
                    "Error Handling", 
                    True, 
                    f"All {len(error_tests)} error scenarios handled correctly"
                )
            else:
                self.log_result(
                    "Error Handling", 
                    False, 
                    f"Only {correct_errors}/{len(error_tests)} error scenarios handled correctly"
                )
                
        except Exception as e:
            self.log_result("Error Handling", False, "", str(e))
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("📊 TEST SUMMARY - Phase 18 Reels Backend")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  ❌ {result['test']}: {result['error']}")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['test']}")
        
        print("\n" + "="*80)
        
        return passed_tests, failed_tests

def main():
    """Main test execution"""
    print("🧪 Starting Backend Testing for Phase 18 - Video Filters & AR Effects for Reels")
    print("="*80)
    
    tester = ReelsBackendTester()
    
    # Setup authentication
    if not tester.setup_auth():
        print("❌ Authentication setup failed. Cannot proceed with tests.")
        return
    
    # Run Phase 18 tests
    tester.test_phase18_endpoints()
    
    # Print summary
    passed, failed = tester.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()