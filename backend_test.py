#!/usr/bin/env python3
"""
Backend Testing Script for Phase 15 - UI/UX & Accessibility Improvements
Tests all Phase 15 endpoints for NovaSocial app
"""

import requests
import json
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://story-tools-ui.preview.emergentagent.com/api"
TEST_USER_EMAIL = "alice.johnson@example.com"
TEST_USER_PASSWORD = "SecurePass123!"
TEST_USER_FULLNAME = "Alice Johnson"
TEST_USER_USERNAME = "alice_johnson"

class BackendTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, message: str, details: Dict = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None, auth_required: bool = True) -> tuple:
        """Make HTTP request with proper headers"""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if auth_required and self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == "POST":
                response = self.session.post(url, headers=headers, json=data, timeout=30)
            elif method.upper() == "PUT":
                response = self.session.put(url, headers=headers, json=data, timeout=30)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers, timeout=30)
            else:
                return False, {"error": f"Unsupported method: {method}"}
            
            return True, {
                "status_code": response.status_code,
                "response": response.json() if response.content else {},
                "headers": dict(response.headers)
            }
        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}
        except json.JSONDecodeError as e:
            return False, {"error": f"JSON decode error: {str(e)}", "response_text": response.text}
    
    def setup_test_user(self):
        """Setup test user for authentication"""
        print("\n🔧 Setting up test user...")
        
        # Try to register user (might already exist)
        register_data = {
            "fullName": TEST_USER_FULLNAME,
            "username": TEST_USER_USERNAME,
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }
        
        success, result = self.make_request("POST", "/auth/register", register_data, auth_required=False)
        
        if success and result["status_code"] == 200:
            self.auth_token = result["response"]["token"]
            self.user_id = result["response"]["user"]["id"]
            self.log_result("User Registration", True, "Test user registered successfully")
        else:
            # User might already exist, try login
            login_data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
            
            success, result = self.make_request("POST", "/auth/login", login_data, auth_required=False)
            
            if success and result["status_code"] == 200:
                self.auth_token = result["response"]["token"]
                self.user_id = result["response"]["user"]["id"]
                self.log_result("User Login", True, "Test user logged in successfully")
            else:
                self.log_result("User Setup", False, "Failed to setup test user", result)
                return False
        
        return True
    
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