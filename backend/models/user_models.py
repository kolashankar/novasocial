from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime


class UserRegister(BaseModel):
    fullName: str
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserProfile(BaseModel):
    profileImage: Optional[str] = None
    bio: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    fullName: str
    profileImage: Optional[str] = None
    bio: Optional[str] = None
    createdAt: datetime


class AuthResponse(BaseModel):
    user: UserResponse
    token: str


class UserStats(BaseModel):
    postsCount: int
    followersCount: int
    followingCount: int