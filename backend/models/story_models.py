from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .user_models import UserResponse


class StoryCreate(BaseModel):
    media: str  # base64 encoded image/video
    mediaType: str  # "image" or "video"
    text: Optional[str] = None
    textPosition: Optional[dict] = None  # {"x": 0.5, "y": 0.3}
    textStyle: Optional[dict] = None  # {"color": "#fff", "fontSize": 24}
    duration: Optional[int] = 24  # hours


class StoryResponse(BaseModel):
    id: str
    authorId: str
    author: UserResponse
    media: str
    mediaType: str
    text: Optional[str]
    textPosition: Optional[dict]
    textStyle: Optional[dict]
    duration: int
    viewers: List[str]  # User IDs who viewed
    viewersCount: int
    createdAt: datetime
    expiresAt: datetime


class StoryHighlightCreate(BaseModel):
    title: str
    storyIds: List[str]
    coverImage: Optional[str] = None  # base64 cover image


class StoryHighlightResponse(BaseModel):
    id: str
    userId: str
    user: UserResponse
    title: str
    storyIds: List[str]
    stories: List[StoryResponse]
    coverImage: Optional[str]
    createdAt: datetime
    updatedAt: datetime


class MemoryResponse(BaseModel):
    id: str
    userId: str
    user: UserResponse
    type: str  # "story", "post"
    contentId: str  # Story or Post ID
    content: dict  # Story or Post object
    title: str
    description: str
    memoryDate: datetime  # The date being remembered (e.g., 1 year ago)
    createdAt: datetime


class StoryViewCreate(BaseModel):
    storyId: str
    viewedAt: Optional[datetime] = None


class StoryViewResponse(BaseModel):
    id: str
    storyId: str
    viewerId: str
    viewer: UserResponse
    viewedAt: datetime
