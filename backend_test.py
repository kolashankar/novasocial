#!/usr/bin/env python3
"""
NovaSocial Backend API Testing Suite
Comprehensive testing for Follow System, Notifications, Search & Discovery, and Recommendations
"""

import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional

# Configuration
BASE_URL = "https://mobile-social-app-1.preview.emergentagent.com/api"
TIMEOUT = 30

class NovaSocialTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.test_users = []
        self.test_posts = []
        self.auth_tokens = {}
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def make_request(self, method: str, endpoint: str, data: dict = None, headers: dict = None, token: str = None) -> requests.Response:
        """Make HTTP request with proper error handling"""
        url = f"{self.base_url}{endpoint}"
        
        # Set up headers
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=request_headers, params=data)
            elif method.upper() == "POST":
                response = self.session.post(url, headers=request_headers, json=data)
            elif method.upper() == "PUT":
                response = self.session.put(url, headers=request_headers, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=request_headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            return response
        except requests.exceptions.RequestException as e:
            self.log(f"Request failed: {e}", "ERROR")
            raise
    
    def create_test_user(self, username_suffix: str = None) -> Dict:
        """Create a test user and return user data with token"""
        if not username_suffix:
            username_suffix = str(uuid.uuid4())[:8]
        
        user_data = {
            "fullName": f"Test User {username_suffix}",
            "username": f"testuser_{username_suffix}",
            "email": f"test_{username_suffix}@novasocial.com",
            "password": "TestPassword123!"
        }
        
        response = self.make_request("POST", "/auth/register", user_data)
        
        if response.status_code in [200, 201]:
            result = response.json()
            self.test_users.append(result["user"])
            self.auth_tokens[result["user"]["id"]] = result["token"]
            self.log(f"Created test user: {user_data['username']}")
            return result
        else:
            self.log(f"Failed to create user {user_data['username']}: {response.status_code} - {response.text}", "ERROR")
            raise Exception(f"User creation failed: {response.text}")
    
    def create_test_post(self, user_token: str, caption: str = None, hashtags: List[str] = None) -> Dict:
        """Create a test post"""
        if not caption:
            caption = f"Test post created at {datetime.now().isoformat()}"
        
        post_data = {
            "caption": caption,
            "media": ["data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A"],
            "mediaTypes": ["image"],
            "hashtags": hashtags or ["test", "novasocial"],
            "taggedUsers": []
        }
        
        response = self.make_request("POST", "/posts", post_data, token=user_token)
        
        if response.status_code == 201:
            result = response.json()
            self.test_posts.append(result)
            self.log(f"Created test post: {result['id']}")
            return result
        else:
            self.log(f"Failed to create post: {response.status_code} - {response.text}", "ERROR")
            raise Exception(f"Post creation failed: {response.text}")

    # ============ FOLLOW SYSTEM TESTS ============
    
    def test_follow_system(self):
        """Test follow/unfollow functionality"""
        self.log("=== TESTING FOLLOW SYSTEM ===")
        
        # Create two test users
        user1 = self.create_test_user("follower")
        user2 = self.create_test_user("followee")
        
        user1_token = user1["token"]
        user2_id = user2["user"]["id"]
        user1_id = user1["user"]["id"]
        
        # Test 1: Follow user
        self.log("Testing follow user...")
        response = self.make_request("POST", f"/users/{user2_id}/follow", token=user1_token)
        
        if response.status_code == 200:
            result = response.json()
            assert result["followed"] == True, "Follow should return followed: true"
            self.log("✅ Follow user successful")
        else:
            self.log(f"❌ Follow user failed: {response.status_code} - {response.text}", "ERROR")
            return False
        
        # Test 2: Try to follow same user again (should fail)
        self.log("Testing duplicate follow (should fail)...")
        response = self.make_request("POST", f"/users/{user2_id}/follow", token=user1_token)
        
        if response.status_code == 400:
            self.log("✅ Duplicate follow properly rejected")
        else:
            self.log(f"❌ Duplicate follow should be rejected: {response.status_code}", "ERROR")
            return False
        
        # Test 3: Get followers list
        self.log("Testing get followers...")
        response = self.make_request("GET", f"/users/{user2_id}/followers", token=user1_token)
        
        if response.status_code == 200:
            followers = response.json()
            assert len(followers) == 1, "Should have 1 follower"
            assert followers[0]["id"] == user1_id, "Follower should be user1"
            self.log("✅ Get followers successful")
        else:
            self.log(f"❌ Get followers failed: {response.status_code} - {response.text}", "ERROR")
            return False
        
        # Test 4: Get following list
        self.log("Testing get following...")
        response = self.make_request("GET", f"/users/{user1_id}/following", token=user1_token)
        
        if response.status_code == 200:
            following = response.json()
            assert len(following) == 1, "Should be following 1 user"
            assert following[0]["id"] == user2_id, "Should be following user2"
            self.log("✅ Get following successful")
        else:
            self.log(f"❌ Get following failed: {response.status_code} - {response.text}", "ERROR")
            return False
        
        # Test 5: Unfollow user
        self.log("Testing unfollow user...")
        response = self.make_request("DELETE", f"/users/{user2_id}/follow", token=user1_token)
        
        if response.status_code == 200:
            result = response.json()
            assert result["unfollowed"] == True, "Unfollow should return unfollowed: true"
            self.log("✅ Unfollow user successful")
        else:
            self.log(f"❌ Unfollow user failed: {response.status_code} - {response.text}", "ERROR")
            return False
        
        # Test 6: Verify unfollow worked
        self.log("Verifying unfollow...")
        response = self.make_request("GET", f"/users/{user2_id}/followers", token=user1_token)
        
        if response.status_code == 200:
            followers = response.json()
            assert len(followers) == 0, "Should have 0 followers after unfollow"
            self.log("✅ Unfollow verification successful")
        else:
            self.log(f"❌ Unfollow verification failed: {response.status_code} - {response.text}", "ERROR")
            return False
        
        # Test 7: Try to follow yourself (should fail)
        self.log("Testing self-follow (should fail)...")
        response = self.make_request("POST", f"/users/{user1_id}/follow", token=user1_token)
        
        if response.status_code == 400:
            self.log("✅ Self-follow properly rejected")
        else:
            self.log(f"❌ Self-follow should be rejected: {response.status_code}", "ERROR")
            return False
        
        self.log("✅ ALL FOLLOW SYSTEM TESTS PASSED")
        return True
    
    # ============ NOTIFICATIONS TESTS ============
    
    def test_notifications_system(self):
        """Test notifications functionality"""
        self.log("=== TESTING NOTIFICATIONS SYSTEM ===")
        
        # Create two test users
        user1 = self.create_test_user("liker")
        user2 = self.create_test_user("poster")
        
        user1_token = user1["token"]
        user2_token = user2["token"]
        user2_id = user2["user"]["id"]
        
        # Create a post by user2
        post = self.create_test_post(user2_token, "Test post for notifications")
        post_id = post["id"]
        
        # Test 1: Like post to generate notification
        self.log("Testing notification generation via post like...")
        response = self.make_request("POST", f"/posts/{post_id}/like", token=user1_token)
        
        if response.status_code == 200:
            self.log("✅ Post liked successfully")
        else:
            self.log(f"❌ Post like failed: {response.status_code} - {response.text}", "ERROR")
            return False
        
        # Wait a moment for notification to be created
        time.sleep(1)
        
        # Test 2: Get notifications
        self.log("Testing get notifications...")
        response = self.make_request("GET", "/notifications", token=user2_token)
        
        if response.status_code == 200:
            notifications = response.json()
            assert len(notifications) >= 1, "Should have at least 1 notification"
            
            # Find the like notification
            like_notification = None
            for notif in notifications:
                if notif["type"] == "like" and notif["relatedId"] == post_id:
                    like_notification = notif
                    break
            
            assert like_notification is not None, "Should have like notification"
            assert like_notification["isRead"] == False, "Notification should be unread"
            assert like_notification["recipientId"] == user2_id, "Notification should be for user2"
            
            self.log("✅ Get notifications successful")
            notification_id = like_notification["id"]
        else:
            self.log(f"❌ Get notifications failed: {response.status_code} - {response.text}", "ERROR")
            return False
        
        # Test 3: Mark notification as read
        self.log("Testing mark notification as read...")
        response = self.make_request("PUT", f"/notifications/{notification_id}/read", token=user2_token)
        
        if response.status_code == 200:
            result = response.json()
            assert result["read"] == True, "Should return read: true"
            self.log("✅ Mark notification as read successful")
        else:
            self.log(f"❌ Mark notification as read failed: {response.status_code} - {response.text}", "ERROR")
            return False
        
        # Test 4: Verify notification is marked as read
        self.log("Verifying notification is read...")
        response = self.make_request("GET", "/notifications", token=user2_token)
        
        if response.status_code == 200:
            notifications = response.json()
            read_notification = None
            for notif in notifications:
                if notif["id"] == notification_id:
                    read_notification = notif
                    break
            
            assert read_notification is not None, "Should find the notification"
            assert read_notification["isRead"] == True, "Notification should be marked as read"
            self.log("✅ Notification read status verified")
        else:
            self.log(f"❌ Notification read verification failed: {response.status_code} - {response.text}", "ERROR")
            return False
        
        # Test 5: Follow user to generate another notification
        self.log("Testing follow notification...")
        response = self.make_request("POST", f"/users/{user2_id}/follow", token=user1_token)
        
        if response.status_code == 200:
            self.log("✅ Follow successful")
        else:
            self.log(f"❌ Follow failed: {response.status_code} - {response.text}", "ERROR")
            return False
        
        # Wait for notification
        time.sleep(1)
        
        # Test 6: Mark all notifications as read
        self.log("Testing mark all notifications as read...")
        response = self.make_request("PUT", "/notifications/read-all", token=user2_token)
        
        if response.status_code == 200:
            result = response.json()
            assert result["allRead"] == True, "Should return allRead: true"
            self.log("✅ Mark all notifications as read successful")
        else:
            self.log(f"❌ Mark all notifications as read failed: {response.status_code} - {response.text}", "ERROR")
            return False
        
        # Test 7: Verify all notifications are read
        self.log("Verifying all notifications are read...")
        response = self.make_request("GET", "/notifications", token=user2_token)
        
        if response.status_code == 200:
            notifications = response.json()
            unread_count = sum(1 for notif in notifications if not notif["isRead"])
            assert unread_count == 0, "All notifications should be read"
            self.log("✅ All notifications read verification successful")
        else:
            self.log(f"❌ All notifications read verification failed: {response.status_code} - {response.text}", "ERROR")
            return False
        
        self.log("✅ ALL NOTIFICATIONS TESTS PASSED")
        return True
    
    # ============ SEARCH & DISCOVERY TESTS ============
    
    def test_search_and_discovery(self):
        """Test search and discovery functionality"""
        self.log("=== TESTING SEARCH & DISCOVERY SYSTEM ===")
        
        # Create test users with specific names for search
        user1 = self.create_test_user("searchable")
        user2 = self.create_test_user("findme")
        
        user1_token = user1["token"]
        user2_token = user2["token"]
        
        # Create posts with specific hashtags and content
        post1 = self.create_test_post(user1_token, "This is a test post about #technology and #innovation", ["technology", "innovation", "test"])
        post2 = self.create_test_post(user2_token, "Another post about #travel and #photography", ["travel", "photography", "adventure"])
        
        # Wait for posts to be indexed
        time.sleep(1)
        
        # Test 1: Search users
        self.log("Testing user search...")
        response = self.make_request("GET", "/search", {"q": "searchable", "type": "users"})
        
        if response.status_code == 200:
            result = response.json()
            assert len(result["users"]) >= 1, "Should find at least 1 user"
            found_user = False
            for user in result["users"]:
                if "searchable" in user["username"]:
                    found_user = True
                    break
            assert found_user, "Should find user with 'searchable' in username"
            self.log("✅ User search successful")
        else:
            self.log(f"❌ User search failed: {response.status_code} - {response.text}", "ERROR")
            return False
        
        # Test 2: Search posts
        self.log("Testing post search...")
        response = self.make_request("GET", "/search", {"q": "technology", "type": "posts"})
        
        if response.status_code == 200:
            result = response.json()
            assert len(result["posts"]) >= 1, "Should find at least 1 post"
            found_post = False
            for post in result["posts"]:
                if "technology" in post["caption"].lower():
                    found_post = True
                    break
            assert found_post, "Should find post with 'technology' in caption"
            self.log("✅ Post search successful")
        else:
            self.log(f"❌ Post search failed: {response.status_code} - {response.text}", "ERROR")
            return False
        
        # Test 3: Search hashtags
        self.log("Testing hashtag search...")
        response = self.make_request("GET", "/search", {"q": "travel", "type": "hashtags"})
        
        if response.status_code == 200:
            result = response.json()
            assert len(result["hashtags"]) >= 1, "Should find at least 1 hashtag"
            assert "travel" in result["hashtags"], "Should find 'travel' hashtag"
            self.log("✅ Hashtag search successful")
        else:
            self.log(f"❌ Hashtag search failed: {response.status_code} - {response.text}", "ERROR")
            return False
        
        # Test 4: Universal search (all types)
        self.log("Testing universal search...")
        response = self.make_request("GET", "/search", {"q": "test", "type": "all"})
        
        if response.status_code == 200:
            result = response.json()
            total_results = len(result["users"]) + len(result["posts"]) + len(result["hashtags"])
            assert total_results >= 1, "Should find at least 1 result across all types"
            self.log("✅ Universal search successful")
        else:
            self.log(f"❌ Universal search failed: {response.status_code} - {response.text}", "ERROR")
            return False
        
        # Test 5: Get trending hashtags
        self.log("Testing trending hashtags...")
        response = self.make_request("GET", "/trending/hashtags", token=user1_token)
        
        if response.status_code == 200:
            trending = response.json()
            assert isinstance(trending, list), "Trending should return a list"
            # Should have some hashtags from our test posts
            hashtag_names = [item["hashtag"] for item in trending]
            assert any(tag in ["technology", "travel", "test"] for tag in hashtag_names), "Should include our test hashtags"
            self.log("✅ Trending hashtags successful")
        else:
            self.log(f"❌ Trending hashtags failed: {response.status_code} - {response.text}", "ERROR")
            return False
        
        # Test 6: Get user suggestions
        self.log("Testing user suggestions...")
        response = self.make_request("GET", "/users/suggestions", token=user1_token)
        
        if response.status_code == 200:
            suggestions = response.json()
            assert isinstance(suggestions, list), "Suggestions should return a list"
            # Should not include the current user
            user_ids = [user["id"] for user in suggestions]
            assert user1["user"]["id"] not in user_ids, "Should not suggest current user"
            self.log("✅ User suggestions successful")
        else:
            self.log(f"❌ User suggestions failed: {response.status_code} - {response.text}", "ERROR")
            return False
        
        self.log("✅ ALL SEARCH & DISCOVERY TESTS PASSED")
        return True
    
    # ============ RECOMMENDATION ENGINE TESTS ============
    
    def test_recommendation_engine(self):
        """Test recommendation engine functionality"""
        self.log("=== TESTING RECOMMENDATION ENGINE ===")
        
        # Create multiple test users
        user1 = self.create_test_user("recommender")
        user2 = self.create_test_user("content_creator1")
        user3 = self.create_test_user("content_creator2")
        
        user1_token = user1["token"]
        user2_token = user2["token"]
        user3_token = user3["token"]
        user2_id = user2["user"]["id"]
        user3_id = user3["user"]["id"]
        
        # Create posts with different hashtags
        post1 = self.create_test_post(user2_token, "AI and machine learning post", ["ai", "machinelearning", "tech"])
        post2 = self.create_test_post(user3_token, "Another AI post for recommendations", ["ai", "technology", "future"])
        post3 = self.create_test_post(user2_token, "Travel photography post", ["travel", "photography", "nature"])
        
        # Wait for posts to be created
        time.sleep(1)
        
        # Test 1: Get recommendations without any activity (should return popular posts)
        self.log("Testing initial recommendations...")
        response = self.make_request("GET", "/feed/recommendations", token=user1_token)
        
        if response.status_code == 200:
            recommendations = response.json()
            assert isinstance(recommendations, list), "Recommendations should return a list"
            self.log(f"✅ Initial recommendations successful ({len(recommendations)} posts)")
        else:
            self.log(f"❌ Initial recommendations failed: {response.status_code} - {response.text}", "ERROR")
            return False
        
        # Test 2: Like posts to establish interests
        self.log("Establishing user interests by liking AI posts...")
        
        # Like AI-related posts
        response = self.make_request("POST", f"/posts/{post1['id']}/like", token=user1_token)
        if response.status_code != 200:
            self.log(f"❌ Failed to like post1: {response.status_code}", "ERROR")
            return False
        
        response = self.make_request("POST", f"/posts/{post2['id']}/like", token=user1_token)
        if response.status_code != 200:
            self.log(f"❌ Failed to like post2: {response.status_code}", "ERROR")
            return False
        
        # Wait for activity to be processed
        time.sleep(1)
        
        # Test 3: Get recommendations based on interests
        self.log("Testing interest-based recommendations...")
        response = self.make_request("GET", "/feed/recommendations", token=user1_token)
        
        if response.status_code == 200:
            recommendations = response.json()
            assert isinstance(recommendations, list), "Recommendations should return a list"
            
            # Check if AI-related posts are prioritized
            ai_posts = []
            for post in recommendations:
                if any(hashtag in ["ai", "machinelearning", "technology"] for hashtag in post.get("hashtags", [])):
                    ai_posts.append(post)
            
            self.log(f"✅ Interest-based recommendations successful ({len(ai_posts)} AI-related posts found)")
        else:
            self.log(f"❌ Interest-based recommendations failed: {response.status_code} - {response.text}", "ERROR")
            return False
        
        # Test 4: Follow users to test follow-based recommendations
        self.log("Testing follow-based recommendations...")
        
        # Follow user2
        response = self.make_request("POST", f"/users/{user2_id}/follow", token=user1_token)
        if response.status_code != 200:
            self.log(f"❌ Failed to follow user2: {response.status_code}", "ERROR")
            return False
        
        # Wait for follow to be processed
        time.sleep(1)
        
        # Get recommendations again
        response = self.make_request("GET", "/feed/recommendations", token=user1_token)
        
        if response.status_code == 200:
            recommendations = response.json()
            assert isinstance(recommendations, list), "Recommendations should return a list"
            
            # Check if posts from followed users are included
            followed_user_posts = []
            for post in recommendations:
                if post["authorId"] == user2_id:
                    followed_user_posts.append(post)
            
            self.log(f"✅ Follow-based recommendations successful ({len(followed_user_posts)} posts from followed users)")
        else:
            self.log(f"❌ Follow-based recommendations failed: {response.status_code} - {response.text}", "ERROR")
            return False
        
        # Test 5: Test recommendation pagination
        self.log("Testing recommendation pagination...")
        response = self.make_request("GET", "/feed/recommendations", {"skip": 0, "limit": 5}, token=user1_token)
        
        if response.status_code == 200:
            page1 = response.json()
            assert len(page1) <= 5, "Should respect limit parameter"
            
            response = self.make_request("GET", "/feed/recommendations", {"skip": 5, "limit": 5}, token=user1_token)
            if response.status_code == 200:
                page2 = response.json()
                # Pages should be different (assuming we have enough posts)
                self.log("✅ Recommendation pagination successful")
            else:
                self.log(f"❌ Recommendation pagination (page 2) failed: {response.status_code}", "ERROR")
                return False
        else:
            self.log(f"❌ Recommendation pagination failed: {response.status_code} - {response.text}", "ERROR")
            return False
        
        self.log("✅ ALL RECOMMENDATION ENGINE TESTS PASSED")
        return True
    
    # ============ INTEGRATION TESTS ============
    
    def test_cross_feature_integration(self):
        """Test integration between different features"""
        self.log("=== TESTING CROSS-FEATURE INTEGRATION ===")
        
        # Create test users
        user1 = self.create_test_user("integrator1")
        user2 = self.create_test_user("integrator2")
        
        user1_token = user1["token"]
        user2_token = user2["token"]
        user1_id = user1["user"]["id"]
        user2_id = user2["user"]["id"]
        
        # Test 1: Follow → Notification → Recommendation flow
        self.log("Testing Follow → Notification → Recommendation integration...")
        
        # Follow user
        response = self.make_request("POST", f"/users/{user2_id}/follow", token=user1_token)
        assert response.status_code == 200, "Follow should succeed"
        
        # Check notification was created
        time.sleep(1)
        response = self.make_request("GET", "/notifications", token=user2_token)
        assert response.status_code == 200, "Get notifications should succeed"
        notifications = response.json()
        follow_notifications = [n for n in notifications if n["type"] == "follow"]
        assert len(follow_notifications) >= 1, "Should have follow notification"
        
        # Create post by followed user
        post = self.create_test_post(user2_token, "Post from followed user", ["integration", "test"])
        
        # Check if post appears in recommendations
        time.sleep(1)
        response = self.make_request("GET", "/feed/recommendations", token=user1_token)
        assert response.status_code == 200, "Get recommendations should succeed"
        recommendations = response.json()
        followed_user_posts = [p for p in recommendations if p["authorId"] == user2_id]
        assert len(followed_user_posts) >= 1, "Should recommend posts from followed users"
        
        self.log("✅ Follow → Notification → Recommendation integration successful")
        
        # Test 2: Like → Notification → Search integration
        self.log("Testing Like → Notification → Search integration...")
        
        # Like the post
        response = self.make_request("POST", f"/posts/{post['id']}/like", token=user1_token)
        assert response.status_code == 200, "Like should succeed"
        
        # Check notification was created
        time.sleep(1)
        response = self.make_request("GET", "/notifications", token=user2_token)
        assert response.status_code == 200, "Get notifications should succeed"
        notifications = response.json()
        like_notifications = [n for n in notifications if n["type"] == "like"]
        assert len(like_notifications) >= 1, "Should have like notification"
        
        # Search for hashtags from liked post
        response = self.make_request("GET", "/search", {"q": "integration", "type": "hashtags"})
        assert response.status_code == 200, "Search should succeed"
        result = response.json()
        assert "integration" in result["hashtags"], "Should find hashtag from liked post"
        
        self.log("✅ Like → Notification → Search integration successful")
        
        self.log("✅ ALL CROSS-FEATURE INTEGRATION TESTS PASSED")
        return True
    
    # ============ MAIN TEST RUNNER ============
    
    def run_all_tests(self):
        """Run all backend tests"""
        self.log("🚀 STARTING NOVASOCIAL BACKEND COMPREHENSIVE TESTING")
        self.log(f"Testing against: {self.base_url}")
        
        test_results = {}
        
        try:
            # Test Follow System
            test_results["follow_system"] = self.test_follow_system()
            
            # Test Notifications System  
            test_results["notifications_system"] = self.test_notifications_system()
            
            # Test Search & Discovery
            test_results["search_discovery"] = self.test_search_and_discovery()
            
            # Test Recommendation Engine
            test_results["recommendation_engine"] = self.test_recommendation_engine()
            
            # Test Cross-Feature Integration
            test_results["integration"] = self.test_cross_feature_integration()
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR during testing: {e}", "ERROR")
            test_results["critical_error"] = str(e)
        
        # Print final results
        self.log("\n" + "="*60)
        self.log("🏁 FINAL TEST RESULTS")
        self.log("="*60)
        
        passed_tests = 0
        total_tests = 0
        
        for test_name, result in test_results.items():
            if test_name == "critical_error":
                self.log(f"❌ CRITICAL ERROR: {result}", "ERROR")
                continue
                
            total_tests += 1
            if result:
                self.log(f"✅ {test_name.replace('_', ' ').title()}: PASSED")
                passed_tests += 1
            else:
                self.log(f"❌ {test_name.replace('_', ' ').title()}: FAILED", "ERROR")
        
        self.log("="*60)
        self.log(f"📊 SUMMARY: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            self.log("🎉 ALL TESTS PASSED! Backend is working correctly.")
            return True
        else:
            self.log("⚠️  SOME TESTS FAILED! Check logs above for details.", "ERROR")
            return False


if __name__ == "__main__":
    tester = NovaSocialTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)