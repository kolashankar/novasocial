#!/usr/bin/env python3
"""
Backend Testing for Phase 16 & 17 - Social Media App
Testing newly implemented Posting & Media Enhancements and Story & Creative Tools endpoints
"""

import requests
import json
import base64
import uuid
from datetime import datetime, timedelta
import os
import sys

# Get backend URL from frontend .env
BACKEND_URL = "https://social-stories-hub-1.preview.emergentagent.com/api"

# Test data
TEST_USER_DATA = {
    "fullName": "Test User Phase16",
    "username": "testuser_phase16",
    "email": "testuser_phase16@example.com",
    "password": "testpassword123"
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
    
    def test_support_system(self):
        """Test support system endpoints"""
        print("\n📞 Testing Support System Endpoints...")
        
        # Test 1: Create support ticket - Bug report
        ticket_data = {
            "category": "bug",
            "subject": "App crashes when uploading large images",
            "description": "The app consistently crashes when I try to upload images larger than 10MB. This happens on both iOS and Android devices. Steps to reproduce: 1. Open camera 2. Take high-res photo 3. Try to post 4. App crashes",
            "attachments": []
        }
        
        success, result = self.make_request("POST", "/support/tickets", ticket_data)
        if success and result["status_code"] == 200:
            ticket_id = result["response"].get("ticketId")
            self.log_result("Create Support Ticket (Bug)", True, f"Bug report ticket created: {ticket_id}")
        else:
            self.log_result("Create Support Ticket (Bug)", False, "Failed to create bug report ticket", result)
        
        # Test 2: Create support ticket - Harassment report
        harassment_ticket = {
            "category": "harassment",
            "subject": "User sending inappropriate messages",
            "description": "User @baduser123 has been sending me threatening messages and inappropriate content. I have screenshots as evidence.",
            "attachments": ["data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="]
        }
        
        success, result = self.make_request("POST", "/support/tickets", harassment_ticket)
        if success and result["status_code"] == 200:
            self.log_result("Create Support Ticket (Harassment)", True, "Harassment report ticket created")
        else:
            self.log_result("Create Support Ticket (Harassment)", False, "Failed to create harassment ticket", result)
        
        # Test 3: Create support ticket - Technical issue
        tech_ticket = {
            "category": "technical",
            "subject": "Push notifications not working",
            "description": "I'm not receiving any push notifications even though they're enabled in settings. I've tried restarting the app and my phone.",
            "attachments": []
        }
        
        success, result = self.make_request("POST", "/support/tickets", tech_ticket)
        if success and result["status_code"] == 200:
            self.log_result("Create Support Ticket (Technical)", True, "Technical support ticket created")
        else:
            self.log_result("Create Support Ticket (Technical)", False, "Failed to create technical ticket", result)
        
        # Test 4: Get user support tickets
        success, result = self.make_request("GET", "/support/tickets")
        if success and result["status_code"] == 200:
            tickets = result["response"]
            if isinstance(tickets, list) and len(tickets) >= 3:
                self.log_result("Get User Support Tickets", True, f"Retrieved {len(tickets)} support tickets")
            else:
                self.log_result("Get User Support Tickets", False, f"Expected at least 3 tickets, got {len(tickets) if isinstance(tickets, list) else 0}")
        else:
            self.log_result("Get User Support Tickets", False, "Failed to retrieve support tickets", result)
        
        # Test 5: Get FAQ entries
        success, result = self.make_request("GET", "/support/faq", auth_required=False)
        if success and result["status_code"] == 200:
            faqs = result["response"]
            if isinstance(faqs, list) and len(faqs) > 0:
                self.log_result("Get FAQ Entries", True, f"Retrieved {len(faqs)} FAQ entries")
            else:
                self.log_result("Get FAQ Entries", False, "No FAQ entries found")
        else:
            self.log_result("Get FAQ Entries", False, "Failed to retrieve FAQ entries", result)
        
        # Test 6: Search FAQ - password query
        success, result = self.make_request("GET", "/support/faq/search", params={"q": "password"}, auth_required=False)
        if success and result["status_code"] == 200:
            search_results = result["response"].get("results", [])
            if len(search_results) > 0:
                self.log_result("Search FAQ (password)", True, f"Found {len(search_results)} FAQ entries for 'password'")
            else:
                self.log_result("Search FAQ (password)", True, "No FAQ entries found for 'password' (expected)")
        else:
            self.log_result("Search FAQ (password)", False, "Failed to search FAQ", result)
        
        # Test 7: Search FAQ - privacy query
        success, result = self.make_request("GET", "/support/faq/search", params={"q": "private"}, auth_required=False)
        if success and result["status_code"] == 200:
            search_results = result["response"].get("results", [])
            self.log_result("Search FAQ (private)", True, f"Found {len(search_results)} FAQ entries for 'private'")
        else:
            self.log_result("Search FAQ (private)", False, "Failed to search FAQ for 'private'", result)
    
    def test_app_information(self):
        """Test app information endpoint"""
        print("\n📱 Testing App Information Endpoint...")
        
        success, result = self.make_request("GET", "/app/info", auth_required=False)
        if success and result["status_code"] == 200:
            app_info = result["response"]
            required_fields = ["version", "buildNumber", "platform", "features", "supportEmail"]
            missing_fields = [field for field in required_fields if field not in app_info]
            
            if not missing_fields:
                features = app_info.get("features", [])
                self.log_result("Get App Info", True, f"App info retrieved with {len(features)} features")
            else:
                self.log_result("Get App Info", False, f"Missing required fields: {missing_fields}", app_info)
        else:
            self.log_result("Get App Info", False, "Failed to retrieve app information", result)
    
    def test_theme_settings(self):
        """Test theme settings endpoints"""
        print("\n🎨 Testing Theme Settings Endpoints...")
        
        # Test 1: Get theme settings (should return defaults)
        success, result = self.make_request("GET", "/settings/theme")
        if success and result["status_code"] == 200:
            theme_settings = result["response"]
            required_fields = ["themeMode", "primaryColor", "accentColor", "fontSize", "fontFamily"]
            missing_fields = [field for field in required_fields if field not in theme_settings]
            
            if not missing_fields:
                self.log_result("Get Theme Settings", True, f"Theme settings retrieved: {theme_settings.get('themeMode', 'unknown')} mode")
            else:
                self.log_result("Get Theme Settings", False, f"Missing required fields: {missing_fields}", theme_settings)
        else:
            self.log_result("Get Theme Settings", False, "Failed to retrieve theme settings", result)
        
        # Test 2: Update theme settings - Dark mode
        dark_theme_update = {
            "themeMode": "dark",
            "primaryColor": "#1E1E1E",
            "accentColor": "#BB86FC",
            "fontSize": "large",
            "highContrast": True,
            "reduceMotion": False
        }
        
        success, result = self.make_request("PUT", "/settings/theme", dark_theme_update)
        if success and result["status_code"] == 200:
            self.log_result("Update Theme Settings (Dark)", True, "Dark theme settings updated successfully")
        else:
            self.log_result("Update Theme Settings (Dark)", False, "Failed to update dark theme settings", result)
        
        # Test 3: Update theme settings - Light mode with accessibility
        light_theme_update = {
            "themeMode": "light",
            "primaryColor": "#007AFF",
            "accentColor": "#FF3B30",
            "fontSize": "medium",
            "fontFamily": "system",
            "highContrast": False,
            "reduceMotion": True,
            "colorBlindMode": "deuteranopia"
        }
        
        success, result = self.make_request("PUT", "/settings/theme", light_theme_update)
        if success and result["status_code"] == 200:
            self.log_result("Update Theme Settings (Light + Accessibility)", True, "Light theme with accessibility settings updated")
        else:
            self.log_result("Update Theme Settings (Light + Accessibility)", False, "Failed to update light theme settings", result)
        
        # Test 4: Verify theme settings were updated
        success, result = self.make_request("GET", "/settings/theme")
        if success and result["status_code"] == 200:
            theme_settings = result["response"]
            if (theme_settings.get("themeMode") == "light" and 
                theme_settings.get("reduceMotion") == True and
                theme_settings.get("colorBlindMode") == "deuteranopia"):
                self.log_result("Verify Theme Settings Update", True, "Theme settings correctly updated and persisted")
            else:
                self.log_result("Verify Theme Settings Update", False, "Theme settings not properly updated", theme_settings)
        else:
            self.log_result("Verify Theme Settings Update", False, "Failed to verify theme settings update", result)
    
    def test_authentication_signout(self):
        """Test authentication sign-out endpoint"""
        print("\n🔐 Testing Authentication Sign-out...")
        
        success, result = self.make_request("POST", "/auth/sign-out")
        if success and result["status_code"] == 200:
            response_data = result["response"]
            if response_data.get("success") == True:
                self.log_result("Sign Out", True, "User signed out successfully with session cleanup")
            else:
                self.log_result("Sign Out", False, "Sign out response missing success flag", response_data)
        else:
            self.log_result("Sign Out", False, "Failed to sign out user", result)
    
    def test_content_reporting(self):
        """Test content reporting endpoint"""
        print("\n🚨 Testing Content Reporting...")
        
        # First, re-authenticate since we signed out
        if not self.setup_test_user():
            self.log_result("Re-authentication for Content Reporting", False, "Failed to re-authenticate")
            return
        
        # Test 1: Report a post for spam
        post_report = {
            "contentType": "post",
            "contentId": "test_post_123",
            "reason": "spam",
            "description": "This post contains spam content promoting fake products and services. It's clearly not genuine content."
        }
        
        success, result = self.make_request("POST", "/reports/content", post_report)
        if success and result["status_code"] == 200:
            report_id = result["response"].get("reportId")
            self.log_result("Report Content (Post - Spam)", True, f"Post reported for spam: {report_id}")
        else:
            self.log_result("Report Content (Post - Spam)", False, "Failed to report post for spam", result)
        
        # Test 2: Report a comment for harassment
        comment_report = {
            "contentType": "comment",
            "contentId": "test_comment_456",
            "reason": "harassment",
            "description": "This comment contains threatening language and personal attacks against other users."
        }
        
        success, result = self.make_request("POST", "/reports/content", comment_report)
        if success and result["status_code"] == 200:
            self.log_result("Report Content (Comment - Harassment)", True, "Comment reported for harassment")
        else:
            self.log_result("Report Content (Comment - Harassment)", False, "Failed to report comment for harassment", result)
        
        # Test 3: Report a user for inappropriate behavior
        user_report = {
            "contentType": "user",
            "contentId": "test_user_789",
            "reason": "inappropriate",
            "description": "This user has been posting inappropriate content and sending unwanted messages to multiple users."
        }
        
        success, result = self.make_request("POST", "/reports/content", user_report)
        if success and result["status_code"] == 200:
            self.log_result("Report Content (User - Inappropriate)", True, "User reported for inappropriate behavior")
        else:
            self.log_result("Report Content (User - Inappropriate)", False, "Failed to report user", result)
        
        # Test 4: Report a message for violence
        message_report = {
            "contentType": "message",
            "contentId": "test_message_101",
            "reason": "violence",
            "description": "This message contains violent threats and graphic content that violates community guidelines."
        }
        
        success, result = self.make_request("POST", "/reports/content", message_report)
        if success and result["status_code"] == 200:
            self.log_result("Report Content (Message - Violence)", True, "Message reported for violence")
        else:
            self.log_result("Report Content (Message - Violence)", False, "Failed to report message for violence", result)
    
    def run_all_tests(self):
        """Run all Phase 15 endpoint tests"""
        print("🚀 Starting Phase 15 Backend Endpoint Testing...")
        print(f"Backend URL: {self.base_url}")
        print("=" * 60)
        
        # Setup test user
        if not self.setup_test_user():
            print("❌ Failed to setup test user. Aborting tests.")
            return False
        
        # Run all test suites
        self.test_support_system()
        self.test_app_information()
        self.test_theme_settings()
        self.test_authentication_signout()
        self.test_content_reporting()
        
        # Print summary
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)

def main():
    """Main function to run the tests"""
    tester = BackendTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()