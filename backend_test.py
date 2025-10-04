#!/usr/bin/env python3
"""
NovaSocial Backend Authentication System Tests
Tests all authentication endpoints with comprehensive validation
"""

import requests
import json
import base64
from datetime import datetime
import uuid

# Backend URL from frontend/.env
BACKEND_URL = "https://chatwave-social-1.preview.emergentagent.com/api"

class AuthenticationTester:
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

if __name__ == "__main__":
    tester = AuthenticationTester()
    tester.run_all_tests()