from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .user_models import UserResponse
from .post_models import PostResponse


class SearchQuery(BaseModel):
    query: str
    type: Optional[str] = "all"  # "users", "posts", "hashtags", "all"
    location: Optional[str] = None
    dateFrom: Optional[datetime] = None
    dateTo: Optional[datetime] = None
    sortBy: Optional[str] = "relevance"  # "relevance", "recent", "popular"


class SearchResponse(BaseModel):
    users: List[UserResponse]
    posts: List[PostResponse]
    hashtags: List[str]
    totalResults: int
    hasMore: bool


class HashtagCreate(BaseModel):
    name: str
    description: Optional[str] = None


class HashtagResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    postsCount: int
    followersCount: int
    isFollowing: bool
    isTrending: bool
    createdAt: datetime
    updatedAt: datetime


class HashtagFollow(BaseModel):
    hashtagId: str


class TrendingHashtagResponse(BaseModel):
    hashtag: str
    count: int
    growth: float  # Percentage growth from previous period
    category: Optional[str] = None


class UserActivityCreate(BaseModel):
    userId: str
    activityType: str  # "like", "comment", "share", "view", "search", "follow"
    targetId: Optional[str] = None  # Post/User/Hashtag ID
    targetType: Optional[str] = None  # "post", "user", "hashtag"
    metadata: Optional[dict] = None  # Additional data


class UserActivityResponse(BaseModel):
    id: str
    userId: str
    activityType: str
    targetId: Optional[str]
    targetType: Optional[str]
    metadata: Optional[dict]
    createdAt: datetime


class RecommendationRequest(BaseModel):
    userId: str
    type: str  # "posts", "users", "hashtags"
    limit: int = 20
    excludeIds: Optional[List[str]] = []  # IDs to exclude from recommendations


class RecommendationResponse(BaseModel):
    id: str
    userId: str
    type: str
    targetId: str
    targetType: str  # "post", "user", "hashtag"
    score: float  # Relevance score (0-1)
    reason: str  # Why this was recommended
    createdAt: datetime


class SearchHistory(BaseModel):
    id: str
    userId: str
    query: str
    type: str
    resultsCount: int
    clickedResultId: Optional[str]
    createdAt: datetime
