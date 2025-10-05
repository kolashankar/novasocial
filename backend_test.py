#!/usr/bin/env python3
"""
Backend Testing for Phase 18 - Video Filters & AR Effects for Reels
Testing newly implemented reels endpoints with comprehensive scenarios
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
BACKEND_URL = "https://socialwave-mobile.preview.emergentagent.com/api"

# Test data for Phase 18 - Reels Testing
TEST_USER_DATA = {
    "fullName": "Reels Tester Phase18",
    "username": "reelstester_phase18",
    "email": "reelstester_phase18@example.com",
    "password": "ReelsTest123!"
}

# Sample base64 image for testing
SAMPLE_IMAGE_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.test_results = []
        
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
    
    def test_phase16_endpoints(self):
        """Test Phase 16 - Posting & Media Enhancements endpoints"""
        print("🚀 Testing Phase 16 - Posting & Media Enhancements Endpoints...")
        
        # 1. Test Tag Search API
        self.test_tag_search()
        
        # 2. Test Enhanced Post Creation
        post_id = self.test_enhanced_post_creation()
        
        # 3. Test Location-based Posts
        self.test_location_posts()
        
        # 4. Test Enhanced Story/Reel Creation
        story_id = self.test_enhanced_story_creation()
        
        # 5. Test Upload Progress Tracking
        self.test_upload_progress()
        
        # 6. Test Tag Validation & Privacy
        self.test_tag_validation_privacy()
    
    def test_tag_search(self):
        """Test tag search endpoints"""
        print("  Testing Tag Search API...")
        
        # Test user search
        try:
            response = self.session.get(f"{BACKEND_URL}/search/tags?q=john&type=users&limit=10")
            if response.status_code == 200:
                data = response.json()
                self.log_result("Tag Search - Users", True, f"Found {len(data.get('users', []))} users")
            else:
                self.log_result("Tag Search - Users", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Tag Search - Users", False, "", str(e))
        
        # Test location search
        try:
            response = self.session.get(f"{BACKEND_URL}/search/tags?q=park&type=locations&limit=10")
            if response.status_code == 200:
                data = response.json()
                self.log_result("Tag Search - Locations", True, f"Found {len(data.get('locations', []))} locations")
            else:
                self.log_result("Tag Search - Locations", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Tag Search - Locations", False, "", str(e))
        
        # Test combined search
        try:
            response = self.session.get(f"{BACKEND_URL}/search/tags?q=central")
            if response.status_code == 200:
                data = response.json()
                users_count = len(data.get('users', []))
                locations_count = len(data.get('locations', []))
                self.log_result("Tag Search - Combined", True, f"Found {users_count} users, {locations_count} locations")
            else:
                self.log_result("Tag Search - Combined", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Tag Search - Combined", False, "", str(e))
    
    def test_enhanced_post_creation(self):
        """Test enhanced post creation with tags and location"""
        print("  Testing Enhanced Post Creation...")
        
        post_data = {
            "caption": "Great day at the park!",
            "media": [SAMPLE_IMAGE_B64],
            "mediaTypes": ["image"],
            "taggedUsers": [{"userId": self.user_id, "position": {"x": 0.5, "y": 0.3}}],
            "location": {
                "id": "loc_1",
                "name": "Central Park",
                "coordinates": {"lat": 40.785091, "lng": -73.968285}
            }
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/posts/enhanced",
                json=post_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                post_id = data.get("id")
                self.log_result("Enhanced Post Creation", True, f"Post ID: {post_id}")
                return post_id
            else:
                self.log_result("Enhanced Post Creation", False, "", f"Status: {response.status_code}, Response: {response.text}")
                return None
        except Exception as e:
            self.log_result("Enhanced Post Creation", False, "", str(e))
            return None
    
    def test_location_posts(self):
        """Test location-based posts retrieval"""
        print("  Testing Location-based Posts...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/locations/loc_1/posts")
            if response.status_code == 200:
                data = response.json()
                self.log_result("Location Posts", True, f"Found {len(data)} posts at location")
            else:
                self.log_result("Location Posts", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Location Posts", False, "", str(e))
    
    def test_enhanced_story_creation(self):
        """Test enhanced story/reel creation"""
        print("  Testing Enhanced Story/Reel Creation...")
        
        story_data = {
            "contentType": "story",
            "media": SAMPLE_IMAGE_B64,
            "mediaType": "image",
            "text": "Test story",
            "effects": [{"type": "filter", "name": "vintage"}],
            "tags": [{"type": "location", "data": {"name": "Central Park"}}]
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/stories/enhanced",
                json=story_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                story_id = data.get("id")
                self.log_result("Enhanced Story Creation", True, f"Story ID: {story_id}")
                return story_id
            else:
                self.log_result("Enhanced Story Creation", False, "", f"Status: {response.status_code}, Response: {response.text}")
                return None
        except Exception as e:
            self.log_result("Enhanced Story Creation", False, "", str(e))
            return None
    
    def test_upload_progress(self):
        """Test upload progress tracking"""
        print("  Testing Upload Progress Tracking...")
        
        # Test upload progress check
        upload_id = str(uuid.uuid4())
        try:
            response = self.session.get(f"{BACKEND_URL}/upload/progress/{upload_id}")
            if response.status_code in [200, 404]:  # 404 is expected for non-existent upload
                if response.status_code == 200:
                    data = response.json()
                    self.log_result("Upload Progress Check", True, f"Progress: {data.get('progress', 0)}%")
                else:
                    self.log_result("Upload Progress Check", True, "Upload not found (expected)")
            else:
                self.log_result("Upload Progress Check", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Upload Progress Check", False, "", str(e))
        
        # Test upload retry
        try:
            response = self.session.post(f"{BACKEND_URL}/upload/retry/{upload_id}")
            if response.status_code in [200, 404]:  # 404 is expected for non-existent upload
                self.log_result("Upload Retry", True, "Retry endpoint accessible")
            else:
                self.log_result("Upload Retry", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Upload Retry", False, "", str(e))
    
    def test_tag_validation_privacy(self):
        """Test tag validation and privacy checks"""
        print("  Testing Tag Validation & Privacy...")
        
        # Test tag validation
        validation_data = {
            "postId": str(uuid.uuid4()),
            "taggedUserIds": [self.user_id],
            "locationId": "loc_1"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/posts/validate-tags",
                json=validation_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Tag Validation", True, f"Valid: {data.get('isValid', False)}")
            else:
                self.log_result("Tag Validation", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Tag Validation", False, "", str(e))
        
        # Test privacy check
        privacy_data = {
            "userId": self.user_id,
            "targetUserId": self.user_id,
            "action": "tag"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/privacy/check",
                json=privacy_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Privacy Check", True, f"Allowed: {data.get('isAllowed', False)}")
            else:
                self.log_result("Privacy Check", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Privacy Check", False, "", str(e))
    
    def test_phase17_endpoints(self):
        """Test Phase 17 - Story & Creative Tools endpoints"""
        print("🎨 Testing Phase 17 - Story & Creative Tools Endpoints...")
        
        # Create a test story first
        story_id = self.create_test_story()
        
        if story_id:
            # 1. Test Story Stickers Management
            self.test_story_stickers(story_id)
            
            # 2. Test Interactive Elements
            self.test_interactive_elements(story_id)
        
        # 3. Test Creative Libraries
        self.test_creative_libraries()
        
        # 4. Test Collaborative Prompts
        self.test_collaborative_prompts()
        
        # 5. Test Story Analytics
        if story_id:
            self.test_story_analytics(story_id)
    
    def create_test_story(self):
        """Create a test story for Phase 17 testing"""
        story_data = {
            "media": SAMPLE_IMAGE_B64,
            "mediaType": "image",
            "text": "Test story for Phase 17"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/stories",
                json=story_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                story_id = data.get("id")
                self.log_result("Test Story Creation", True, f"Story ID: {story_id}")
                return story_id
            else:
                self.log_result("Test Story Creation", False, "", f"Status: {response.status_code}")
                return None
        except Exception as e:
            self.log_result("Test Story Creation", False, "", str(e))
            return None
    
    def test_story_stickers(self, story_id):
        """Test story stickers management"""
        print("  Testing Story Stickers Management...")
        
        # Test adding sticker
        sticker_data = {
            "type": "location",
            "data": {"name": "Central Park", "coordinates": {"lat": 40.785091, "lng": -73.968285}},
            "position": {"x": 0.5, "y": 0.3, "rotation": 0, "scale": 1.0},
            "zIndex": 1
        }
        
        sticker_id = None
        try:
            response = self.session.post(
                f"{BACKEND_URL}/stories/{story_id}/stickers",
                json=sticker_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                sticker_id = data.get("id")
                self.log_result("Add Story Sticker", True, f"Sticker ID: {sticker_id}")
            else:
                self.log_result("Add Story Sticker", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Add Story Sticker", False, "", str(e))
        
        # Test getting stickers
        try:
            response = self.session.get(f"{BACKEND_URL}/stories/{story_id}/stickers")
            if response.status_code == 200:
                data = response.json()
                self.log_result("Get Story Stickers", True, f"Found {len(data)} stickers")
            else:
                self.log_result("Get Story Stickers", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Get Story Stickers", False, "", str(e))
        
        # Test updating sticker (if we have a sticker_id)
        if sticker_id:
            update_data = {
                "position": {"x": 0.6, "y": 0.4, "rotation": 15, "scale": 1.2}
            }
            
            try:
                response = self.session.put(
                    f"{BACKEND_URL}/stories/stickers/{sticker_id}",
                    json=update_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    self.log_result("Update Story Sticker", True, "Sticker updated successfully")
                else:
                    self.log_result("Update Story Sticker", False, "", f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("Update Story Sticker", False, "", str(e))
            
            # Test deleting sticker
            try:
                response = self.session.delete(f"{BACKEND_URL}/stories/stickers/{sticker_id}")
                if response.status_code in [200, 204]:
                    self.log_result("Delete Story Sticker", True, "Sticker deleted successfully")
                else:
                    self.log_result("Delete Story Sticker", False, "", f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("Delete Story Sticker", False, "", str(e))
    
    def test_creative_libraries(self):
        """Test creative libraries endpoints"""
        print("  Testing Creative Libraries...")
        
        # Test music library
        try:
            response = self.session.get(f"{BACKEND_URL}/creative/music")
            if response.status_code == 200:
                data = response.json()
                self.log_result("Music Library", True, f"Found {len(data)} music items")
            else:
                self.log_result("Music Library", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Music Library", False, "", str(e))
        
        # Test music search
        try:
            response = self.session.get(f"{BACKEND_URL}/creative/music?category=trending&search=upbeat")
            if response.status_code == 200:
                data = response.json()
                self.log_result("Music Search", True, f"Found {len(data)} matching items")
            else:
                self.log_result("Music Search", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Music Search", False, "", str(e))
        
        # Test GIF library
        try:
            response = self.session.get(f"{BACKEND_URL}/creative/gifs")
            if response.status_code == 200:
                data = response.json()
                self.log_result("GIF Library", True, f"Found {len(data)} GIF items")
            else:
                self.log_result("GIF Library", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("GIF Library", False, "", str(e))
        
        # Test GIF search
        try:
            response = self.session.get(f"{BACKEND_URL}/creative/gifs?search=happy")
            if response.status_code == 200:
                data = response.json()
                self.log_result("GIF Search", True, f"Found {len(data)} matching GIFs")
            else:
                self.log_result("GIF Search", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("GIF Search", False, "", str(e))
        
        # Test frames library
        try:
            response = self.session.get(f"{BACKEND_URL}/creative/frames")
            if response.status_code == 200:
                data = response.json()
                self.log_result("Frames Library", True, f"Found {len(data)} frame templates")
            else:
                self.log_result("Frames Library", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Frames Library", False, "", str(e))
        
        # Test colors library
        try:
            response = self.session.get(f"{BACKEND_URL}/creative/colors")
            if response.status_code == 200:
                data = response.json()
                self.log_result("Colors Library", True, f"Found {len(data)} color palettes")
            else:
                self.log_result("Colors Library", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Colors Library", False, "", str(e))
    
    def test_interactive_elements(self, story_id):
        """Test interactive elements"""
        print("  Testing Interactive Elements...")
        
        # Test adding interactive element (poll)
        element_data = {
            "type": "poll",
            "question": "What's your favorite color?",
            "options": ["Red", "Blue", "Green", "Yellow"]
        }
        
        element_id = None
        try:
            response = self.session.post(
                f"{BACKEND_URL}/stories/{story_id}/interactive",
                json=element_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                element_id = data.get("id")
                self.log_result("Add Interactive Element", True, f"Element ID: {element_id}")
            else:
                self.log_result("Add Interactive Element", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Add Interactive Element", False, "", str(e))
        
        # Test responding to interactive element
        if element_id:
            response_data = {
                "response": {"selectedOption": 1, "optionText": "Blue"}
            }
            
            try:
                response = self.session.post(
                    f"{BACKEND_URL}/interactive/{element_id}/respond",
                    json=response_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    self.log_result("Respond to Interactive Element", True, "Response recorded")
                else:
                    self.log_result("Respond to Interactive Element", False, "", f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("Respond to Interactive Element", False, "", str(e))
            
            # Test getting interactive results
            try:
                response = self.session.get(f"{BACKEND_URL}/interactive/{element_id}/results")
                if response.status_code == 200:
                    data = response.json()
                    self.log_result("Get Interactive Results", True, f"Total responses: {len(data.get('responses', []))}")
                else:
                    self.log_result("Get Interactive Results", False, "", f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("Get Interactive Results", False, "", str(e))
    
    def test_collaborative_prompts(self):
        """Test collaborative prompts"""
        print("  Testing Collaborative Prompts...")
        
        # Test creating collaborative prompt
        prompt_data = {
            "promptText": "Show me your morning routine!",
            "category": "lifestyle",
            "tags": ["morning", "routine", "lifestyle"]
        }
        
        prompt_id = None
        try:
            response = self.session.post(
                f"{BACKEND_URL}/collaborative/prompts",
                json=prompt_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                prompt_id = data.get("id")
                self.log_result("Create Collaborative Prompt", True, f"Prompt ID: {prompt_id}")
            else:
                self.log_result("Create Collaborative Prompt", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Create Collaborative Prompt", False, "", str(e))
        
        # Test participating in prompt
        if prompt_id:
            participation_data = {
                "response": {
                    "media": SAMPLE_IMAGE_B64,
                    "text": "My morning routine includes coffee and stretching!"
                }
            }
            
            try:
                response = self.session.post(
                    f"{BACKEND_URL}/collaborative/prompts/{prompt_id}/participate",
                    json=participation_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    self.log_result("Participate in Prompt", True, "Participation recorded")
                else:
                    self.log_result("Participate in Prompt", False, "", f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("Participate in Prompt", False, "", str(e))
        
        # Test getting trending prompts
        try:
            response = self.session.get(f"{BACKEND_URL}/collaborative/prompts/trending")
            if response.status_code == 200:
                data = response.json()
                self.log_result("Get Trending Prompts", True, f"Found {len(data)} trending prompts")
            else:
                self.log_result("Get Trending Prompts", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Get Trending Prompts", False, "", str(e))
    
    def test_story_analytics(self, story_id):
        """Test story analytics"""
        print("  Testing Story Analytics...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/stories/{story_id}/analytics")
            if response.status_code == 200:
                data = response.json()
                views = data.get("views", 0)
                self.log_result("Story Analytics", True, f"Views: {views}, Engagement: {data.get('engagement', {})}")
            else:
                self.log_result("Story Analytics", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Story Analytics", False, "", str(e))
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("📊 TEST SUMMARY")
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
        
        print("\n" + "="*80)
        
        return passed_tests, failed_tests

def main():
    """Main test execution"""
    print("🧪 Starting Backend Testing for Phase 16 & 17")
    print("="*80)
    
    tester = BackendTester()
    
    # Setup authentication
    if not tester.setup_auth():
        print("❌ Authentication setup failed. Cannot proceed with tests.")
        return
    
    # Run Phase 16 tests
    tester.test_phase16_endpoints()
    
    # Run Phase 17 tests
    tester.test_phase17_endpoints()
    
    # Print summary
    passed, failed = tester.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()