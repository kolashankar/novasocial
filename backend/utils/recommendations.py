from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import math
import logging
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Advanced recommendation system for posts, users, and content"""
    
    def __init__(self, db):
        self.db = db
    
    async def get_post_recommendations(
        self, 
        user_id: str, 
        limit: int = 20,
        exclude_ids: List[str] = None
    ) -> List[Dict]:
        """Get personalized post recommendations for user"""
        try:
            exclude_ids = exclude_ids or []
            
            # Get user's interests and activity
            user_profile = await self._get_user_profile(user_id)
            user_activity = await self._get_user_activity(user_id)
            
            # Get candidate posts
            candidate_posts = await self._get_candidate_posts(user_id, exclude_ids, limit * 3)
            
            # Score and rank posts
            scored_posts = []
            for post in candidate_posts:
                score = await self._calculate_post_score(user_id, post, user_profile, user_activity)
                scored_posts.append((post, score))
            
            # Sort by score and return top posts
            scored_posts.sort(key=lambda x: x[1], reverse=True)
            return [post for post, score in scored_posts[:limit]]
            
        except Exception as e:
            logger.error(f"Error getting post recommendations: {e}")
            return []
    
    async def get_user_recommendations(
        self, 
        user_id: str, 
        limit: int = 20,
        exclude_ids: List[str] = None
    ) -> List[Dict]:
        """Get user recommendations (people to follow)"""
        try:
            exclude_ids = exclude_ids or []
            
            # Get users current user is already following
            following = await self._get_user_following(user_id)
            exclude_ids.extend(following)
            exclude_ids.append(user_id)  # Don't recommend self
            
            # Get candidate users
            candidate_users = await self._get_candidate_users(user_id, exclude_ids, limit * 2)
            
            # Score and rank users
            scored_users = []
            for user in candidate_users:
                score = await self._calculate_user_score(user_id, user)
                scored_users.append((user, score))
            
            # Sort by score and return top users
            scored_users.sort(key=lambda x: x[1], reverse=True)
            return [user for user, score in scored_users[:limit]]
            
        except Exception as e:
            logger.error(f"Error getting user recommendations: {e}")
            return []
    
    async def get_hashtag_recommendations(
        self, 
        user_id: str, 
        limit: int = 10
    ) -> List[str]:
        """Get trending hashtag recommendations"""
        try:
            # Get user's recently used hashtags
            user_hashtags = await self._get_user_hashtags(user_id)
            
            # Get trending hashtags
            trending_hashtags = await self._get_trending_hashtags(limit * 2)
            
            # Get related hashtags based on user's interests
            related_hashtags = await self._get_related_hashtags(user_hashtags, limit)
            
            # Combine and deduplicate
            all_hashtags = list(set(trending_hashtags + related_hashtags))
            
            # Score hashtags
            scored_hashtags = []
            for hashtag in all_hashtags:
                score = await self._calculate_hashtag_score(user_id, hashtag, user_hashtags)
                scored_hashtags.append((hashtag, score))
            
            # Sort and return top hashtags
            scored_hashtags.sort(key=lambda x: x[1], reverse=True)
            return [hashtag for hashtag, score in scored_hashtags[:limit]]
            
        except Exception as e:
            logger.error(f"Error getting hashtag recommendations: {e}")
            return []
    
    async def _get_user_profile(self, user_id: str) -> Dict:
        """Get user profile with interests and preferences"""
        user = await self.db.users.find_one({"id": user_id})
        if not user:
            return {}
        
        # Extract interests from user settings or posts
        interests = user.get("interests", [])
        if not interests:
            # Infer interests from user's posts and activity
            interests = await self._infer_user_interests(user_id)
        
        return {
            "interests": interests,
            "createdAt": user.get("createdAt"),
            "followersCount": await self._get_followers_count(user_id),
            "postsCount": await self._get_posts_count(user_id)
        }
    
    async def _get_user_activity(self, user_id: str) -> Dict:
        """Get user's recent activity patterns"""
        # Get recent likes, comments, shares
        recent_likes = await self._get_recent_likes(user_id, days=30)
        recent_comments = await self._get_recent_comments(user_id, days=30)
        
        return {
            "recent_likes": recent_likes,
            "recent_comments": recent_comments,
            "activity_score": len(recent_likes) + len(recent_comments)
        }
    
    async def _get_candidate_posts(self, user_id: str, exclude_ids: List[str], limit: int) -> List[Dict]:
        """Get candidate posts for recommendation"""
        # Get posts from followed users (higher priority)
        following_ids = await self._get_user_following(user_id)
        
        candidate_posts = []
        
        # Posts from followed users
        if following_ids:
            following_posts = await self.db.posts.find({
                "authorId": {"$in": following_ids},
                "id": {"$nin": exclude_ids}
            }).sort("createdAt", -1).limit(limit // 2).to_list(length=limit // 2)
            candidate_posts.extend(following_posts)
        
        # Trending posts (posts with high engagement)
        trending_posts = await self.db.posts.find({
            "id": {"$nin": exclude_ids + [p["id"] for p in candidate_posts]},
            "likesCount": {"$gte": 5}  # Minimum engagement threshold
        }).sort([
            ("likesCount", -1),
            ("createdAt", -1)
        ]).limit(limit // 2).to_list(length=limit // 2)
        candidate_posts.extend(trending_posts)
        
        return candidate_posts
    
    async def _calculate_post_score(self, user_id: str, post: Dict, user_profile: Dict, user_activity: Dict) -> float:
        """Calculate recommendation score for a post"""
        score = 0.0
        
        # Recency factor (newer posts get higher scores)
        days_old = (datetime.utcnow() - post["createdAt"]).days
        recency_score = max(0, 1 - (days_old / 30))  # Decay over 30 days
        score += recency_score * 0.2
        
        # Engagement factor
        engagement_score = (post.get("likesCount", 0) + post.get("commentsCount", 0) * 2) / 10
        engagement_score = min(engagement_score, 1.0)  # Cap at 1.0
        score += engagement_score * 0.3
        
        # Interest matching
        user_interests = user_profile.get("interests", [])
        post_hashtags = post.get("hashtags", [])
        
        if user_interests and post_hashtags:
            interest_matches = len(set(user_interests) & set(post_hashtags))
            interest_score = min(interest_matches / len(user_interests), 1.0)
            score += interest_score * 0.3
        
        # Author popularity
        author_followers = await self._get_followers_count(post["authorId"])
        popularity_score = min(math.log(author_followers + 1) / math.log(1000), 1.0)
        score += popularity_score * 0.2
        
        return score
    
    async def _get_candidate_users(self, user_id: str, exclude_ids: List[str], limit: int) -> List[Dict]:
        """Get candidate users for recommendation"""
        # Get users with mutual follows (friends of friends)
        mutual_connections = await self._get_mutual_connections(user_id, limit // 2)
        
        # Get popular users
        popular_users = await self.db.users.find({
            "id": {"$nin": exclude_ids + [u["id"] for u in mutual_connections]}
        }).limit(limit // 2).to_list(length=limit // 2)
        
        return mutual_connections + popular_users
    
    async def _calculate_user_score(self, user_id: str, candidate_user: Dict) -> float:
        """Calculate recommendation score for a user"""
        score = 0.0
        
        # Mutual connections
        mutual_count = await self._get_mutual_followers_count(user_id, candidate_user["id"])
        mutual_score = min(mutual_count / 5, 1.0)  # Max score when 5+ mutual connections
        score += mutual_score * 0.4
        
        # User activity (recent posts)
        recent_posts_count = await self._get_recent_posts_count(candidate_user["id"], days=30)
        activity_score = min(recent_posts_count / 10, 1.0)  # Max score at 10+ posts
        score += activity_score * 0.3
        
        # Profile completeness
        completeness_score = self._calculate_profile_completeness(candidate_user)
        score += completeness_score * 0.2
        
        # Similar interests (if available)
        interest_similarity = await self._calculate_interest_similarity(user_id, candidate_user["id"])
        score += interest_similarity * 0.1
        
        return score
    
    async def _calculate_hashtag_score(self, user_id: str, hashtag: str, user_hashtags: List[str]) -> float:
        """Calculate recommendation score for a hashtag"""
        score = 0.0
        
        # Trending factor
        hashtag_usage = await self._get_hashtag_usage_count(hashtag, days=7)
        trending_score = min(hashtag_usage / 50, 1.0)  # Max score at 50+ uses
        score += trending_score * 0.5
        
        # Similarity to user's hashtags
        similarity_score = self._calculate_hashtag_similarity(hashtag, user_hashtags)
        score += similarity_score * 0.3
        
        # Growth factor (increasing usage)
        growth_score = await self._calculate_hashtag_growth(hashtag)
        score += growth_score * 0.2
        
        return score
    
    # Helper methods
    async def _get_user_following(self, user_id: str) -> List[str]:
        """Get list of user IDs that the user is following"""
        follows = await self.db.follows.find({"followerId": user_id}).to_list(length=None)
        return [follow["followingId"] for follow in follows]
    
    async def _get_followers_count(self, user_id: str) -> int:
        """Get follower count for user"""
        return await self.db.follows.count_documents({"followingId": user_id})
    
    async def _get_posts_count(self, user_id: str) -> int:
        """Get post count for user"""
        return await self.db.posts.count_documents({"authorId": user_id})
    
    async def _infer_user_interests(self, user_id: str) -> List[str]:
        """Infer user interests from their posts and activity"""
        # Get user's recent posts
        posts = await self.db.posts.find({"authorId": user_id}).limit(50).to_list(length=50)
        
        # Extract hashtags
        all_hashtags = []
        for post in posts:
            all_hashtags.extend(post.get("hashtags", []))
        
        # Get most common hashtags
        hashtag_counts = Counter(all_hashtags)
        return [hashtag for hashtag, count in hashtag_counts.most_common(10)]
    
    def _calculate_profile_completeness(self, user: Dict) -> float:
        """Calculate how complete a user's profile is"""
        score = 0.0
        
        if user.get("profileImage"):
            score += 0.3
        if user.get("bio"):
            score += 0.3
        if user.get("fullName"):
            score += 0.2
        if user.get("username"):
            score += 0.2
        
        return score
    
    async def _get_mutual_connections(self, user_id: str, limit: int) -> List[Dict]:
        """Get users with mutual connections"""
        # This is a simplified version - in a real implementation,
        # you'd use a more sophisticated graph traversal
        following_ids = await self._get_user_following(user_id)
        
        if not following_ids:
            return []
        
        # Get users that the user's friends are following
        mutual_follows = await self.db.follows.find({
            "followerId": {"$in": following_ids}
        }).limit(limit * 2).to_list(length=limit * 2)
        
        # Count mutual connections
        user_counts = Counter([follow["followingId"] for follow in mutual_follows])
        
        # Get user details for top candidates
        top_user_ids = [user_id for user_id, count in user_counts.most_common(limit)]
        users = await self.db.users.find({"id": {"$in": top_user_ids}}).to_list(length=limit)
        
        return users
