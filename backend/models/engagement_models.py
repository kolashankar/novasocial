from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from .user_models import UserResponse


class LikeToggle(BaseModel):
    targetId: str  # Post or Comment ID
    targetType: str  # "post" or "comment"


class FollowRequest(BaseModel):
    targetUserId: str


class FollowResponse(BaseModel):
    id: str
    followerId: str
    followingId: str
    follower: UserResponse
    following: UserResponse
    createdAt: datetime


class NotificationCreate(BaseModel):
    recipientId: str
    type: str  # "like", "comment", "follow", "mention"
    title: str
    message: str
    relatedId: Optional[str] = None  # Post/Comment/User ID
    relatedType: Optional[str] = None  # "post", "comment", "user"


class NotificationResponse(BaseModel):
    id: str
    recipientId: str
    senderId: Optional[str]
    sender: Optional[UserResponse]
    type: str
    title: str
    message: str
    relatedId: Optional[str]
    relatedType: Optional[str]
    isRead: bool
    createdAt: datetime


class AchievementCreate(BaseModel):
    userId: str
    type: str  # "first_post", "100_likes", "10_followers", etc.
    title: str
    description: str
    iconUrl: Optional[str] = None
    points: int = 0


class AchievementResponse(BaseModel):
    id: str
    userId: str
    user: UserResponse
    type: str
    title: str
    description: str
    iconUrl: Optional[str]
    points: int
    unlockedAt: datetime


class UserBadge(BaseModel):
    id: str
    userId: str
    badgeType: str  # "verified", "premium", "creator", etc.
    title: str
    description: str
    iconUrl: Optional[str]
    isActive: bool
    awardedAt: datetime
