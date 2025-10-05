from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .user_models import UserResponse


# Phase 16: Posting & Media Enhancements Models

class PostTag(BaseModel):
    id: Optional[str] = None
    postId: str
    tagType: str  # "user", "location"
    taggedUserId: Optional[str] = None  # For user tags
    locationId: Optional[str] = None  # For location tags
    locationName: Optional[str] = None
    locationCoordinates: Optional[dict] = None  # {"lat": float, "lng": float}
    position: Optional[dict] = None  # {"x": float, "y": float} - position on media
    createdAt: datetime


class LocationTag(BaseModel):
    id: Optional[str] = None
    name: str
    displayName: Optional[str] = None
    coordinates: dict  # {"lat": float, "lng": float}
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    category: Optional[str] = None  # "restaurant", "park", "mall", etc.
    isVerified: bool = False
    totalPosts: int = 0
    createdAt: datetime


class UserTag(BaseModel):
    id: Optional[str] = None
    postId: str
    taggerId: str  # User who tagged
    taggedUserId: str  # User who was tagged
    position: Optional[dict] = None  # Position on media {"x": float, "y": float}
    isApproved: bool = False  # Tagged user needs to approve
    createdAt: datetime


class StoryReel(BaseModel):
    id: Optional[str] = None
    authorId: str
    author: Optional[UserResponse] = None
    contentType: str  # "story", "reel", "story_reel" (hybrid)
    media: str  # base64 encoded
    mediaType: str  # "image", "video"
    duration: Optional[int] = None  # Duration in seconds for videos
    text: Optional[str] = None
    textPosition: Optional[dict] = None
    textStyle: Optional[dict] = None
    music: Optional[dict] = None  # Music metadata
    effects: Optional[List[dict]] = []  # Applied effects/filters
    tags: Optional[List[dict]] = []  # User and location tags
    stickers: Optional[List[dict]] = []  # Applied stickers
    viewers: List[str] = []  # User IDs who viewed
    viewersCount: int = 0
    likesCount: int = 0
    likes: List[str] = []
    commentsCount: int = 0
    isHighlight: bool = False  # If saved to highlights
    expiresAt: Optional[datetime] = None  # For stories
    createdAt: datetime
    updatedAt: datetime


class PostCreate(BaseModel):
    caption: str
    media: List[str]  # Base64 images/videos
    mediaTypes: List[str]  # ["image", "video", ...]
    hashtags: Optional[List[str]] = []
    taggedUsers: Optional[List[dict]] = []  # [{"userId": str, "position": {"x": float, "y": float}}]
    location: Optional[dict] = None  # Location tag data
    

class LocationSearchResult(BaseModel):
    id: str
    name: str
    displayName: str
    address: Optional[str]
    coordinates: dict
    category: Optional[str]
    distance: Optional[float] = None  # Distance from search location


class TagSearchResult(BaseModel):
    users: List[UserResponse]
    locations: List[LocationSearchResult]


# Upload Progress Models
class UploadProgress(BaseModel):
    id: str
    userId: str
    fileName: str
    totalSize: int
    uploadedSize: int
    progress: float  # Percentage 0-100
    status: str  # "uploading", "processing", "completed", "failed"
    retryCount: int = 0
    maxRetries: int = 3
    errorMessage: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime


class MediaCompression(BaseModel):
    id: Optional[str] = None
    originalSize: int
    compressedSize: int
    compressionRatio: float
    quality: int  # 1-100
    format: str
    width: int
    height: int
    duration: Optional[int] = None  # For videos
    processingTime: float  # In seconds
    createdAt: datetime


class StoryReelCreate(BaseModel):
    contentType: str  # "story", "reel", "story_reel"
    media: str  # Base64
    mediaType: str
    duration: Optional[int] = None
    text: Optional[str] = None
    textPosition: Optional[dict] = None
    textStyle: Optional[dict] = None
    music: Optional[dict] = None
    effects: Optional[List[dict]] = []
    tags: Optional[List[dict]] = []
    stickers: Optional[List[dict]] = []
    expiresAt: Optional[datetime] = None


class TagValidation(BaseModel):
    postId: str
    taggedUserIds: List[str]
    locationId: Optional[str] = None
    isValid: bool
    errors: List[str] = []
    warnings: List[str] = []


class PrivacyCheck(BaseModel):
    userId: str
    targetUserId: str
    action: str  # "tag", "mention", "view_post"
    isAllowed: bool
    reason: Optional[str] = None