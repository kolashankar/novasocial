from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .user_models import UserResponse


class PostCreate(BaseModel):
    caption: str
    media: List[str]  # List of base64 images/videos
    mediaTypes: List[str]  # ["image", "video", ...]
    hashtags: Optional[List[str]] = []
    taggedUsers: Optional[List[str]] = []


class PostResponse(BaseModel):
    id: str
    authorId: str
    author: UserResponse
    caption: str
    media: List[str]
    mediaTypes: List[str]
    hashtags: List[str]
    taggedUsers: List[str]
    likes: List[str]  # List of user IDs who liked
    likesCount: int
    comments: List[dict]  # Will be populated separately
    commentsCount: int
    createdAt: datetime


class CommentCreate(BaseModel):
    text: str


class CommentResponse(BaseModel):
    id: str
    postId: str
    userId: str
    user: UserResponse
    text: str
    likes: List[str]
    likesCount: int
    createdAt: datetime