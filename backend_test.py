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

class NovaSocialAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.user2_token = None
        self.user2_id = None
        self.test_results = []
        self.test_post_id = None
        self.test_story_id = None
        self.test_conversation_id = None
        
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
        """Register and login test users"""
        print("🔐 Setting up authentication...")
        
        # Register first user
        try:
            register_response = self.session.post(
                f"{BACKEND_URL}/auth/register",
                json=TEST_USER_DATA,
                headers={"Content-Type": "application/json"}
            )
            
            if register_response.status_code in [200, 201]:
                data = register_response.json()
                self.auth_token = data.get("token")
                self.user_id = data.get("user", {}).get("id")
                self.log_result("User 1 Registration", True, f"User ID: {self.user_id}")
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
                    self.log_result("User 1 Login", True, f"User ID: {self.user_id}")
                else:
                    self.log_result("User 1 Login", False, "", f"Status: {login_response.status_code}")
                    return False
            else:
                self.log_result("User 1 Registration", False, "", f"Status: {register_response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("User 1 Auth Setup", False, "", str(e))
            return False
        
        # Register second user
        try:
            register_response = self.session.post(
                f"{BACKEND_URL}/auth/register",
                json=TEST_USER2_DATA,
                headers={"Content-Type": "application/json"}
            )
            
            if register_response.status_code in [200, 201]:
                data = register_response.json()
                self.user2_token = data.get("token")
                self.user2_id = data.get("user", {}).get("id")
                self.log_result("User 2 Registration", True, f"User ID: {self.user2_id}")
            elif register_response.status_code == 400 and "already" in register_response.text.lower():
                # User exists, try login
                login_response = self.session.post(
                    f"{BACKEND_URL}/auth/login",
                    json={"email": TEST_USER2_DATA["email"], "password": TEST_USER2_DATA["password"]},
                    headers={"Content-Type": "application/json"}
                )
                
                if login_response.status_code == 200:
                    data = login_response.json()
                    self.user2_token = data.get("token")
                    self.user2_id = data.get("user", {}).get("id")
                    self.log_result("User 2 Login", True, f"User ID: {self.user2_id}")
                else:
                    self.log_result("User 2 Login", False, "", f"Status: {login_response.status_code}")
            else:
                self.log_result("User 2 Registration", False, "", f"Status: {register_response.status_code}")
                
        except Exception as e:
            self.log_result("User 2 Auth Setup", False, "", str(e))
        
        return self.auth_token is not None
    
    def make_request(self, method, endpoint, data=None, use_user2=False):
        """Make authenticated request"""
        headers = {"Content-Type": "application/json"}
        if use_user2 and self.user2_token:
            headers["Authorization"] = f"Bearer {self.user2_token}"
        elif self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        url = f"{BACKEND_URL}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers, timeout=30)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, headers=headers, timeout=30)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, headers=headers, timeout=30)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed for {method} {url}: {str(e)}")
            raise
    
    def test_authentication_endpoints(self):
        """Test authentication endpoints"""
        print("\n🔐 TESTING AUTHENTICATION ENDPOINTS")
        
        # Test get current user profile
        try:
            response = self.make_request("GET", "/auth/me")
            if response.status_code == 200:
                data = response.json()
                if "id" in data and "email" in data:
                    self.log_result("Get Current User Profile", True, f"Profile retrieved for: {data.get('username')}")
                else:
                    self.log_result("Get Current User Profile", False, "Missing required fields", str(data))
            else:
                self.log_result("Get Current User Profile", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Get Current User Profile", False, "", str(e))
        
        # Test profile update
        try:
            profile_data = {
                "profileImage": SAMPLE_IMAGE_B64,
                "bio": "Testing user profile update functionality"
            }
            response = self.make_request("PUT", "/auth/profile", profile_data)
            if response.status_code == 200:
                data = response.json()
                if data.get("bio") == profile_data["bio"]:
                    self.log_result("Profile Update", True, "Profile updated successfully")
                else:
                    self.log_result("Profile Update", False, "Profile not updated correctly")
            else:
                self.log_result("Profile Update", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Profile Update", False, "", str(e))
    
    def test_post_endpoints(self):
        """Test post creation and feed endpoints"""
        print("\n📝 TESTING POST ENDPOINTS")
        
        # Test post creation
        try:
            post_data = {
                "caption": "Testing post creation with beautiful sunset photo! #sunset #photography #test",
                "media": [SAMPLE_IMAGE_B64],
                "mediaTypes": ["image"],
                "hashtags": ["sunset", "photography", "test"],
                "taggedUsers": []
            }
            response = self.make_request("POST", "/posts", post_data)
            if response.status_code in [200, 201]:
                data = response.json()
                if "id" in data and "caption" in data:
                    self.test_post_id = data["id"]
                    self.log_result("Post Creation", True, f"Post created with ID: {self.test_post_id}")
                else:
                    self.log_result("Post Creation", False, "Missing required fields")
            else:
                self.log_result("Post Creation", False, "", f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Post Creation", False, "", str(e))
        
        # Test get feed
        try:
            response = self.make_request("GET", "/posts/feed?limit=10")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("Get Posts Feed", True, f"Feed retrieved with {len(data)} posts")
                else:
                    self.log_result("Get Posts Feed", False, "Response is not a list")
            else:
                self.log_result("Get Posts Feed", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Get Posts Feed", False, "", str(e))
        
        # Test post like
        if self.test_post_id:
            try:
                response = self.make_request("POST", f"/posts/{self.test_post_id}/like")
                if response.status_code == 200:
                    data = response.json()
                    if "liked" in data:
                        self.log_result("Post Like", True, f"Post like toggled: {data.get('liked')}")
                    else:
                        self.log_result("Post Like", False, "Missing 'liked' field")
                else:
                    self.log_result("Post Like", False, "", f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("Post Like", False, "", str(e))
            
            # Test post comment
            try:
                comment_data = {"text": "Great photo! Love the colors in this sunset.", "postId": self.test_post_id}
                response = self.make_request("POST", f"/posts/{self.test_post_id}/comments", comment_data)
                if response.status_code in [200, 201]:
                    data = response.json()
                    if "id" in data and "text" in data:
                        self.log_result("Post Comment", True, "Comment created successfully")
                    else:
                        self.log_result("Post Comment", False, "Missing required fields")
                else:
                    self.log_result("Post Comment", False, "", f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("Post Comment", False, "", str(e))
    
    def test_messaging_endpoints(self):
        """Test messaging system endpoints"""
        print("\n💬 TESTING MESSAGING ENDPOINTS")
        
        if not self.user2_id:
            self.log_result("Messaging Tests", False, "Second user not available for messaging tests")
            return
        
        # Test conversation creation
        try:
            conv_data = {
                "participantIds": [self.user_id, self.user2_id],
                "isGroup": False
            }
            response = self.make_request("POST", "/conversations", conv_data)
            if response.status_code in [200, 201]:
                data = response.json()
                if "id" in data:
                    self.test_conversation_id = data["id"]
                    self.log_result("Conversation Creation", True, f"Conversation created: {self.test_conversation_id}")
                else:
                    self.log_result("Conversation Creation", False, "Missing conversation ID")
            else:
                self.log_result("Conversation Creation", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Conversation Creation", False, "", str(e))
        
        # Test get conversations
        try:
            response = self.make_request("GET", "/conversations")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("Get Conversations", True, f"Retrieved {len(data)} conversations")
                else:
                    self.log_result("Get Conversations", False, "Response is not a list")
            else:
                self.log_result("Get Conversations", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Get Conversations", False, "", str(e))
        
        # Test send message
        if self.test_conversation_id:
            try:
                message_data = {
                    "conversationId": self.test_conversation_id,
                    "text": "Hello! This is a test message from the API testing suite.",
                    "messageType": "text"
                }
                response = self.make_request("POST", f"/conversations/{self.test_conversation_id}/messages", message_data)
                if response.status_code in [200, 201]:
                    data = response.json()
                    if "id" in data and "text" in data:
                        self.log_result("Send Message", True, "Message sent successfully")
                    else:
                        self.log_result("Send Message", False, "Missing required fields")
                else:
                    self.log_result("Send Message", False, "", f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("Send Message", False, "", str(e))
            
            # Test get messages
            try:
                response = self.make_request("GET", f"/conversations/{self.test_conversation_id}/messages")
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        self.log_result("Get Messages", True, f"Retrieved {len(data)} messages")
                    else:
                        self.log_result("Get Messages", False, "Response is not a list")
                else:
                    self.log_result("Get Messages", False, "", f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("Get Messages", False, "", str(e))
    
    def test_stories_endpoints(self):
        """Test stories system endpoints"""
        print("\n📖 TESTING STORIES ENDPOINTS")
        
        # Test story creation
        try:
            story_data = {
                "media": SAMPLE_IMAGE_B64,
                "mediaType": "image",
                "text": "Testing story creation! 🎉",
                "textPosition": {"x": 0.5, "y": 0.3},
                "textStyle": {"color": "#ffffff", "fontSize": 24},
                "duration": 24
            }
            response = self.make_request("POST", "/stories", story_data)
            if response.status_code in [200, 201]:
                data = response.json()
                if "id" in data:
                    self.test_story_id = data["id"]
                    self.log_result("Story Creation", True, f"Story created: {self.test_story_id}")
                else:
                    self.log_result("Story Creation", False, "Missing story ID")
            else:
                self.log_result("Story Creation", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Story Creation", False, "", str(e))
        
        # Test get stories feed
        try:
            response = self.make_request("GET", "/stories/feed")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("Get Stories Feed", True, f"Retrieved {len(data)} stories")
                else:
                    self.log_result("Get Stories Feed", False, "Response is not a list")
            else:
                self.log_result("Get Stories Feed", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Get Stories Feed", False, "", str(e))
        
        # Test story view
        if self.test_story_id:
            try:
                response = self.make_request("POST", f"/stories/{self.test_story_id}/view")
                if response.status_code == 200:
                    data = response.json()
                    if "viewed" in data:
                        self.log_result("Story View", True, "Story viewed successfully")
                    else:
                        self.log_result("Story View", False, "Missing 'viewed' field")
                else:
                    self.log_result("Story View", False, "", f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("Story View", False, "", str(e))
    
    def test_follow_system_endpoints(self):
        """Test follow system endpoints"""
        print("\n👥 TESTING FOLLOW SYSTEM ENDPOINTS")
        
        if not self.user2_id:
            self.log_result("Follow System Tests", False, "Second user not available for follow tests")
            return
        
        # Test follow user
        try:
            response = self.make_request("POST", f"/users/{self.user2_id}/follow")
            if response.status_code == 200:
                data = response.json()
                if "following" in data:
                    self.log_result("Follow User", True, f"Follow status: {data.get('following')}")
                else:
                    self.log_result("Follow User", False, "Missing 'following' field")
            else:
                self.log_result("Follow User", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Follow User", False, "", str(e))
        
        # Test get followers
        try:
            response = self.make_request("GET", f"/users/{self.user_id}/followers")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("Get Followers", True, f"Retrieved {len(data)} followers")
                else:
                    self.log_result("Get Followers", False, "Response is not a list")
            else:
                self.log_result("Get Followers", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Get Followers", False, "", str(e))
        
        # Test get following
        try:
            response = self.make_request("GET", f"/users/{self.user_id}/following")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("Get Following", True, f"Retrieved {len(data)} following")
                else:
                    self.log_result("Get Following", False, "Response is not a list")
            else:
                self.log_result("Get Following", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Get Following", False, "", str(e))
    
    def test_notifications_endpoints(self):
        """Test notifications system endpoints"""
        print("\n🔔 TESTING NOTIFICATIONS ENDPOINTS")
        
        # Test get notifications
        try:
            response = self.make_request("GET", "/notifications")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("Get Notifications", True, f"Retrieved {len(data)} notifications")
                else:
                    self.log_result("Get Notifications", False, "Response is not a list")
            else:
                self.log_result("Get Notifications", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Get Notifications", False, "", str(e))
        
        # Test mark all notifications as read
        try:
            response = self.make_request("PUT", "/notifications/read-all")
            if response.status_code == 200:
                data = response.json()
                if "success" in data:
                    self.log_result("Mark All Notifications Read", True, "All notifications marked as read")
                else:
                    self.log_result("Mark All Notifications Read", False, "Missing success field")
            else:
                self.log_result("Mark All Notifications Read", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Mark All Notifications Read", False, "", str(e))
    
    def test_search_endpoints(self):
        """Test search and discovery endpoints"""
        print("\n🔍 TESTING SEARCH & DISCOVERY ENDPOINTS")
        
        # Test universal search
        try:
            response = self.make_request("GET", "/search?query=test&type=all")
            if response.status_code == 200:
                data = response.json()
                if "users" in data or "posts" in data or "hashtags" in data:
                    self.log_result("Universal Search", True, "Search results retrieved")
                else:
                    self.log_result("Universal Search", False, "Missing search result categories")
            else:
                self.log_result("Universal Search", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Universal Search", False, "", str(e))
        
        # Test trending hashtags
        try:
            response = self.make_request("GET", "/trending/hashtags")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("Trending Hashtags", True, f"Retrieved {len(data)} trending hashtags")
                else:
                    self.log_result("Trending Hashtags", False, "Response is not a list")
            else:
                self.log_result("Trending Hashtags", False, "", f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Trending Hashtags", False, "", str(e))
    
    def test_phase16_endpoints(self):
        """Test Phase 16 - Posting & Media Enhancements endpoints"""
        print("\n🎯 TESTING PHASE 16 - POSTING & MEDIA ENHANCEMENTS")
        
        # Test search tags endpoint
        try:
            response = self.make_request("GET", "/search/tags?query=sarah&type=users")
            if response.status_code == 200:
                self.log_result("Search Tags (Users)", True, "Search tags endpoint working")
            else:
                self.log_result("Search Tags (Users)", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Search Tags (Users)", False, str(e))
        
        # Test enhanced post creation
        try:
            enhanced_post_data = {
                "caption": "Enhanced post with location and tags! #enhanced #testing",
                "media": [SAMPLE_IMAGE_B64],
                "mediaTypes": ["image"],
                "hashtags": ["enhanced", "testing"],
                "taggedUsers": [],
                "location": {
                    "name": "Central Park",
                    "coordinates": {"lat": 40.785091, "lng": -73.968285}
                }
            }
            response = self.make_request("POST", "/posts/enhanced", enhanced_post_data)
            if response.status_code in [200, 201]:
                self.log_result("Enhanced Post Creation", True, "Enhanced post created successfully")
            else:
                self.log_result("Enhanced Post Creation", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Enhanced Post Creation", False, str(e))
        
        # Test validate tags endpoint
        try:
            validate_data = {
                "taggedUsers": [self.user_id] if self.user_id else [],
                "postType": "post"
            }
            response = self.make_request("POST", "/posts/validate-tags", validate_data)
            if response.status_code == 200:
                self.log_result("Validate Tags", True, "Tag validation working")
            else:
                self.log_result("Validate Tags", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Validate Tags", False, str(e))
    
    def test_phase17_endpoints(self):
        """Test Phase 17 - Story & Creative Tools endpoints"""
        print("\n🎨 TESTING PHASE 17 - STORY & CREATIVE TOOLS")
        
        # Test creative music library
        try:
            response = self.make_request("GET", "/creative/music?query=pop")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("Creative Music Library", True, f"Retrieved {len(data)} music tracks")
                else:
                    self.log_result("Creative Music Library", False, "Response is not a list")
            else:
                self.log_result("Creative Music Library", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Creative Music Library", False, str(e))
        
        # Test GIF library
        try:
            response = self.make_request("GET", "/creative/gifs?query=happy")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("Creative GIF Library", True, f"Retrieved {len(data)} GIFs")
                else:
                    self.log_result("Creative GIF Library", False, "Response is not a list")
            else:
                self.log_result("Creative GIF Library", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Creative GIF Library", False, str(e))
        
        # Test frame templates
        try:
            response = self.make_request("GET", "/creative/frames")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("Creative Frame Templates", True, f"Retrieved {len(data)} frame templates")
                else:
                    self.log_result("Creative Frame Templates", False, "Response is not a list")
            else:
                self.log_result("Creative Frame Templates", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Creative Frame Templates", False, str(e))
        
        # Test collaborative prompts
        try:
            response = self.make_request("GET", "/collaborative/prompts/trending")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("Collaborative Prompts", True, f"Retrieved {len(data)} trending prompts")
                else:
                    self.log_result("Collaborative Prompts", False, "Response is not a list")
            else:
                self.log_result("Collaborative Prompts", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Collaborative Prompts", False, str(e))
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 STARTING NOVASOCIAL BACKEND API TESTING")
        print(f"Testing against: {BACKEND_URL}")
        print("=" * 60)
        
        # Setup authentication first
        if not self.setup_auth():
            print("❌ Authentication setup failed. Cannot proceed with tests.")
            return
        
        # Run all test suites
        self.test_authentication_endpoints()
        self.test_post_endpoints()
        self.test_messaging_endpoints()
        self.test_stories_endpoints()
        self.test_follow_system_endpoints()
        self.test_notifications_endpoints()
        self.test_search_endpoints()
        self.test_phase16_endpoints()
        self.test_phase17_endpoints()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS ({failed_tests}):")
            for test in self.test_results:
                if not test["success"]:
                    print(f"  • {test['test']}: {test['error'] or test['details']}")
        
        print(f"\n✅ PASSED TESTS ({passed_tests}):")
        for test in self.test_results:
            if test["success"]:
                print(f"  • {test['test']}")
        
        # Save detailed results to file
        with open("/app/test_results_detailed.json", "w") as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: /app/test_results_detailed.json")

if __name__ == "__main__":
    tester = NovaSocialAPITester()
    tester.run_all_tests()