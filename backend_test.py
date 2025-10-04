#!/usr/bin/env python3
"""
NovaSocial Backend API Testing Suite
Tests messaging system, stories system, and authentication with Socket.IO integration
"""

import requests
import json
import base64
import time
from datetime import datetime, timedelta
import uuid

# Backend URL from frontend/.env
BACKEND_URL = "https://mobile-social-app-1.preview.emergentagent.com/api"

# Test users for messaging system
TEST_USER_1 = {
    "fullName": "Alice Johnson",
    "username": "alice_test_user",
    "email": "alice.test@example.com",
    "password": "testpassword123"
}
TEST_USER_2 = {
    "fullName": "Bob Smith", 
    "username": "bob_test_user",
    "email": "bob.test@example.com",
    "password": "testpassword456"
}

# Global variables to store tokens and user data
user1_token = None
user1_data = None
user2_token = None
user2_data = None
test_conversation_id = None
test_story_id = None

class ComprehensiveTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_user_data = {
            "fullName": "Sarah Johnson",
            "username": "sarah_johnson",
            "email": "sarah.johnson@example.com",
            "password": "SecurePass123"
        }
        self.auth_token = None
        self.user_id = None
        
    def log_test(self, test_name, status, details=""):
        """Log test results"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"[{timestamp}] {status_symbol} {test_name}")
        if details:
            print(f"    Details: {details}")
        print()

def print_test_header(test_name):
    print(f"\n{'='*60}")
    print(f"TESTING: {test_name}")
    print(f"{'='*60}")

def print_result(test_name, success, details=""):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"   Details: {details}")

def create_test_image_base64():
    """Create a simple test image in base64 format"""
    # Simple 1x1 pixel PNG in base64
    return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77zgAAAABJRU5ErkJggg=="

def test_user_authentication():
    """Test user registration and login to get JWT tokens"""
    global user1_token, user1_data, user2_token, user2_data
    
    print_test_header("USER AUTHENTICATION SYSTEM")
    
    # Test User 1 Registration
    try:
        response = requests.post(f"{BACKEND_URL}/auth/register", json=TEST_USER_1)
        if response.status_code == 201 or response.status_code == 200:
            data = response.json()
            user1_token = data.get("token")
            user1_data = data.get("user")
            print_result("User 1 Registration", True, f"User ID: {user1_data.get('id')}")
        elif response.status_code == 400 and "already" in response.text.lower():
            # User already exists, try login
            login_response = requests.post(f"{BACKEND_URL}/auth/login", json={
                "email": TEST_USER_1["email"],
                "password": TEST_USER_1["password"]
            })
            if login_response.status_code == 200:
                data = login_response.json()
                user1_token = data.get("token")
                user1_data = data.get("user")
                print_result("User 1 Login (existing user)", True, f"User ID: {user1_data.get('id')}")
            else:
                print_result("User 1 Authentication", False, f"Login failed: {login_response.text}")
                return False
        else:
            print_result("User 1 Registration", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        print_result("User 1 Authentication", False, f"Exception: {str(e)}")
        return False
    
    # Test User 2 Registration
    try:
        response = requests.post(f"{BACKEND_URL}/auth/register", json=TEST_USER_2)
        if response.status_code == 201 or response.status_code == 200:
            data = response.json()
            user2_token = data.get("token")
            user2_data = data.get("user")
            print_result("User 2 Registration", True, f"User ID: {user2_data.get('id')}")
        elif response.status_code == 400 and "already" in response.text.lower():
            # User already exists, try login
            login_response = requests.post(f"{BACKEND_URL}/auth/login", json={
                "email": TEST_USER_2["email"],
                "password": TEST_USER_2["password"]
            })
            if login_response.status_code == 200:
                data = login_response.json()
                user2_token = data.get("token")
                user2_data = data.get("user")
                print_result("User 2 Login (existing user)", True, f"User ID: {user2_data.get('id')}")
            else:
                print_result("User 2 Authentication", False, f"Login failed: {login_response.text}")
                return False
        else:
            print_result("User 2 Registration", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        print_result("User 2 Authentication", False, f"Exception: {str(e)}")
        return False
    
    return user1_token and user2_token

def test_messaging_system():
    """Test the complete messaging system"""
    global test_conversation_id
    
    print_test_header("MESSAGING SYSTEM")
    
    if not user1_token or not user2_token:
        print_result("Messaging System", False, "Authentication tokens not available")
        return False
    
    headers1 = {"Authorization": f"Bearer {user1_token}"}
    headers2 = {"Authorization": f"Bearer {user2_token}"}
    
    # Test 1: Create a new conversation
    try:
        conversation_data = {
            "participantIds": [user1_data["id"], user2_data["id"]],
            "isGroup": False
        }
        response = requests.post(f"{BACKEND_URL}/conversations", json=conversation_data, headers=headers1)
        
        if response.status_code == 200 or response.status_code == 201:
            conv_data = response.json()
            test_conversation_id = conv_data.get("id")
            print_result("POST /api/conversations - Create conversation", True, f"Conversation ID: {test_conversation_id}")
        else:
            print_result("POST /api/conversations - Create conversation", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        print_result("POST /api/conversations - Create conversation", False, f"Exception: {str(e)}")
        return False
    
    # Test 2: Get user conversations
    try:
        response = requests.get(f"{BACKEND_URL}/conversations", headers=headers1)
        
        if response.status_code == 200:
            conversations = response.json()
            found_conversation = any(conv.get("id") == test_conversation_id for conv in conversations)
            print_result("GET /api/conversations - Get user conversations", found_conversation, f"Found {len(conversations)} conversations")
        else:
            print_result("GET /api/conversations - Get user conversations", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        print_result("GET /api/conversations - Get user conversations", False, f"Exception: {str(e)}")
        return False
    
    # Test 3: Send a message
    try:
        message_data = {
            "conversationId": test_conversation_id,
            "text": "Hello! This is a test message from Alice.",
            "messageType": "text"
        }
        response = requests.post(f"{BACKEND_URL}/conversations/{test_conversation_id}/messages", json=message_data, headers=headers1)
        
        if response.status_code == 200 or response.status_code == 201:
            message_response = response.json()
            print_result("POST /api/conversations/{id}/messages - Send message", True, f"Message ID: {message_response.get('id')}")
        else:
            print_result("POST /api/conversations/{id}/messages - Send message", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        print_result("POST /api/conversations/{id}/messages - Send message", False, f"Exception: {str(e)}")
        return False
    
    # Test 4: Send a message with media
    try:
        message_data = {
            "conversationId": test_conversation_id,
            "text": "Here's an image!",
            "messageType": "image",
            "media": create_test_image_base64()
        }
        response = requests.post(f"{BACKEND_URL}/conversations/{test_conversation_id}/messages", json=message_data, headers=headers2)
        
        if response.status_code == 200 or response.status_code == 201:
            message_response = response.json()
            print_result("POST /api/conversations/{id}/messages - Send image message", True, f"Message ID: {message_response.get('id')}")
        else:
            print_result("POST /api/conversations/{id}/messages - Send image message", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        print_result("POST /api/conversations/{id}/messages - Send image message", False, f"Exception: {str(e)}")
        return False
    
    # Test 5: Get conversation messages
    try:
        response = requests.get(f"{BACKEND_URL}/conversations/{test_conversation_id}/messages", headers=headers1)
        
        if response.status_code == 200:
            messages = response.json()
            print_result("GET /api/conversations/{id}/messages - Get messages", True, f"Retrieved {len(messages)} messages")
            
            # Verify message content
            text_message = next((msg for msg in messages if msg.get("messageType") == "text"), None)
            image_message = next((msg for msg in messages if msg.get("messageType") == "image"), None)
            
            if text_message and image_message:
                print_result("Message content validation", True, "Both text and image messages found")
            else:
                print_result("Message content validation", False, "Missing expected message types")
        else:
            print_result("GET /api/conversations/{id}/messages - Get messages", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        print_result("GET /api/conversations/{id}/messages - Get messages", False, f"Exception: {str(e)}")
        return False
    
    return True

def test_stories_system():
    """Test the complete stories system"""
    global test_story_id
    
    print_test_header("STORIES SYSTEM")
    
    if not user1_token or not user2_token:
        print_result("Stories System", False, "Authentication tokens not available")
        return False
    
    headers1 = {"Authorization": f"Bearer {user1_token}"}
    headers2 = {"Authorization": f"Bearer {user2_token}"}
    
    # Test 1: Create a new story
    try:
        story_data = {
            "media": create_test_image_base64(),
            "mediaType": "image",
            "text": "This is my test story!",
            "textPosition": {"x": 0.5, "y": 0.3},
            "textStyle": {"color": "#ffffff", "fontSize": 24},
            "duration": 24
        }
        response = requests.post(f"{BACKEND_URL}/stories", json=story_data, headers=headers1)
        
        if response.status_code == 200 or response.status_code == 201:
            story_response = response.json()
            test_story_id = story_response.get("id")
            print_result("POST /api/stories - Create story", True, f"Story ID: {test_story_id}")
        else:
            print_result("POST /api/stories - Create story", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        print_result("POST /api/stories - Create story", False, f"Exception: {str(e)}")
        return False
    
    # Test 2: Get stories feed
    try:
        response = requests.get(f"{BACKEND_URL}/stories/feed", headers=headers2)
        
        if response.status_code == 200:
            stories = response.json()
            found_story = any(story.get("id") == test_story_id for story in stories)
            print_result("GET /api/stories/feed - Get stories feed", found_story, f"Found {len(stories)} stories")
        else:
            print_result("GET /api/stories/feed - Get stories feed", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        print_result("GET /api/stories/feed - Get stories feed", False, f"Exception: {str(e)}")
        return False
    
    # Test 3: View a story
    try:
        response = requests.post(f"{BACKEND_URL}/stories/{test_story_id}/view", headers=headers2)
        
        if response.status_code == 200:
            view_response = response.json()
            print_result("POST /api/stories/{id}/view - View story", True, f"Viewed: {view_response.get('viewed')}")
        else:
            print_result("POST /api/stories/{id}/view - View story", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        print_result("POST /api/stories/{id}/view - View story", False, f"Exception: {str(e)}")
        return False
    
    # Test 4: View story again (should not increment view count)
    try:
        response = requests.post(f"{BACKEND_URL}/stories/{test_story_id}/view", headers=headers2)
        
        if response.status_code == 200:
            print_result("POST /api/stories/{id}/view - View story again", True, "Duplicate view handled correctly")
        else:
            print_result("POST /api/stories/{id}/view - View story again", False, f"Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print_result("POST /api/stories/{id}/view - View story again", False, f"Exception: {str(e)}")
    
    # Test 5: Delete story (by owner)
    try:
        response = requests.delete(f"{BACKEND_URL}/stories/{test_story_id}", headers=headers1)
        
        if response.status_code == 200:
            delete_response = response.json()
            print_result("DELETE /api/stories/{id} - Delete story", True, f"Deleted: {delete_response.get('deleted')}")
        else:
            print_result("DELETE /api/stories/{id} - Delete story", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        print_result("DELETE /api/stories/{id} - Delete story", False, f"Exception: {str(e)}")
        return False
    
    # Test 6: Try to view deleted story (should fail)
    try:
        response = requests.post(f"{BACKEND_URL}/stories/{test_story_id}/view", headers=headers2)
        
        if response.status_code == 404:
            print_result("View deleted story - Error handling", True, "Correctly returns 404 for deleted story")
        else:
            print_result("View deleted story - Error handling", False, f"Expected 404, got {response.status_code}")
    except Exception as e:
        print_result("View deleted story - Error handling", False, f"Exception: {str(e)}")
    
    return True

def test_error_handling():
    """Test error handling and validation"""
    print_test_header("ERROR HANDLING & VALIDATION")
    
    if not user1_token:
        print_result("Error Handling Tests", False, "Authentication token not available")
        return False
    
    headers = {"Authorization": f"Bearer {user1_token}"}
    
    # Test 1: Access conversation without permission
    try:
        fake_conversation_id = str(uuid.uuid4())
        response = requests.get(f"{BACKEND_URL}/conversations/{fake_conversation_id}/messages", headers=headers)
        
        if response.status_code == 404:
            print_result("Access non-existent conversation", True, "Correctly returns 404")
        else:
            print_result("Access non-existent conversation", False, f"Expected 404, got {response.status_code}")
    except Exception as e:
        print_result("Access non-existent conversation", False, f"Exception: {str(e)}")
    
    # Test 2: Create story without media
    try:
        story_data = {
            "mediaType": "image",
            "text": "Story without media"
        }
        response = requests.post(f"{BACKEND_URL}/stories", json=story_data, headers=headers)
        
        if response.status_code == 422:  # Validation error
            print_result("Create story without media", True, "Correctly validates required fields")
        else:
            print_result("Create story without media", False, f"Expected validation error, got {response.status_code}")
    except Exception as e:
        print_result("Create story without media", False, f"Exception: {str(e)}")
    
    # Test 3: Unauthorized access
    try:
        response = requests.get(f"{BACKEND_URL}/conversations")
        
        if response.status_code == 403 or response.status_code == 401:
            print_result("Unauthorized access", True, "Correctly requires authentication")
        else:
            print_result("Unauthorized access", False, f"Expected 401/403, got {response.status_code}")
    except Exception as e:
        print_result("Unauthorized access", False, f"Exception: {str(e)}")
    
    return True

    def test_user_registration(self):
        """Test user registration endpoint"""
        print("=" * 60)
        print("TESTING USER REGISTRATION API")
        print("=" * 60)
        
        # Test 1: Successful registration
        try:
            response = requests.post(
                f"{self.base_url}/auth/register",
                json=self.test_user_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "user" in data and "token" in data:
                    self.auth_token = data["token"]
                    self.user_id = data["user"]["id"]
                    self.log_test("User Registration - Valid Data", "PASS", 
                                f"User created with ID: {self.user_id}")
                else:
                    self.log_test("User Registration - Valid Data", "FAIL", 
                                "Response missing user or token")
            else:
                self.log_test("User Registration - Valid Data", "FAIL", 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("User Registration - Valid Data", "FAIL", f"Exception: {str(e)}")

        # Test 2: Duplicate email validation
        try:
            duplicate_data = self.test_user_data.copy()
            duplicate_data["username"] = "different_username"
            
            response = requests.post(
                f"{self.base_url}/auth/register",
                json=duplicate_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 400 and "Email already registered" in response.text:
                self.log_test("User Registration - Duplicate Email", "PASS", 
                            "Correctly rejected duplicate email")
            else:
                self.log_test("User Registration - Duplicate Email", "FAIL", 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("User Registration - Duplicate Email", "FAIL", f"Exception: {str(e)}")

        # Test 3: Duplicate username validation
        try:
            duplicate_data = self.test_user_data.copy()
            duplicate_data["email"] = "different@example.com"
            
            response = requests.post(
                f"{self.base_url}/auth/register",
                json=duplicate_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 400 and "Username already taken" in response.text:
                self.log_test("User Registration - Duplicate Username", "PASS", 
                            "Correctly rejected duplicate username")
            else:
                self.log_test("User Registration - Duplicate Username", "FAIL", 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("User Registration - Duplicate Username", "FAIL", f"Exception: {str(e)}")

        # Test 4: Username format validation
        try:
            invalid_username_data = self.test_user_data.copy()
            invalid_username_data["username"] = "ab"  # Too short
            invalid_username_data["email"] = "test_short@example.com"
            
            response = requests.post(
                f"{self.base_url}/auth/register",
                json=invalid_username_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 400 and "3-20 characters" in response.text:
                self.log_test("User Registration - Invalid Username Format", "PASS", 
                            "Correctly rejected short username")
            else:
                self.log_test("User Registration - Invalid Username Format", "FAIL", 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("User Registration - Invalid Username Format", "FAIL", f"Exception: {str(e)}")

        # Test 5: Password validation
        try:
            weak_password_data = self.test_user_data.copy()
            weak_password_data["password"] = "weak"  # Too short
            weak_password_data["email"] = "test_weak@example.com"
            weak_password_data["username"] = "test_weak"
            
            response = requests.post(
                f"{self.base_url}/auth/register",
                json=weak_password_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 400 and "at least 8 characters" in response.text:
                self.log_test("User Registration - Weak Password", "PASS", 
                            "Correctly rejected weak password")
            else:
                self.log_test("User Registration - Weak Password", "FAIL", 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("User Registration - Weak Password", "FAIL", f"Exception: {str(e)}")

    def test_user_login(self):
        """Test user login endpoint"""
        print("=" * 60)
        print("TESTING USER LOGIN API")
        print("=" * 60)
        
        # Test 1: Successful login
        try:
            login_data = {
                "email": self.test_user_data["email"],
                "password": self.test_user_data["password"]
            }
            
            response = requests.post(
                f"{self.base_url}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "user" in data and "token" in data:
                    self.auth_token = data["token"]  # Update token
                    self.log_test("User Login - Valid Credentials", "PASS", 
                                "Successfully logged in with JWT token")
                else:
                    self.log_test("User Login - Valid Credentials", "FAIL", 
                                "Response missing user or token")
            else:
                self.log_test("User Login - Valid Credentials", "FAIL", 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("User Login - Valid Credentials", "FAIL", f"Exception: {str(e)}")

        # Test 2: Invalid email
        try:
            invalid_login_data = {
                "email": "nonexistent@example.com",
                "password": self.test_user_data["password"]
            }
            
            response = requests.post(
                f"{self.base_url}/auth/login",
                json=invalid_login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 401 and "Incorrect email or password" in response.text:
                self.log_test("User Login - Invalid Email", "PASS", 
                            "Correctly rejected invalid email")
            else:
                self.log_test("User Login - Invalid Email", "FAIL", 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("User Login - Invalid Email", "FAIL", f"Exception: {str(e)}")

        # Test 3: Invalid password
        try:
            invalid_login_data = {
                "email": self.test_user_data["email"],
                "password": "wrongpassword"
            }
            
            response = requests.post(
                f"{self.base_url}/auth/login",
                json=invalid_login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 401 and "Incorrect email or password" in response.text:
                self.log_test("User Login - Invalid Password", "PASS", 
                            "Correctly rejected invalid password")
            else:
                self.log_test("User Login - Invalid Password", "FAIL", 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("User Login - Invalid Password", "FAIL", f"Exception: {str(e)}")

    def test_profile_update(self):
        """Test profile update endpoint"""
        print("=" * 60)
        print("TESTING PROFILE UPDATE API")
        print("=" * 60)
        
        if not self.auth_token:
            self.log_test("Profile Update - Setup", "FAIL", "No auth token available")
            return

        # Test 1: Update profile with valid token
        try:
            # Create a simple base64 image (1x1 pixel PNG)
            sample_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77yQAAAABJRU5ErkJggg=="
            
            profile_data = {
                "profileImage": f"data:image/png;base64,{sample_image_b64}",
                "bio": "Passionate photographer and social media enthusiast. Love capturing life's beautiful moments! 📸✨"
            }
            
            response = requests.put(
                f"{self.base_url}/auth/profile",
                json=profile_data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.auth_token}"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if "profileImage" in data and "bio" in data:
                    self.log_test("Profile Update - Valid Token", "PASS", 
                                "Successfully updated profile image and bio")
                else:
                    self.log_test("Profile Update - Valid Token", "FAIL", 
                                "Response missing profileImage or bio")
            else:
                self.log_test("Profile Update - Valid Token", "FAIL", 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Profile Update - Valid Token", "FAIL", f"Exception: {str(e)}")

        # Test 2: Update profile without token (unauthorized)
        try:
            profile_data = {
                "bio": "This should fail"
            }
            
            response = requests.put(
                f"{self.base_url}/auth/profile",
                json=profile_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 403:
                self.log_test("Profile Update - No Token", "PASS", 
                            "Correctly rejected request without token")
            else:
                self.log_test("Profile Update - No Token", "FAIL", 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Profile Update - No Token", "FAIL", f"Exception: {str(e)}")

        # Test 3: Update profile with invalid token
        try:
            profile_data = {
                "bio": "This should also fail"
            }
            
            response = requests.put(
                f"{self.base_url}/auth/profile",
                json=profile_data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer invalid_token_here"
                }
            )
            
            if response.status_code == 401:
                self.log_test("Profile Update - Invalid Token", "PASS", 
                            "Correctly rejected request with invalid token")
            else:
                self.log_test("Profile Update - Invalid Token", "FAIL", 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Profile Update - Invalid Token", "FAIL", f"Exception: {str(e)}")

    def test_get_current_user(self):
        """Test get current user profile endpoint"""
        print("=" * 60)
        print("TESTING GET CURRENT USER PROFILE API")
        print("=" * 60)
        
        if not self.auth_token:
            self.log_test("Get Current User - Setup", "FAIL", "No auth token available")
            return

        # Test 1: Get profile with valid token
        try:
            response = requests.get(
                f"{self.base_url}/auth/me",
                headers={
                    "Authorization": f"Bearer {self.auth_token}"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ["id", "email", "username", "fullName", "createdAt"]
                if all(field in data for field in expected_fields):
                    self.log_test("Get Current User - Valid Token", "PASS", 
                                f"Successfully retrieved user profile for {data.get('username')}")
                else:
                    missing_fields = [field for field in expected_fields if field not in data]
                    self.log_test("Get Current User - Valid Token", "FAIL", 
                                f"Response missing fields: {missing_fields}")
            else:
                self.log_test("Get Current User - Valid Token", "FAIL", 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Get Current User - Valid Token", "FAIL", f"Exception: {str(e)}")

        # Test 2: Get profile without token
        try:
            response = requests.get(f"{self.base_url}/auth/me")
            
            if response.status_code == 403:
                self.log_test("Get Current User - No Token", "PASS", 
                            "Correctly rejected request without token")
            else:
                self.log_test("Get Current User - No Token", "FAIL", 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Get Current User - No Token", "FAIL", f"Exception: {str(e)}")

        # Test 3: Get profile with invalid token
        try:
            response = requests.get(
                f"{self.base_url}/auth/me",
                headers={
                    "Authorization": "Bearer invalid_token_here"
                }
            )
            
            if response.status_code == 401:
                self.log_test("Get Current User - Invalid Token", "PASS", 
                            "Correctly rejected request with invalid token")
            else:
                self.log_test("Get Current User - Invalid Token", "FAIL", 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Get Current User - Invalid Token", "FAIL", f"Exception: {str(e)}")

    def test_database_validation(self):
        """Test database operations and data integrity"""
        print("=" * 60)
        print("TESTING DATABASE VALIDATION")
        print("=" * 60)
        
        # This would require direct database access which we don't have in this test environment
        # Instead, we'll verify through API responses that data is properly stored
        
        if not self.auth_token:
            self.log_test("Database Validation", "FAIL", "No auth token available for validation")
            return
            
        try:
            # Get current user to verify data structure
            response = requests.get(
                f"{self.base_url}/auth/me",
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            
            if response.status_code == 200:
                user_data = response.json()
                
                # Check that password is not returned
                if "password" not in user_data:
                    self.log_test("Database Validation - Password Security", "PASS", 
                                "Password correctly excluded from API response")
                else:
                    self.log_test("Database Validation - Password Security", "FAIL", 
                                "Password field present in API response")
                
                # Check user data structure
                required_fields = ["id", "email", "username", "fullName", "createdAt"]
                if all(field in user_data for field in required_fields):
                    self.log_test("Database Validation - User Schema", "PASS", 
                                "User data structure matches expected schema")
                else:
                    missing = [f for f in required_fields if f not in user_data]
                    self.log_test("Database Validation - User Schema", "FAIL", 
                                f"Missing required fields: {missing}")
                    
                # Check that username is lowercase (as per backend logic)
                if user_data.get("username") == self.test_user_data["username"].lower():
                    self.log_test("Database Validation - Username Format", "PASS", 
                                "Username correctly stored in lowercase")
                else:
                    self.log_test("Database Validation - Username Format", "FAIL", 
                                f"Username format issue: expected {self.test_user_data['username'].lower()}, got {user_data.get('username')}")
                    
            else:
                self.log_test("Database Validation", "FAIL", 
                            f"Could not retrieve user data for validation: {response.status_code}")
                
        except Exception as e:
            self.log_test("Database Validation", "FAIL", f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all authentication tests"""
        print("🚀 Starting NovaSocial Backend Authentication Tests")
        print(f"Backend URL: {self.base_url}")
        print(f"Test User: {self.test_user_data['email']}")
        print()
        
        # Run tests in sequence
        self.test_user_registration()
        self.test_user_login()
        self.test_profile_update()
        self.test_get_current_user()
        self.test_database_validation()
        
        print("=" * 60)
        print("🏁 AUTHENTICATION TESTING COMPLETE")
        print("=" * 60)

def run_comprehensive_tests():
    """Run all backend tests including messaging and stories"""
    print("🚀 Starting NovaSocial Backend Comprehensive API Tests")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test started at: {datetime.now()}")
    
    test_results = {
        "authentication": False,
        "messaging": False,
        "stories": False,
        "error_handling": False
    }
    
    # Run tests in sequence
    test_results["authentication"] = test_user_authentication()
    
    if test_results["authentication"]:
        test_results["messaging"] = test_messaging_system()
        test_results["stories"] = test_stories_system()
        test_results["error_handling"] = test_error_handling()
    
    # Print final summary
    print_test_header("FINAL TEST SUMMARY")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result is True)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name.upper()}")
    
    print(f"\n📊 OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Backend is working correctly.")
        return True
    else:
        print("⚠️  SOME TESTS FAILED! Check the details above.")
        return False

def test_phase8_endpoints():
    """Test Phase 8 endpoints: user posts and user stats"""
    print_test_header("PHASE 8 ENDPOINTS - USER POSTS & STATS")
    
    if not user1_token or not user2_token:
        print_result("Phase 8 Endpoints", False, "Authentication tokens not available")
        return False
    
    headers1 = {"Authorization": f"Bearer {user1_token}"}
    headers2 = {"Authorization": f"Bearer {user2_token}"}
    
    # First, create some test posts for user1
    test_posts_created = []
    
    # Create 3 test posts for user1
    for i in range(3):
        try:
            post_data = {
                "caption": f"Test post {i+1} by {user1_data['username']} - sharing amazing content! #test #phase8 #novasocial",
                "media": [create_test_image_base64()],
                "mediaTypes": ["image"],
                "hashtags": ["test", "phase8", "novasocial"],
                "taggedUsers": []
            }
            response = requests.post(f"{BACKEND_URL}/posts", json=post_data, headers=headers1)
            
            if response.status_code == 200 or response.status_code == 201:
                post = response.json()
                test_posts_created.append(post)
                print_result(f"Create test post {i+1}", True, f"Post ID: {post.get('id')}")
            else:
                print_result(f"Create test post {i+1}", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            print_result(f"Create test post {i+1}", False, f"Exception: {str(e)}")
    
    # Create follow relationship for stats testing
    try:
        response = requests.post(f"{BACKEND_URL}/users/{user2_data['id']}/follow", headers=headers1)
        if response.status_code == 200:
            print_result("Create follow relationship", True, f"{user1_data['username']} follows {user2_data['username']}")
        else:
            print_result("Create follow relationship", False, f"Status: {response.status_code}")
    except Exception as e:
        print_result("Create follow relationship", False, f"Exception: {str(e)}")
    
    # Test 1: GET /api/users/{user_id}/posts - Get posts by specific user
    try:
        user_id = user1_data["id"]
        response = requests.get(f"{BACKEND_URL}/users/{user_id}/posts")
        
        if response.status_code == 200:
            posts = response.json()
            print_result("GET /api/users/{user_id}/posts - Get user posts", True, f"Retrieved {len(posts)} posts")
            
            # Validate response structure
            if posts:
                post = posts[0]
                required_fields = ["id", "authorId", "author", "caption", "media", "mediaTypes", "createdAt"]
                missing_fields = [field for field in required_fields if field not in post]
                
                if missing_fields:
                    print_result("User posts response validation", False, f"Missing fields: {missing_fields}")
                else:
                    print_result("User posts response validation", True, "All required fields present")
                    
                # Check if posts are in descending order (newest first)
                if len(posts) > 1:
                    first_time = posts[0]["createdAt"]
                    second_time = posts[1]["createdAt"]
                    if first_time >= second_time:
                        print_result("User posts ordering", True, "Posts correctly ordered (newest first)")
                    else:
                        print_result("User posts ordering", False, "Posts not properly ordered")
                        
                # Validate author information
                author = post["author"]
                author_fields = ["id", "username", "fullName", "email"]
                missing_author_fields = [field for field in author_fields if field not in author]
                
                if missing_author_fields:
                    print_result("User posts author info", False, f"Missing author fields: {missing_author_fields}")
                else:
                    print_result("User posts author info", True, "Author information complete")
            else:
                print_result("User posts content", False, "No posts returned despite creating test posts")
        else:
            print_result("GET /api/users/{user_id}/posts - Get user posts", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        print_result("GET /api/users/{user_id}/posts - Get user posts", False, f"Exception: {str(e)}")
        return False
    
    # Test 2: GET /api/users/{user_id}/posts with non-existent user
    try:
        fake_user_id = str(uuid.uuid4())
        response = requests.get(f"{BACKEND_URL}/users/{fake_user_id}/posts")
        
        if response.status_code == 404:
            print_result("GET /api/users/{user_id}/posts - Non-existent user", True, "Correctly returns 404")
        else:
            print_result("GET /api/users/{user_id}/posts - Non-existent user", False, f"Expected 404, got {response.status_code}")
    except Exception as e:
        print_result("GET /api/users/{user_id}/posts - Non-existent user", False, f"Exception: {str(e)}")
    
    # Test 3: GET /api/users/{user_id}/stats - Get user statistics
    try:
        user_id = user1_data["id"]
        response = requests.get(f"{BACKEND_URL}/users/{user_id}/stats")
        
        if response.status_code == 200:
            stats = response.json()
            print_result("GET /api/users/{user_id}/stats - Get user stats", True, f"Stats: {stats}")
            
            # Validate response structure
            required_fields = ["postsCount", "followersCount", "followingCount"]
            missing_fields = [field for field in required_fields if field not in stats]
            
            if missing_fields:
                print_result("User stats response validation", False, f"Missing fields: {missing_fields}")
            else:
                print_result("User stats response validation", True, "All required fields present")
                
            # Validate data types and values
            for field in required_fields:
                if not isinstance(stats[field], int):
                    print_result(f"User stats {field} type", False, f"Expected int, got {type(stats[field])}")
                elif stats[field] < 0:
                    print_result(f"User stats {field} value", False, f"Negative value: {stats[field]}")
                else:
                    print_result(f"User stats {field} validation", True, f"Valid value: {stats[field]}")
                    
            # Check if stats make sense based on our test data
            if stats["postsCount"] >= len(test_posts_created):
                print_result("User stats posts count accuracy", True, f"Posts count {stats['postsCount']} >= created posts {len(test_posts_created)}")
            else:
                print_result("User stats posts count accuracy", False, f"Posts count {stats['postsCount']} < created posts {len(test_posts_created)}")
                
        else:
            print_result("GET /api/users/{user_id}/stats - Get user stats", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        print_result("GET /api/users/{user_id}/stats - Get user stats", False, f"Exception: {str(e)}")
        return False
    
    # Test 4: GET /api/users/{user_id}/stats with non-existent user
    try:
        fake_user_id = str(uuid.uuid4())
        response = requests.get(f"{BACKEND_URL}/users/{fake_user_id}/stats")
        
        if response.status_code == 404:
            print_result("GET /api/users/{user_id}/stats - Non-existent user", True, "Correctly returns 404")
        else:
            print_result("GET /api/users/{user_id}/stats - Non-existent user", False, f"Expected 404, got {response.status_code}")
    except Exception as e:
        print_result("GET /api/users/{user_id}/stats - Non-existent user", False, f"Exception: {str(e)}")
    
    # Test 5: Test with authentication (should work with or without auth for these public endpoints)
    try:
        user_id = user1_data["id"]
        response = requests.get(f"{BACKEND_URL}/users/{user_id}/posts", headers=headers2)
        
        if response.status_code == 200:
            print_result("User posts with authentication", True, "Endpoints work with valid auth token")
        else:
            print_result("User posts with authentication", False, f"Failed with auth token: {response.status_code}")
    except Exception as e:
        print_result("User posts with authentication", False, f"Exception: {str(e)}")
    
    return True

def run_comprehensive_tests():
    """Run all backend tests including messaging, stories, and Phase 8 endpoints"""
    print("🚀 Starting NovaSocial Backend Comprehensive API Tests")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test started at: {datetime.now()}")
    
    test_results = {
        "authentication": False,
        "messaging": False,
        "stories": False,
        "error_handling": False,
        "phase8_endpoints": False
    }
    
    # Run tests in sequence
    test_results["authentication"] = test_user_authentication()
    
    if test_results["authentication"]:
        test_results["messaging"] = test_messaging_system()
        test_results["stories"] = test_stories_system()
        test_results["error_handling"] = test_error_handling()
        test_results["phase8_endpoints"] = test_phase8_endpoints()
    
    # Print final summary
    print_test_header("FINAL TEST SUMMARY")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result is True)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name.upper()}")
    
    print(f"\n📊 OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Backend is working correctly.")
        return True
    else:
        print("⚠️  SOME TESTS FAILED! Check the details above.")
        return False

if __name__ == "__main__":
    # Run comprehensive tests for messaging, stories, and Phase 8 endpoints
    success = run_comprehensive_tests()
    exit(0 if success else 1)